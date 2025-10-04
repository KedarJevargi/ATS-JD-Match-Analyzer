import { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { JobDescriptionInput } from './components/JobDescriptionInput';
import { AnalysisResults } from './components/AnalysisResults';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ErrorMessage } from './components/ErrorMessage';
import { apiService } from './services/api';
import { AnalysisResult } from './types/api';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AnalysisResult | null>(null);

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('Please upload a resume PDF');
      return;
    }

    if (!jobDescription.trim()) {
      setError('Please enter a job description');
      return;
    }

    setError(null);
    setLoading(true);
    setResults(null);

    try {
      const analysisResults = await apiService.analyzeResume(selectedFile, jobDescription);
      setResults(analysisResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during analysis');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setJobDescription('');
    setResults(null);
    setError(null);
  };

  return (
    <div className="app">
      <div className="app-container">
        <header className="app-header">
          <h1 className="app-title">ATS Resume Analyzer</h1>
          <p className="app-subtitle">
            Optimize your resume to pass Applicant Tracking Systems
          </p>
        </header>

        <main className="app-main">
          {!results ? (
            <div className="input-section">
              <FileUpload
                onFileSelect={setSelectedFile}
                selectedFile={selectedFile}
                disabled={loading}
              />

              <JobDescriptionInput
                value={jobDescription}
                onChange={setJobDescription}
                disabled={loading}
              />

              {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

              {loading ? (
                <LoadingSpinner message="Analyzing your resume..." />
              ) : (
                <button
                  className="analyze-button"
                  onClick={handleAnalyze}
                  disabled={!selectedFile || !jobDescription.trim()}
                >
                  Analyze Resume
                </button>
              )}
            </div>
          ) : (
            <div className="results-section">
              <AnalysisResults results={results} />
              <button className="reset-button" onClick={handleReset}>
                Analyze Another Resume
              </button>
            </div>
          )}
        </main>

        <footer className="app-footer">
          <p>Powered by AI-driven ATS analysis</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
