import fitz  # PyMuPDF
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from collections import Counter
import json
import asyncio

# --- Helper function for Keyword Analysis ---
def extract_skills_from_json(data):
    """
    Recursively traverses a nested dictionary/list structure to extract all string values
    into a single flat set.
    """
    skills = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ["job_title", "experience_years"]:
                continue
            skills.update(extract_skills_from_json(value))
    elif isinstance(data, list):
        for item in data:
            skills.update(extract_skills_from_json(item))
    elif isinstance(data, str) and data:
        skills.add(data)
    return skills

# --- Main ATS Checker Function (Modified) ---
async def check_ats_friendly_pdf(pdf_path, jd_json_data=None, visualize=True):
    """
    Comprehensive ATS-friendliness and keyword match checker for PDF resumes.
    """
    try:
        # --- Part 1: Structural Analysis ---
        doc = fitz.open(pdf_path)
        
        line_data, all_fonts, all_font_sizes, text_alignment_data = [], [], [], []
        has_images, has_tables, section_headers = False, False, []
        page_width, full_resume_text = 0, ""

        for page in doc:
            page_width = page.rect.width
            full_resume_text += page.get_text()

            if len(page.get_images()) > 0: has_images = True
            
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = "".join(span["text"] for span in line["spans"]).strip()
                        if len(line_text) < 3: continue
                        
                        x_start = min([span["bbox"][0] for span in line["spans"]])
                        line_data.append((x_start, len(line_text)))
                        
                        for span in line["spans"]:
                            all_fonts.append(span["font"])
                            font_size = span["size"]
                            all_font_sizes.append(font_size)
                            text_alignment_data.append(span["bbox"][0] / page_width)
                            text = span["text"].strip()
                            if len(all_font_sizes) > 1:
                                if font_size > np.mean(all_font_sizes) + 2 and len(text) > 3:
                                    section_headers.append(text)
        doc.close()

        if len(line_data) < 5: return {"error": "Not enough text to analyze"}

        # --- Structural Checks ---
        x_positions = np.array([x for x, _ in line_data])
        hist, _ = np.histogram(x_positions, bins=30)
        is_single_column = True
        if len(hist) > 0 and max(hist) > 0:
            significant_bins = hist > (max(hist) * 0.1)
            is_single_column = np.sum(np.diff(significant_bins.astype(int)) == 1) < 2

        ATS_FRIENDLY_FONTS = {'arial', 'calibri', 'times', 'helvetica', 'georgia', 'garamond', 'cambria', 'verdana', 'tahoma', 'computer modern'}
        font_counter = Counter(all_fonts)
        total_fonts = len(all_fonts)
        ats_friendly_font_count = sum(count for font, count in font_counter.items() if any(ats in font.lower() for ats in ATS_FRIENDLY_FONTS))
        font_compatibility_score = (ats_friendly_font_count / total_fonts) * 100 if total_fonts > 0 else 100
        uses_simple_fonts = font_compatibility_score > 80

        no_images = not has_images
        has_clear_headers = len(section_headers) >= 3
        left_aligned_count = sum(1 for r in text_alignment_data if r < 0.2)
        left_alignment_score = (left_aligned_count / len(text_alignment_data)) * 100 if text_alignment_data else 100
        is_left_aligned = left_alignment_score > 70
        no_tables = not has_tables

        structural_checks = [is_single_column, uses_simple_fonts, no_images, has_clear_headers, is_left_aligned, no_tables]
        
        # --- Part 2: Scoring ---
        structural_score = (sum(structural_checks) / len(structural_checks)) * 100

        keyword_match_score, found_skills, missing_skills, total_required_skills = 0, [], [], 0
        if jd_json_data:
            required_skills = extract_skills_from_json(jd_json_data)
            total_required_skills = len(required_skills)
            resume_text_lower = full_resume_text.lower()
            if required_skills:
                for skill in sorted(list(required_skills)):
                    if skill.lower() in resume_text_lower: found_skills.append(skill)
                    else: missing_skills.append(skill)
                if total_required_skills > 0:
                    keyword_match_score = (len(found_skills) / total_required_skills) * 100

        overall_score = (keyword_match_score * 0.6) + (structural_score * 0.4) if jd_json_data else structural_score
        
        # --- Part 3: Reporting & Visualization ---
        report = { "overall_ats_score": round(overall_score, 2), "structural_score": round(structural_score, 2), "keyword_match_score": round(keyword_match_score, 2), "structural_checks": {"single_column": is_single_column, "simple_fonts": uses_simple_fonts, "no_images": no_images, "clear_headers": has_clear_headers, "left_aligned": is_left_aligned, "no_tables": no_tables}, "keyword_analysis": {"found_skills": found_skills, "missing_skills": missing_skills, "match_percentage": round(keyword_match_score, 2)}}

        # ========== Visualization ==========
        if visualize:
            is_strong_match = report["overall_ats_score"] > 75
            fig = plt.figure(figsize=(15, 10))
            gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
            
            # Plot 1: X-Position Distribution (Column Detection)
            ax1 = fig.add_subplot(gs[0, :])
            ax1.hist(x_positions, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
            ax1.set_xlabel('Line Start X Position (pixels)', fontsize=11)
            ax1.set_ylabel('Frequency', fontsize=11)
            ax1.set_title(f'Line Start Position (Structure) - Detected {"1 Column" if is_single_column else "Multi-Column"}', fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Font Distribution
            ax2 = fig.add_subplot(gs[1, 0])
            font_names = list(font_counter.keys())[:10]
            font_counts = [font_counter[f] for f in font_names]
            colors_fonts = ['green' if any(ats in f.lower() for ats in ATS_FRIENDLY_FONTS) else 'red' for f in font_names]
            ax2.barh(font_names, font_counts, color=colors_fonts, alpha=0.7)
            ax2.set_xlabel('Count', fontsize=11)
            ax2.set_title('Font Usage (Green = ATS-Friendly)', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='x')
            
            # Plot 3: Keyword Match Doughnut Chart
            ax3 = fig.add_subplot(gs[1, 1])
            if jd_json_data:
                match_sizes = [len(found_skills), len(missing_skills)]
                match_labels = [f'Matched ({len(found_skills)})', f'Missing ({len(missing_skills)})']
                match_colors = ['#4CAF50', '#F44336']
                ax3.pie(match_sizes, labels=match_labels, colors=match_colors, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4, edgecolor='w'))
                ax3.set_title('Keyword Match vs. Job Description', fontsize=12, fontweight='bold')
            else:
                ax3.text(0.5, 0.5, 'No Job Description Provided', ha='center', va='center', fontsize=12, color='gray')
                ax3.set_title('Keyword Match', fontsize=12, fontweight='bold')
                ax3.axis('off')
            
            # Plot 4: Final Score & Checklist
            ax4 = fig.add_subplot(gs[2, :])
            ax4.axis('off')
            
            check_labels = [f"✓ Single Column Layout" if is_single_column else f"✗ Multi-Column Layout", f"✓ Simple Fonts ({font_compatibility_score:.1f}%)" if uses_simple_fonts else f"✗ Complex Fonts ({font_compatibility_score:.1f}%)", f"✓ No Images" if no_images else f"✗ Contains Images", f"✓ Clear Section Headers" if has_clear_headers else f"✗ Few Section Headers", f"✓ Left-Aligned Text ({left_alignment_score:.1f}%)" if is_left_aligned else f"✗ Poor Alignment", f"✓ No Tables" if no_tables else f"✗ Contains Tables"]
            check_colors = ['green' if check else 'red' for check in structural_checks]
            
            y_pos = 0.95
            ax4.text(0.05, y_pos, "Structural Checklist:", fontsize=11, fontweight='bold'); y_pos -= 0.15
            for label, color in zip(check_labels, check_colors):
                ax4.text(0.1, y_pos, label, fontsize=10, color=color, transform=ax4.transAxes); y_pos -= 0.12
            
            score_color = 'green' if is_strong_match else 'orange' if report["overall_ats_score"] >= 60 else 'red'
            ax4.text(0.75, 0.6, f"Overall Score\n{report['overall_ats_score']:.1f}%", fontsize=20, color='white', fontweight='bold', ha='center', bbox=dict(boxstyle='circle', facecolor=score_color, pad=0.8))
            ax4.text(0.75, 0.35, f"Structure: {report['structural_score']:.1f}%", fontsize=11, ha='center')
            ax4.text(0.75, 0.25, f"Keywords: {report['keyword_match_score']:.1f}%", fontsize=11, ha='center')
            
            plt.suptitle(f"Resume Analysis Report - {'STRONG MATCH ✓' if is_strong_match else 'NEEDS IMPROVEMENT ✗'}", fontsize=16, fontweight='bold', color='green' if is_strong_match else 'red')
            plt.show()

        # --- Print to Console ---
        # (The console printout logic from the previous answer is omitted here for brevity, but would go here)

        return report

    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# --- Example Usage ---
if __name__ == "__main__":
    # 1. PASTE YOUR JOB DESCRIPTION JSON HERE
    jd_json_string = """
    {
  "job_title": "Backend Developer",
  "experience_years": {
    "min": 2,
    "max": null
  },
  "programming_languages": [
    "Python",
    "Golang"
  ],
  "frontend_frameworks": [],
  "backend_frameworks": [
    "Django",
    "Flask",
    "FastAPI"
  ],
  "databases": {
    "relational": [
      "SQL"
    ],
    "nosql": [],
    "in_memory": [],
    "search_engines": [],
    "graph": [],
    "time_series": []
  },
  "cloud_platforms": {
    "providers": [
      "AWS",
      "Azure",
      "GCP"
    ],
    "aws_services": [],
    "azure_services": [],
    "gcp_services": []
  },
  "devops_and_infrastructure": {
    "containerization": [
      "Docker"
    ],
    "orchestration": [
      "Kubernetes"
    ],
    "ci_cd": [
      "CI/CD Pipelines",
      "GitHub Actions"
    ],
    "iac": [],
    "monitoring": [],
    "version_control": [
      "GitHub"
    ]
  },
  "messaging_and_streaming": [],
  "testing_frameworks": {
    "unit_testing": [],
    "integration_testing": [],
    "e2e_testing": [],
    "performance_testing": []
  },
  "build_and_package_managers": [],
  "apis_and_protocols": [
    "RESTful APIs"
  ],
  "markup_and_styling": [],
  "architectural_patterns": [
    "Microservices Architecture"
  ],
  "methodologies": [],
  "security": [],
  "operating_systems": [],
  "data_processing": [],
  "machine_learning": [],
  "mobile_development": [],
  "soft_skills": [
    "Collaboration Skills",
    "Communication"
  ],
  "certifications": [],
  "other_technical_skills": [
    "Caching Strategies",
    "System Design Principles"
  ]
}
    """
    jd_data = json.loads(jd_json_string)
    
    # 2. SET THE PATH TO YOUR RESUME PDF FILE HERE
    pdf_file_path = "Kedar_Jevargi_Resume.pdf"  # <--- CHANGE THIS FILENAME
    
    try:
        # Run the analysis with visualization enabled
        report = asyncio.run(check_ats_friendly_pdf(pdf_file_path, jd_json_data=jd_data, visualize=True))
        
        if report and "error" not in report:
            if report.get("overall_ats_score", 0) > 75:
                print("\n🎉 Your resume is a strong match for this job description!")
            else:
                print("\n⚠️ Your resume needs improvements to be a better match.")
    except FileNotFoundError:
        print(f"\nERROR: The file '{pdf_file_path}' was not found.")
        print("Please make sure the PDF file is in the same directory as the script, or provide the full path.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")