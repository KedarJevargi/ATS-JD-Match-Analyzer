import spacy
import re
from collections import defaultdict

# You still need spaCy and its model. If you haven't installed it:
# pip install spacy
# python -m spacy download en_core_web_sm
nlp = spacy.load("en_core_web_sm")

async def extract_keywords_simple(job_description: str) -> dict:
    """
    Extracts keywords dynamically from a job description using a simple linguistic approach.

    This function identifies noun phrases, proper nouns, and known entities (like products)
    to build a list of relevant keywords without statistical ranking.

    Args:
        job_description: The full text of the job description.

    Returns:
        A dictionary containing lists of keywords and qualifications.
    """
    # Process the document with spaCy
    doc = nlp(job_description)

    # Use a set to automatically handle duplicates
    keywords = set()

    # 1. Extract Noun Phrases (multi-word keywords like "backend systems")
    for chunk in doc.noun_chunks:
        keywords.add(chunk.text.lower())

    # 2. Extract Proper Nouns (single-word keywords like "Java" or "Kotlin")
    for token in doc:
        if token.pos_ == 'PROPN':
            keywords.add(token.text.lower())
    
    # 3. Extract Named Entities (finds products, companies, etc.)
    for ent in doc.ents:
        if ent.label_ in ['PRODUCT', 'ORG']:
            keywords.add(ent.text.lower())

    # 4. Extract Years of Experience using Regex
    experience_pattern = r'(\d+\+?)\s*years?'
    matches = re.findall(experience_pattern, job_description.lower())
    experience = list(set([f"{m} years" for m in matches])) # Use set to get unique values

    # --- Clean up the results ---
    # Filter out very short or generic keywords
    final_keywords = [
        keyword for keyword in keywords 
        if len(keyword) > 2 and keyword not in ['the job', 'experience', 'team', 'responsibilities']
    ]

    return {
        "keywords": sorted(list(final_keywords)),
        "experience_requirements": sorted(experience)
    }


# --- Example Usage ---
if __name__ == "__main__":
    jd_text = """
    About the job
Experience: 2.00 + years

Salary: INR 1500000.00 / year (based on experience)

Expected Notice Period: 30 Days

Shift: (GMT+05:30) Asia/Kolkata (IST)

Opportunity Type: Remote

Placement Type: Full Time Indefinite Contract(40 hrs a week/160 hrs a month)

(*Note: This is a requirement for one of Uplers' client - Moii Ai)

What do you need for this opportunity?

Must have skills required:

FastAPI, Flask, GCP (or any cloud), Good-to-have: Go, Django, Python, Golang, GCP

Moii Ai is Looking for: 

Backend Developer About the Role We are seeking a highly skilled and motivated Backend Developer to join our engineering team. You will be responsible for building and maintaining the core server-side logic, databases, and APIs that power our applications. The ideal candidate has strong expertise in building scalable, secure, and performant systems, with hands-on experience in both Python and Go, and an understanding of cloud-native development practices. Key Responsibilities

  Design, develop, and maintain robust, scalable, and secure backend services and APIs using Python and Go.
 Work with Python frameworks such as FastAPI, Flask, and/or Django to build high-performance applications.
 Architect and optimize databases, writing complex and efficient SQL queries to manage data integrity and performance.
 Implement and manage CI/CD pipelines using GitHub Actions to automate testing, building, and deployment processes.
 Deploy and manage applications on a cloud platform, with a focus on Google Cloud Platform (GCP) or other major providers (AWS, Azure).
 Collaborate closely with front-end developers, product managers, and other stakeholders to define and deliver new features.
 Design and implement RESTful APIs to facilitate seamless data communication.
 Conduct code reviews and contribute to a culture of continuous improvement and best practices.
 Troubleshoot, debug, and resolve technical issues in development and production environments. Required Qualifications
 Programming Languages: Proven experience with both Python and Go in a professional capacity.
 Web Frameworks: Strong proficiency with at least one Python framework (FastAPI, Flask, or Django).
 Databases: Expertise in SQL and experience with relational database design and management.
 API Development: Hands-on experience with RESTful API design.
 Cloud: Experience with cloud computing platforms, specifically GCP or a similar provider.
 CI/CD: Practical experience building and maintaining CI/CD pipelines with GitHub Actions.
 Soft Skills: Excellent problem-solving, communication, and collaboration skills. Preferred Qualifications
 Experience with microservices architecture.
 Familiarity with containerization technologies like Docker and Kubernetes.
 Knowledge of system design principles, caching strategies, and performance optimization.



    """
    
    extracted_data = extract_keywords_simple(jd_text)
    
    import json
    print(json.dumps(extracted_data, indent=2))