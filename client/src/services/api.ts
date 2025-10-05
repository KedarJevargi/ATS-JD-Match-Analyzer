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

    const data = await this.handleResponse<{ result: AnalysisResult; response: string | object }>(response);
    
    // Backend returns {result: AnalysisResult, response: string | object}
    // We need to extract result and add suggestions from response
    if (!data.result) {
      throw new Error('Invalid response format from server');
    }
    
    // Handle both string and complex object responses
    let suggestions: string | object = data.response || '';
    
    // If response is an object, keep it as-is; if it's a string, use it as-is
    if (typeof data.response === 'object' && data.response !== null) {
      suggestions = data.response;
    }
    
    return {
      ...data.result,
      suggestions
    };
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

// Create and export the service instance
const apiService = new ApiService();

// Export as both named and default export for flexibility
export { apiService };
export default apiService;