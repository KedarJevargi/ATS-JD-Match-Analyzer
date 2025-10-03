import os
import json
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
from utils import jd_keyword_extractor, pdf_text_extractor, atsAanalyzer, sendGemini
from io import BytesIO
import google.generativeai as genai

# --- Router Setup ---
router = APIRouter(
    prefix="/ats",
    tags=["ATS"]
)

@router.post("/analyse", status_code=status.HTTP_201_CREATED)
async def analyse_resume(pdf: UploadFile = File(...), jd: str = Form(...)):
    """
    Analyzes a resume PDF against a job description.
    """
    
    # === STEP 1: Initial Data Processing ===
    try:
        # Extract text from PDF
        pdf_text = pdf_text_extractor.extract_text_from_pdf(pdf)
        if not pdf_text.strip():
            raise HTTPException(status_code=422, detail="No text could be extracted from the PDF")
        
        # Parse JD text
        jd_text = jd.strip()
        if not jd_text:
            raise HTTPException(status_code=422, detail="Job description cannot be empty")
        
        # Extract keywords from JD
        raw_keywords = await jd_keyword_extractor.extract_keywords_simple(jd_text)
        
        # Structure keywords using a helper function
        parsed_jd = sendGemini.parse_with_gemini(sendGemini.system_prompt, raw_keywords)
        
        # Reset file pointer and get bytes for analysis
        await pdf.seek(0)
        pdf_bytes = await pdf.read()
        pdf_stream = BytesIO(pdf_bytes)
        
        # Perform the initial structural and keyword analysis
        analysis_result_json = await atsAanalyzer.analyze_resume(pdf_stream, parsed_jd, False)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during initial processing: {str(e)}")


    # === STEP 2: Use the Original Prompt for Formatted String Output ===
    final_prompt_template = """
    You are a software dev resume analyzer given:
    The text content of a resume.
    A JSON analysis of its structure and keyword coverage.
    The JSON has the following keys and rules:
    "column": true/false → true means single column (good), false means multiple columns (bad).
    "simple fonts": true/false → true means allowed fonts (Arial, Calibri, Times, Helvetica, Georgia, Garamond, Cambria, Verdana, Tahoma, Computer Modern, CMR, LM Roman). false means non-standard fonts used.
    "no images": true/false → true means no images (good), false means images are present (bad).
    "clear section header": true/false → true means section headers are clear, false means missing/unclear.
    "poor text alignment": true/false → true means poor alignment, false means alignment is fine.
    "no tables": true/false → true means no tables (good), false means tables are used (bad).
    "key words matched": [...] → list of relevant keywords already found in resume.
    "keyword missing": [...] → list of important keywords not found in resume.
    Your Task
    Based on the resume text + JSON analysis:
    Structural Improvements
    Identify formatting issues (columns, fonts, images, tables, alignment).
    Suggest specific fixes (e.g., "Remove images from header", "Convert multi-column layout to single column").
    Content Improvements
    Review "key words matched" and "keyword missing".
    Recommend where to add the missing keywords (e.g., "Add Python, Django, and RESTful APIs under 'Technical Skills'", "Mention CI/CD Pipelines and GitHub Actions under 'Projects'").
    Section-by-Section Updates
    For each standard resume section (Summary, Skills, Experience, Projects, Education), specify what to improve.
    If keywords fit multiple sections, state the best placement.
    Final Recommendations
    Summarize all changes clearly in bullet points.
    Ensure advice is tailored for a Software Development / Backend Engineering resume aiming at FAANG companies.
    Output Format (Strictly Follow This)
    Structural Fixes: [list of changes]
    Content Fixes: [list of keyword insertions and rewrites]
    Section Updates:
    Summary: [...]
    Skills: [...]
    Experience: [...]
    Projects: [...]
    Education: [...]
    Final Recommendations: [concise summary]
    """
    
    full_prompt_with_context = final_prompt_template.format(
        resume_text=pdf_text,
        json_analysis=json.dumps(analysis_result_json, indent=2)
    )

    # === STEP 3: Call Gemini and Return the Raw String Response ===
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable is not set.")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')

        gemini_response = await model.generate_content_async(
            full_prompt_with_context,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
            )
        )
        
        # --- Return the raw text directly from the model ---
        return {
            "result": analysis_result_json,
            "response": gemini_response.text 
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred with the Gemini API: {str(e)}")