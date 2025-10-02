import fitz  # PyMuPDF
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from collections import Counter

def check_ats_friendly_pdf(pdf_path, visualize=True):
    """
    Comprehensive ATS-friendliness checker for PDF resumes.
    
    Args:
        pdf_path (str): Path to the PDF file
        visualize (bool): Whether to show visualization
    
    Returns:
        dict: Detailed ATS compatibility report
    """
    
    try:
        doc = fitz.open(pdf_path)
        
        # Initialize data structures
        all_x_positions = []
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
                    block_x = block["bbox"][0]
                    
                    for line in block["lines"]:
                        for span in line["spans"]:
                            # Collect x-positions
                            x_pos = span["bbox"][0]
                            all_x_positions.append(x_pos)
                            
                            # Collect fonts
                            font_name = span["font"]
                            all_fonts.append(font_name)
                            
                            # Collect font sizes
                            font_size = span["size"]
                            all_font_sizes.append(font_size)
                            
                            # Check text alignment (left-aligned if x < 20% of page width)
                            alignment_ratio = x_pos / page_width
                            text_alignment_data.append(alignment_ratio)
                            
                            # Detect section headers (larger font size)
                            text = span["text"].strip()
                            if font_size > np.mean(all_font_sizes) + 2 and len(text) > 3:
                                section_headers.append(text)
            
            # Detect tables (simplified: look for grid-like structures)
            text_dict = page.get_text("dict")
            if "blocks" in text_dict:
                block_positions = [(b["bbox"][0], b["bbox"][1]) for b in text_dict["blocks"] if "lines" in b]
                if len(block_positions) > 10:
                    # Check for regular grid pattern
                    x_coords = [pos[0] for pos in block_positions]
                    y_coords = [pos[1] for pos in block_positions]
                    x_std = np.std(x_coords)
                    y_std = np.std(y_coords)
                    # Low std dev indicates grid structure
                    if x_std < 50 and y_std < 50:
                        has_tables = True
        
        doc.close()
        
        if len(all_x_positions) < 10:
            return {"error": "Not enough text to analyze"}
        
        # ========== CHECK 1: Multi-Column Detection ==========
        X = np.array(all_x_positions).reshape(-1, 1)
        clustering = DBSCAN(eps=50, min_samples=10).fit(X)
        labels = clustering.labels_
        unique_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        x_positions_sorted = sorted(all_x_positions)
        gaps = []
        for i in range(1, len(x_positions_sorted)):
            gap = x_positions_sorted[i] - x_positions_sorted[i-1]
            if gap > 100:
                gaps.append((x_positions_sorted[i-1], x_positions_sorted[i]))
        
        is_single_column = unique_clusters < 2 and len(gaps) < 1
        
        # ========== CHECK 2: Simple Fonts ==========
        ATS_FRIENDLY_FONTS = {
            'arial', 'calibri', 'times', 'helvetica', 'georgia', 
            'garamond', 'cambria', 'verdana', 'tahoma'
        }
        
        font_counter = Counter(all_fonts)
        total_fonts = len(all_fonts)
        ats_friendly_font_count = 0
        
        for font, count in font_counter.items():
            font_lower = font.lower()
            if any(ats_font in font_lower for ats_font in ATS_FRIENDLY_FONTS):
                ats_friendly_font_count += count
        
        font_compatibility_score = (ats_friendly_font_count / total_fonts) * 100
        uses_simple_fonts = font_compatibility_score > 80
        
        # ========== CHECK 3: No Images with Text ==========
        no_images = not has_images
        
        # ========== CHECK 4: Clear Section Headers ==========
        has_clear_headers = len(section_headers) >= 3
        
        # ========== CHECK 5: Left-Aligned Text ==========
        left_aligned_count = sum(1 for ratio in text_alignment_data if ratio < 0.2)
        left_alignment_score = (left_aligned_count / len(text_alignment_data)) * 100
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
                "detected_clusters": unique_clusters,
                "column_gaps": len(gaps),
                "font_compatibility": round(font_compatibility_score, 2),
                "left_alignment_score": round(left_alignment_score, 2),
                "section_headers_found": len(section_headers),
                "images_detected": has_images,
                "tables_detected": has_tables
            }
        }
        
        # ========== Visualization ==========
        if visualize:
            fig = plt.figure(figsize=(14, 10))
            gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
            
            # Plot 1: X-Position Distribution
            ax1 = fig.add_subplot(gs[0, :])
            ax1.hist(all_x_positions, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
            ax1.set_xlabel('X Position (pixels)', fontsize=11)
            ax1.set_ylabel('Frequency', fontsize=11)
            ax1.set_title('Text Position Distribution (Column Detection)', fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            for gap_start, gap_end in gaps:
                ax1.axvspan(gap_start, gap_end, color='red', alpha=0.2)
            
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
            ax3.hist(text_alignment_data, bins=30, color='purple', edgecolor='black', alpha=0.7)
            ax3.axvline(x=0.2, color='red', linestyle='--', linewidth=2, label='Left-aligned threshold')
            ax3.set_xlabel('Alignment Ratio (x/page_width)', fontsize=11)
            ax3.set_ylabel('Frequency', fontsize=11)
            ax3.set_title('Text Alignment Distribution', fontsize=12, fontweight='bold')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Plot 4: ATS Compatibility Checklist
            ax4 = fig.add_subplot(gs[2, :])
            ax4.axis('off')
            
            check_labels = [
                f"✓ Single Column Layout" if is_single_column else f"✗ Multi-Column Layout ({unique_clusters} columns)",
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
            
            # Overall score
            score_color = 'green' if is_ats_friendly else 'orange' if ats_score >= 70 else 'red'
            ax4.text(0.5, 0.05, f"ATS COMPATIBILITY SCORE: {ats_score:.1f}%",
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
        
        if not is_ats_friendly:
            print("\n RECOMMENDATIONS:")
            if not is_single_column:
                print("  • Convert to single-column layout")
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
        return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Replace with your PDF path
    pdf_file_path = "Kedar_Jevargi_Resume.pdf"
    
    result = check_ats_friendly_pdf(pdf_file_path, visualize=True)
    
    if result.get("is_ats_friendly"):
        print("\n Your PDF is ATS-friendly!")
    else:
        print("\n Your PDF needs improvements for ATS compatibility.")
