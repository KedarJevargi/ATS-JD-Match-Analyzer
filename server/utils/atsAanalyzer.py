import fitz  # PyMuPDF
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from collections import Counter
from scipy import stats

def check_ats_friendly_pdf(pdf_path, visualize=True):
    """
    Comprehensive ATS-friendliness checker for PDF resumes.
    Fixed for LaTeX-generated PDFs with artifacts.
    """
    
    try:
        doc = fitz.open(pdf_path)
        
        # Initialize data structures
        line_data = []  # Store (x_position, text_length) pairs
        all_fonts = []
        all_font_sizes = []
        text_alignment_data = []
        has_images = False
        has_tables = False
        section_headers = []
        page_width = 0
        
        # Extract data from all pages
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_width = page.rect.width
            page_height = page.rect.height
            
            # Check for images
            image_list = page.get_images()
            if len(image_list) > 0:
                has_images = True
            
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:  # Text block
                    for line in block["lines"]:
                        # Get line text content
                        line_text = "".join(span["text"] for span in line["spans"]).strip()
                        
                        # Skip empty or very short lines (likely artifacts)
                        if len(line_text) < 3:
                            continue
                        
                        # Get line start position
                        x_positions = [span["bbox"][0] for span in line["spans"]]
                        x_start = min(x_positions)
                        
                        # Store x position with text length (for filtering)
                        line_data.append((x_start, len(line_text)))
                        
                        for span in line["spans"]:
                            # Collect fonts
                            font_name = span["font"]
                            all_fonts.append(font_name)
                            
                            # Collect font sizes
                            font_size = span["size"]
                            all_font_sizes.append(font_size)
                            
                            # Check text alignment
                            alignment_ratio = span["bbox"][0] / page_width
                            text_alignment_data.append(alignment_ratio)
                            
                            # Detect section headers
                            text = span["text"].strip()
                            if len(all_font_sizes) > 0:  # Prevent division by zero
                                mean_size = np.mean(all_font_sizes)
                                if font_size > mean_size + 2 and len(text) > 3:
                                    section_headers.append(text)
            
            # Detect tables (simplified)
            text_dict = page.get_text("dict")
            if "blocks" in text_dict:
                block_positions = [(b["bbox"][0], b["bbox"][1]) for b in text_dict["blocks"] if "lines" in b]
                if len(block_positions) > 10:
                    x_coords = [pos[0] for pos in block_positions]
                    y_coords = [pos[1] for pos in block_positions]
                    if np.std(x_coords) < 50 and np.std(y_coords) < 50:
                        has_tables = True
        
        doc.close()
        
        if len(line_data) < 5:
            return {"error": "Not enough text to analyze"}
        
        # ========== ENHANCED CHECK 1: Multi-Column Detection ==========
        
        # Extract x positions and text lengths
        x_positions = np.array([x for x, _ in line_data])
        text_lengths = np.array([length for _, length in line_data])
        
        # Method 1: Remove outliers using IQR
        Q1 = np.percentile(x_positions, 25)
        Q3 = np.percentile(x_positions, 75)
        IQR = Q3 - Q1
        
        # Define outlier bounds (more lenient for right side)
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 3 * IQR  # More lenient for right outliers
        
        # Filter positions
        mask = (x_positions >= lower_bound) & (x_positions <= upper_bound)
        filtered_x_positions = x_positions[mask]
        
        # Method 2: Histogram-based column detection
        hist, bin_edges = np.histogram(filtered_x_positions, bins=30)
        
        # Find significant peaks (peaks with at least 10% of max frequency)
        threshold = max(hist) * 0.1
        significant_bins = hist > threshold
        
        # Group consecutive significant bins as columns
        column_groups = []
        in_group = False
        current_group = []
        
        for i, is_significant in enumerate(significant_bins):
            if is_significant:
                if not in_group:
                    in_group = True
                    current_group = [i]
                else:
                    current_group.append(i)
            else:
                if in_group:
                    column_groups.append(current_group)
                    current_group = []
                    in_group = False
        
        if in_group:
            column_groups.append(current_group)
        
        # Count columns based on histogram peaks
        histogram_columns = len(column_groups)
        
        # Method 3: DBSCAN with filtered data (fallback)
        if len(filtered_x_positions) > 5:
            X_filtered = filtered_x_positions.reshape(-1, 1)
            
            # Dynamic eps based on page width
            eps = page_width * 0.15  # 15% of page width
            
            clustering = DBSCAN(eps=eps, min_samples=10).fit(X_filtered)
            labels = clustering.labels_
            unique_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        else:
            unique_clusters = 1
        
        # Method 4: Statistical approach - check for multimodal distribution
        # If standard deviation is high relative to mean, might indicate columns
        if len(filtered_x_positions) > 0:
            x_std = np.std(filtered_x_positions)
            x_mean = np.mean(filtered_x_positions)
            cv = x_std / x_mean if x_mean > 0 else 0  # Coefficient of variation
            
            # Low CV suggests single column
            statistical_single_column = cv < 0.3
        else:
            statistical_single_column = True
        
        # Combine methods with weighted decision
        # Prioritize histogram method for LaTeX PDFs
        if histogram_columns <= 1:
            is_single_column = True
        elif histogram_columns >= 3:
            # Likely artifacts if more than 2 columns detected
            is_single_column = statistical_single_column
        else:
            # 2 potential columns - verify with clustering
            is_single_column = unique_clusters <= 1 or statistical_single_column
        
        # For debugging/reporting
        detected_columns = min(histogram_columns, unique_clusters) if is_single_column else max(histogram_columns, unique_clusters)
        
        # ========== CHECK 2: Simple Fonts ==========
        ATS_FRIENDLY_FONTS = {
            'arial', 'calibri', 'times', 'helvetica', 'georgia', 
            'garamond', 'cambria', 'verdana', 'tahoma', 'computer modern',  # Added LaTeX font
            'latin modern', 'tex gyre'  # Common LaTeX fonts
        }
        
        font_counter = Counter(all_fonts)
        total_fonts = len(all_fonts)
        ats_friendly_font_count = 0
        
        for font, count in font_counter.items():
            font_lower = font.lower()
            if any(ats_font in font_lower for ats_font in ATS_FRIENDLY_FONTS):
                ats_friendly_font_count += count
        
        font_compatibility_score = (ats_friendly_font_count / total_fonts) * 100 if total_fonts > 0 else 0
        uses_simple_fonts = font_compatibility_score > 80
        
        # ========== CHECK 3: No Images with Text ==========
        no_images = not has_images
        
        # ========== CHECK 4: Clear Section Headers ==========
        has_clear_headers = len(section_headers) >= 3
        
        # ========== CHECK 5: Left-Aligned Text ==========
        left_aligned_count = sum(1 for ratio in text_alignment_data if ratio < 0.2)
        left_alignment_score = (left_aligned_count / len(text_alignment_data)) * 100 if text_alignment_data else 0
        is_left_aligned = left_alignment_score > 70
        
        # ========== CHECK 6: No Tables ==========
        no_tables = not has_tables
        
        # ========== Overall ATS Score ==========
        checks = [
            is_single_column,
            uses_simple_fonts,
            no_images,
            has_clear_headers,
            is_left_aligned,
            no_tables
        ]
        
        ats_score = (sum(checks) / len(checks)) * 100
        is_ats_friendly = ats_score >= 80
        
        # Prepare report
        report = {
            "is_ats_friendly": is_ats_friendly,
            "ats_score": round(ats_score, 2),
            "checks": {
                "single_column": is_single_column,
                "simple_fonts": uses_simple_fonts,
                "no_images": no_images,
                "clear_headers": has_clear_headers,
                "left_aligned": is_left_aligned,
                "no_tables": no_tables
            },
            "details": {
                "detected_columns": detected_columns,
                "histogram_columns": histogram_columns,
                "dbscan_clusters": unique_clusters,
                "font_compatibility": round(font_compatibility_score, 2),
                "left_alignment_score": round(left_alignment_score, 2),
                "section_headers_found": len(section_headers),
                "images_detected": has_images,
                "tables_detected": has_tables,
                "outliers_removed": len(x_positions) - len(filtered_x_positions)
            }
        }
        
        # ========== Visualization ==========
        if visualize:
            fig = plt.figure(figsize=(14, 10))
            gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
            
            # Plot 1: X-Position Distribution with outlier detection
            ax1 = fig.add_subplot(gs[0, :])
            
            # Show all data with outliers marked
            ax1.hist(x_positions, bins=50, color='lightgray', edgecolor='black', 
                    alpha=0.5, label='All positions')
            ax1.hist(filtered_x_positions, bins=30, color='steelblue', 
                    edgecolor='black', alpha=0.7, label='Filtered (outliers removed)')
            
            # Mark outlier bounds
            if len(filtered_x_positions) > 0:
                ax1.axvline(x=lower_bound, color='red', linestyle='--', 
                           linewidth=1, label=f'Outlier bounds')
                ax1.axvline(x=upper_bound, color='red', linestyle='--', linewidth=1)
            
            ax1.set_xlabel('Line Start X Position (pixels)', fontsize=11)
            ax1.set_ylabel('Frequency', fontsize=11)
            ax1.set_title(f'Line Start Position Distribution (Detected: {detected_columns} column(s))', 
                         fontsize=12, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Font Distribution
            ax2 = fig.add_subplot(gs[1, 0])
            font_names = list(font_counter.keys())[:10]  # Top 10 fonts
            font_counts = [font_counter[f] for f in font_names]
            colors_fonts = ['green' if any(ats in f.lower() for ats in ATS_FRIENDLY_FONTS) else 'red' 
                           for f in font_names]
            ax2.barh(font_names, font_counts, color=colors_fonts, alpha=0.7)
            ax2.set_xlabel('Count', fontsize=11)
            ax2.set_title('Font Usage (Green = ATS-Friendly)', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='x')
            
            # Plot 3: Text Alignment
            ax3 = fig.add_subplot(gs[1, 1])
            if text_alignment_data:
                ax3.hist(text_alignment_data, bins=30, color='purple', 
                        edgecolor='black', alpha=0.7)
                ax3.axvline(x=0.2, color='red', linestyle='--', linewidth=2, 
                           label='Left-aligned threshold')
                ax3.set_xlabel('Alignment Ratio (x/page_width)', fontsize=11)
                ax3.set_ylabel('Frequency', fontsize=11)
                ax3.set_title('Text Alignment Distribution', fontsize=12, fontweight='bold')
                ax3.legend()
                ax3.grid(True, alpha=0.3)
            
            # Plot 4: ATS Compatibility Checklist
            ax4 = fig.add_subplot(gs[2, :])
            ax4.axis('off')
            
            check_labels = [
                f"✓ Single Column Layout" if is_single_column else f"✗ Multi-Column Layout ({detected_columns} columns detected)",
                f"✓ Simple Fonts ({font_compatibility_score:.1f}%)" if uses_simple_fonts else f"✗ Complex Fonts ({font_compatibility_score:.1f}%)",
                f"✓ No Images" if no_images else f"✗ Contains Images",
                f"✓ Clear Section Headers ({len(section_headers)})" if has_clear_headers else f"✗ Few Section Headers ({len(section_headers)})",
                f"✓ Left-Aligned Text ({left_alignment_score:.1f}%)" if is_left_aligned else f"✗ Poor Alignment ({left_alignment_score:.1f}%)",
                f"✓ No Tables" if no_tables else f"✗ Contains Tables",
            ]
            
            check_colors = ['green' if check else 'red' for check in checks]
            
            y_pos = 0.9
            for label, color in zip(check_labels, check_colors):
                ax4.text(0.1, y_pos, label, fontsize=11, color=color, fontweight='bold',
                        transform=ax4.transAxes)
                y_pos -= 0.12
            
            # Add debug info for LaTeX PDFs
            if report["details"]["outliers_removed"] > 0:
                ax4.text(0.1, 0.05, 
                        f"Note: {report['details']['outliers_removed']} outlier positions filtered (LaTeX artifacts)",
                        fontsize=9, color='gray', style='italic', transform=ax4.transAxes)
            
            # Overall score
            score_color = 'green' if is_ats_friendly else 'orange' if ats_score >= 70 else 'red'
            ax4.text(0.5, 0.15, f"ATS COMPATIBILITY SCORE: {ats_score:.1f}%",
                    fontsize=14, color=score_color, fontweight='bold',
                    transform=ax4.transAxes, ha='center',
                    bbox=dict(boxstyle='round', facecolor=score_color, alpha=0.2))
            
            plt.suptitle(f"ATS-Friendly PDF Analysis - {'PASS ✓' if is_ats_friendly else 'FAIL ✗'}", 
                        fontsize=16, fontweight='bold', 
                        color='green' if is_ats_friendly else 'red')
            
            plt.show()
        
        # Print report
        print("\n" + "="*60)
        print("ATS-FRIENDLY PDF ANALYSIS REPORT")
        print("="*60)
        print(f"\nOverall ATS Score: {ats_score:.2f}%")
        print(f"ATS-Friendly: {'YES ✓' if is_ats_friendly else 'NO ✗'}")
        print("\n" + "-"*60)
        print("DETAILED CHECKS:")
        print("-"*60)
        for key, value in report["checks"].items():
            status = "✓ PASS" if value else "✗ FAIL"
            print(f"{key.replace('_', ' ').title():.<40} {status}")
        print("-"*60)
        print("\nDEBUG INFO:")
        print(f"  Histogram detected columns: {histogram_columns}")
        print(f"  DBSCAN detected clusters: {unique_clusters}")
        print(f"  Outliers filtered: {report['details']['outliers_removed']}")
        print("-"*60)
        
        if not is_ats_friendly:
            print("\n📋 RECOMMENDATIONS:")
            if not is_single_column:
                print("  • Convert to single-column layout")
                print("    (Note: Some LaTeX templates may show false positives)")
            if not uses_simple_fonts:
                print("  • Use standard fonts (Arial, Calibri, Times New Roman)")
            if not no_images:
                print("  • Remove images or replace with text")
            if not has_clear_headers:
                print("  • Add clear section headers (Experience, Education, Skills)")
            if not is_left_aligned:
                print("  • Align text to the left")
            if not no_tables:
                print("  • Replace tables with simple text formatting")
        
        print("="*60 + "\n")
        
        return report
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Replace with your PDF path
    pdf_file_path = "non.pdf"
    
    result = check_ats_friendly_pdf(pdf_file_path, visualize=True)
    
    if result.get("is_ats_friendly"):
        print("\n🎉 Your PDF is ATS-friendly!")
    else:
        print("\n⚠️ Your PDF needs improvements for ATS compatibility.")