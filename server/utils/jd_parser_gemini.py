import google.generativeai as genai
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

def parse_with_gemini(raw_keywords: Dict[str, Any], temperature: float = 0.1) -> Dict[str, Any]: # <-- CHANGED: No longer takes system_prompt
    """
    Parses raw keywords from a job description using the Gemini API.
    It loads the system prompt from the .env file.

    Args:
        raw_keywords: A dictionary containing the messy keywords extracted from the JD.
        temperature: The creativity level for the model's response (lower is more deterministic).

    Returns:
        A structured dictionary with the parsed job description data.
    """
    
    # Get credentials and prompt from environment variables
    api_key = os.getenv('GEMINI_API_KEY')
    system_prompt = os.getenv('SYSTEM_PROMPT') # <-- CHANGED: Load prompt from .env

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")
    if not system_prompt:
        raise ValueError("SYSTEM_PROMPT not found. Please set it in your .env file.")
    
    # Configure the Gemini client
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
    
    # Convert the raw_keywords dictionary to a JSON string to include in the prompt
    keywords_json_string = json.dumps(raw_keywords, indent=2)
    
    # Combine the instructions (system_prompt) with the actual data to be processed.
    full_prompt = f"""{system_prompt}

# INPUT DATA TO PARSE
Now, process the following raw JSON data based on the rules you were given:

{keywords_json_string}
"""
    
    # Generate the response from the model
    response = model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=4096,
        )
    )
    
    # Extract and clean the response text
    response_text = response.text.strip()
    
    # Remove markdown code block formatting (e.g., ```json ... ```) if present
    if response_text.startswith('```'):
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            response_text = response_text[start_idx:end_idx + 1]
    
    # Parse the cleaned text into a Python dictionary and return it
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from model response: {e}")
        print(f"Raw response from model:\n{response_text}")
        return {"error": "Failed to parse model response as JSON."}


# This block runs when the script is executed directly
if __name__ == "__main__":
    
    # The detailed instructions are now in the .env file, so we don't define them here.

    # This is the messy data extracted from a Job Description
    raw_keywords = {
        "keywords": [
            "(gmt+05:30) asia/kolkata", "2.00 + years\n\nsalary", "30 days\n\nshift", "a cloud platform", 
            "a culture", "a focus", "a highly skilled and motivated backend developer", "a professional capacity", 
            "a requirement", "actions", "an understanding", "api", "api development", "apis", "applications", 
            "architect", "asia", "at least one python framework", "aws", "azure", "backend", "backend developer", 
            "best practices", "both python", "building", "caching strategies", "ci/cd pipelines", 
            "ci/cd: practical experience building", "cloud", "cloud computing platforms", 
            "cloud-native development practices", "code reviews", "collaboration skills", "communication", 
            "complex and efficient sql", "containerization technologies", "continuous improvement", "data integrity", 
            "databases", "debug", "deployment processes", "design", "developer", "development", "django", "docker", 
            "expertise", "familiarity", "fastapi", "flask", "frameworks", "front-end developers", 
            "full time indefinite contract(40", "gcp", "gcp\n\nmoii ai", "github", "github actions", "gmt+05:30", 
            "golang", "good", "google", "google cloud platform", "hands-on experience", "high-performance applications", 
            "indefinite", "inr", "ist", "key responsibilities\n\n  design", "knowledge", "kolkata", "kubernetes", 
            "languages", "management", "microservices architecture", "moii", "new features", "notice", "notice period", 
            "opportunity", "opportunity type", "other major providers", "other stakeholders", "our applications", 
            "our engineering team", "performance", "performance optimization", "period", "placement", "platform", 
            "preferred", "preferred qualifications\n experience", "product managers", "production environments", 
            "programming", "proven experience", "python", "python frameworks", "qualifications", 
            "relational database design", "remote", "remote\n\nplacement type", "required", 
            "required qualifications\n programming languages", "restful api design", "restful apis", 
            "robust, scalable, and secure backend services", "role", "salary", "scalable, secure, and performant systems", 
            "seamless data communication", "skills", "soft", "soft skills", "sql", "strong expertise", 
            "strong proficiency", "system design principles", "technical issues", "testing", "that", 
            "the core server-side logic", "the ideal candidate", "the job\nexperience", "the role", "this", 
            "this opportunity", "time", "troubleshoot", "type", "uplers", "uplers' client - moii ai", 
            "web frameworks", "week/160", "what", "work", "you"
        ],
        "experience_requirements": []
    }
    
    # Call the function and print the structured result
    print("Parsing job description keywords...")
    structured_jd = parse_with_gemini(raw_keywords) # <-- CHANGED: No longer pass system_prompt
    print("\n--- Structured Job Description ---")
    print(json.dumps(structured_jd, indent=2))
    print("--------------------------------\n")