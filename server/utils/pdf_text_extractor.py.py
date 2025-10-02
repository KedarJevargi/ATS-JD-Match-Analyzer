import pdfplumber

def extract_text_from_pdf(path: str) -> str:
    """
    Extracts text from ALL pages of a PDF file.
    Returns an empty string if the file is not found or an error occurs.
    """
    full_text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n" # Add a newline to separate pages
        return full_text
    except Exception as e:
        return f"Error processing file {path}: {e}"
        