// API Response Types

export interface AnalysisScore {
  'overall score': number;
  'structure score': number;
  'keyword score': number;
}

// Complex response structure for suggestions
export interface SectionUpdates {
  Summary?: string[] | string;
  Skills?: string[] | string;
  Experience?: string[] | string;
  Projects?: string[] | string;
  Education?: string[] | string;
  // Allow any additional section names with flexible types
  [key: string]: string[] | string | undefined;
}

export interface ComplexSuggestions {
  structural_fixes?: string[];
  content_fixes?: string[];
  section_updates?: SectionUpdates;
  final_recommendations?: string[];
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
  suggestions?: string | ComplexSuggestions;
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
