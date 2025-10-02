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

# --- Main ATS Checker Function ---
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
            # FIX: Convert numpy.bool_ to standard Python bool
            is_single_column = bool(np.sum(np.diff(significant_bins.astype(int)) == 1) < 2)

        ATS_FRIENDLY_FONTS = {'arial', 'calibri', 'times', 'helvetica', 'georgia', 'garamond', 'cambria', 'verdana', 'tahoma', 'computer modern'}
        font_counter = Counter(all_fonts)
        font_compatibility_score = 100
        if all_fonts:
            ats_friendly_font_count = sum(count for font, count in font_counter.items() if any(ats in font.lower() for ats in ATS_FRIENDLY_FONTS))
            font_compatibility_score = (ats_friendly_font_count / len(all_fonts)) * 100
        uses_simple_fonts = font_compatibility_score > 80

        no_images = not has_images
        has_clear_headers = len(section_headers) >= 3
        is_left_aligned = False
        left_alignment_score = 0
        if text_alignment_data:
            left_aligned_count = sum(1 for r in text_alignment_data if r < 0.2)
            left_alignment_score = (left_aligned_count / len(text_alignment_data)) * 100
        is_left_aligned = left_alignment_score > 70
        no_tables = not has_tables

        # --- Part 2: Scoring ---
        structural_checks = [is_single_column, uses_simple_fonts, no_images, has_clear_headers, is_left_aligned, no_tables]
        structural_score = (sum(structural_checks) / len(structural_checks)) * 100

        keyword_match_score, found_skills, missing_skills = 0, [], []
        if jd_json_data:
            required_skills = extract_skills_from_json(jd_json_data)
            if required_skills:
                resume_text_lower = full_resume_text.lower()
                for skill in sorted(list(required_skills)):
                    if skill.lower() in resume_text_lower: found_skills.append(skill)
                    else: missing_skills.append(skill)
                if required_skills:
                    keyword_match_score = (len(found_skills) / len(required_skills)) * 100

        overall_score = (keyword_match_score * 0.6) + (structural_score * 0.4) if jd_json_data else structural_score
        
        # --- Part 3: Visualization & Reporting ---
        # (The visualization and printout code remains the same as before)
        
        # --- Final JSON Output ---
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
        print(f"Error processing PDF: {e}")
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
    
    pdf_file_path = "Kedar_Jevargi_Resume.pdf"  # <--- CHANGE THIS FILENAME
    
    try:
        report = asyncio.run(check_ats_friendly_pdf(pdf_file_path, jd_json_data=jd_data, visualize=False))
        
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