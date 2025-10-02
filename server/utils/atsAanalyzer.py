import fitz  # PyMuPDF
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import json
import asyncio

def extract_skills_from_json(data):
    """
    Recursively traverses a nested dictionary/list structure to extract all string values
    into a single flat set for keyword matching.
    """
    skills = set()
    if isinstance(data, dict):
        for key, value in data.items():
            # We don't want to match the job title or experience years as skills
            if key in ["job_title", "experience_years"]:
                continue
            skills.update(extract_skills_from_json(value))
    elif isinstance(data, list):
        for item in data:
            skills.update(extract_skills_from_json(item))
    elif isinstance(data, str) and data:
        skills.add(data)
    return skills

async def analyze_resume(pdf_path, jd_json_data=None, visualize=True):
    """
    Comprehensive ATS-friendliness and keyword match checker for PDF resumes.
    Features robust column detection, dual scoring, and detailed visualization.

    Args:
        pdf_path (str): The file path to the PDF resume.
        jd_json_data (dict, optional): A dictionary parsed from the Job Description JSON.
        visualize (bool, optional): Whether to generate and display matplotlib graphs.

    Returns:
        dict: A JSON-serializable dictionary with the detailed analysis report.
    """
    try:
        # --- Part 1: PDF Parsing and Structural Analysis ---
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

        # --- Structural Checks with Robust Logic ---
        x_positions = np.array([x for x, _ in line_data])
        
        # **NEW ROBUST COLUMN DETECTION**
        hist, bin_edges = np.histogram(x_positions, bins=40, range=(0, page_width))
        column_groups = 0
        if len(hist) > 0 and max(hist) > 0:
            threshold = max(hist) * 0.1
            significant_bins = hist > threshold
            in_group = False
            for is_significant in significant_bins:
                if is_significant and not in_group:
                    column_groups += 1
                    in_group = True
                elif not is_significant:
                    in_group = False
        is_single_column = bool(column_groups <= 1)

        ATS_FRIENDLY_FONTS = {'arial', 'calibri', 'times', 'helvetica', 'georgia', 'garamond', 'cambria', 'verdana', 'tahoma'}
        font_counter = Counter(all_fonts)
        font_compatibility_score = 100.0
        if all_fonts:
            ats_friendly_font_count = sum(count for font, count in font_counter.items() if any(ats in font.lower() for ats in ATS_FRIENDLY_FONTS))
            font_compatibility_score = (ats_friendly_font_count / len(all_fonts)) * 100
        uses_simple_fonts = bool(font_compatibility_score > 80)

        no_images = bool(not has_images)
        has_clear_headers = bool(len(section_headers) >= 3)
        
        left_alignment_score = 0.0
        if text_alignment_data:
            left_aligned_count = sum(1 for r in text_alignment_data if r < 0.2)
            left_alignment_score = (left_aligned_count / len(text_alignment_data)) * 100
        is_left_aligned = bool(left_alignment_score > 70)
        
        no_tables = bool(not has_tables) # Simplified check

        # --- Part 2: Scoring ---
        structural_checks = [is_single_column, uses_simple_fonts, no_images, has_clear_headers, is_left_aligned, no_tables]
        structural_score = (sum(structural_checks) / len(structural_checks)) * 100

        keyword_match_score, found_skills, missing_skills = 0.0, [], []
        if jd_json_data:
            required_skills = extract_skills_from_json(jd_json_data)
            if required_skills:
                resume_text_lower = full_resume_text.lower()
                for skill in sorted(list(required_skills)):
                    # Use word boundaries for more accurate matching
                    if f" {skill.lower()} " in f" {resume_text_lower} ":
                        found_skills.append(skill)
                    else:
                        missing_skills.append(skill)
                keyword_match_score = (len(found_skills) / len(required_skills)) * 100 if required_skills else 0.0

        # Weighted overall score: 60% for keyword match, 40% for structure
        overall_score = (keyword_match_score * 0.6) + (structural_score * 0.4) if jd_json_data else structural_score
        
        # --- Part 3: Visualization ---
        if visualize:
            fig = plt.figure(figsize=(15, 12))
            gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
            fig.suptitle('ATS Resume Analysis Report', fontsize=20, fontweight='bold')

            # Plot 1: Column Layout Analysis
            ax1 = fig.add_subplot(gs[0, :])
            ax1.hist(x_positions, bins=40, color='skyblue', edgecolor='black', alpha=0.7)
            ax1.axhline(y=max(hist) * 0.1 if len(hist) > 0 and max(hist) > 0 else 0, color='r', linestyle='--', label='Significance Threshold')
            ax1.set_title(f'Layout Analysis: Detected {column_groups} Column(s)', fontweight='bold')
            ax1.set_xlabel('Text Start Position (pixels)')
            ax1.set_ylabel('Frequency')
            ax1.legend()
            ax1.grid(alpha=0.3)

            # Plot 2: Keyword Match Analysis
            ax2 = fig.add_subplot(gs[1, 0])
            if jd_json_data:
                labels = 'Keywords Matched', 'Keywords Missing'
                sizes = [len(found_skills), len(missing_skills)]
                colors = ['#4CAF50', '#F44336']
                ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, wedgeprops={"edgecolor":"black"})
                ax2.set_title('Keyword Match vs. Job Description', fontweight='bold')
                ax2.axis('equal')
            else:
                ax2.text(0.5, 0.5, 'No Job Description Provided\n for Keyword Analysis', ha='center', va='center')
                ax2.axis('off')

            # Plot 3: Structural ATS Score Breakdown
            ax3 = fig.add_subplot(gs[1, 1])
            check_names = ['Single Column', 'Simple Fonts', 'No Images', 'Clear Headers', 'Left Aligned', 'No Tables']
            check_values = [c * 100 for c in structural_checks]
            colors = ['#4CAF50' if v > 50 else '#F44336' for v in check_values]
            bars = ax3.barh(check_names, check_values, color=colors, edgecolor='black')
            ax3.set_title('Structural ATS Compliance', fontweight='bold')
            ax3.set_xlabel('Compliance Score (%)')
            ax3.set_xlim(0, 100)
            # Add text labels on bars
            for bar in bars:
                width = bar.get_width()
                label = '✓' if width > 50 else '✗'
                ax3.text(width - 10, bar.get_y() + bar.get_height()/2, label, ha='center', va='center', color='white', fontweight='bold')


            # Plot 4: Final Scores
            ax4 = fig.add_subplot(gs[2, :])
            ax4.axis('off')
            scores = {
                'Structural Score': structural_score,
                'Keyword Score': keyword_match_score,
                'Overall Match Score': overall_score
            }
            y_pos = 0.8
            for name, score in scores.items():
                color = 'green' if score >= 75 else 'orange' if score >= 50 else 'red'
                ax4.text(0.5, y_pos, f'{name}: {score:.1f}%', ha='center', fontsize=16, fontweight='bold', color=color,
                         bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=color, lw=2))
                y_pos -= 0.3
            
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            plt.show()

        # --- Part 4: Final JSON Output ---
        final_json_output = {
            "column": is_single_column,
            "simple fonts": uses_simple_fonts,
            "no images": no_images,
            "clear section header": has_clear_headers,
            "poor text alignment": not is_left_aligned,
            "no tables": no_tables,
            "key words matched": found_skills,
            "keyword missing": missing_skills,
            "score": {
                "overall score": round(overall_score, 2),
                "structure score": round(structural_score, 2),
                "keyword score": round(keyword_match_score, 2)
            }
        }

        return final_json_output

    except Exception as e:
        # Using boolean() and round() on all values ensures they are JSON serializable
        # Also added traceback for better debugging.
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# --- Example Usage ---
if __name__ == "__main__":
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
    "Collaboration",
    "Communication"
  ],
  "certifications": [],
  "other_technical_skills": [
    "Caching Strategies"
  ]
}
    """
    jd_data = json.loads(jd_json_string)
    
    # Use the PDF you uploaded
    pdf_file_path = "Kedar_Jevargi_Resume.pdf"
    
    try:
        # Run the analysis with visualization
        report = asyncio.run(analyze_resume(pdf_file_path, jd_json_data=jd_data, visualize=True))
        
        if report and "error" not in report:
            print("\n--- JSON OUTPUT ---")
            print(json.dumps(report, indent=2))
            print("-------------------\n")

            overall_score = report.get("score", {}).get("overall score", 0)
            if overall_score > 75:
                print("🎉 Your resume is a strong match for this job description!")
            else:
                print("⚠️ Your resume needs improvements to be a better match.")

    except FileNotFoundError:
        print(f"\nERROR: The file '{pdf_file_path}' was not found.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")