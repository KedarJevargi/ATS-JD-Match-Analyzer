import { AnalysisResult, ParsedJD, ExtractTextResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  /**
   * Analyze resume against job description
   */
  async analyzeResume(pdfFile: File, jobDescription: string): Promise<AnalysisResult> {
    const formData = new FormData();
    formData.append('pdf', pdfFile);
    formData.append('jd', jobDescription);

    const response = await fetch(`${API_BASE_URL}/ats/analyse`, {
      method: 'POST',
      body: formData,
    });

    return this.handleResponse<AnalysisResult>(response);
  }

  /**
   * Parse job description text
   */
  async parseJobDescription(jobDescription: string): Promise<ParsedJD> {
    const response = await fetch(`${API_BASE_URL}/jds/parse_text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ jd: jobDescription }),
    });

    return this.handleResponse<ParsedJD>(response);
  }

  /**
   * Extract text from PDF
   */
  async extractTextFromPdf(pdfFile: File): Promise<ExtractTextResponse> {
    const formData = new FormData();
    formData.append('pdf', pdfFile);

    const response = await fetch(`${API_BASE_URL}/pdfs/extracttext`, {
      method: 'POST',
      body: formData,
    });

    return this.handleResponse<ExtractTextResponse>(response);
  }
}

export const apiService = new ApiService();
