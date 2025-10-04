// API Response Types

export interface AnalysisScore {
  'overall score': number;
  'structure score': number;
  'keyword score': number;
}

export interface AnalysisResult {
  column: boolean;
  'simple fonts': boolean;
  'no images': boolean;
  'clear section header': boolean;
  'poor text alignment': boolean;
  'no tables': boolean;
  'key words matched': string[];
  'keyword missing': string[];
  score: AnalysisScore;
  suggestions?: string;
}

export interface ParsedJD {
  [key: string]: string[] | string;
}

export interface ExtractTextResponse {
  extracted_text: string;
}

export interface ApiError {
  detail: string;
}
