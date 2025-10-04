import { AnalysisResult, ComplexSuggestions, SectionUpdates } from '../types/api';
import './AnalysisResults.css';

interface AnalysisResultsProps {
  results: AnalysisResult;
}

export const AnalysisResults = ({ results }: AnalysisResultsProps) => {
  const getScoreColor = (score: number): string => {
    if (score >= 75) return 'score-high';
    if (score >= 50) return 'score-medium';
    return 'score-low';
  };

  const isComplexSuggestions = (
    suggestions: string | ComplexSuggestions | undefined
  ): suggestions is ComplexSuggestions => {
    return typeof suggestions === 'object' && suggestions !== null;
  };

  const renderStringList = (items: string[] | undefined, title: string) => {
    if (!items || items.length === 0) return null;
    
    return (
      <div className="suggestion-subsection">
        <h4 className="subsection-title">{title}</h4>
        <ul className="suggestion-list">
          {items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>
    );
  };

  const renderSectionUpdates = (sectionUpdates: SectionUpdates | undefined) => {
    if (!sectionUpdates) return null;

    const sections = Object.entries(sectionUpdates).filter(([_, value]) => value);
    
    if (sections.length === 0) return null;

    return (
      <div className="suggestion-subsection">
        <h4 className="subsection-title">Section Updates</h4>
        {sections.map(([sectionName, items]) => {
          // Handle both string and array formats
          const itemsArray = Array.isArray(items) ? items : [items];
          
          return (
            <div key={sectionName} className="section-update">
              <h5 className="section-name">{sectionName}</h5>
              <ul className="suggestion-list">
                {itemsArray.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    );
  };

  const renderComplexSuggestions = (suggestions: ComplexSuggestions) => {
    return (
      <div className="complex-suggestions">
        {renderStringList(suggestions.structural_fixes, 'Structural Fixes')}
        {renderStringList(suggestions.content_fixes, 'Content Fixes')}
        {renderSectionUpdates(suggestions.section_updates)}
        {renderStringList(suggestions.final_recommendations, 'Final Recommendations')}
      </div>
    );
  };

  const structuralChecks = [
    { label: 'Single Column', value: results.column, key: 'column' },
    { label: 'Simple Fonts', value: results['simple fonts'], key: 'simple-fonts' },
    { label: 'No Images', value: results['no images'], key: 'no-images' },
    { label: 'Clear Section Headers', value: results['clear section header'], key: 'clear-headers' },
    { label: 'Good Text Alignment', value: !results['poor text alignment'], key: 'alignment' },
    { label: 'No Tables', value: results['no tables'], key: 'no-tables' },
  ];

  return (
    <div className="analysis-results">
      <h2 className="results-title">Analysis Results</h2>

      {/* Score Cards */}
      <div className="score-cards">
        <div className={`score-card ${getScoreColor(results.score['overall score'])}`}>
          <div className="score-label">Overall Score</div>
          <div className="score-value">{results.score['overall score'].toFixed(1)}%</div>
        </div>
        <div className={`score-card ${getScoreColor(results.score['structure score'])}`}>
          <div className="score-label">Structure Score</div>
          <div className="score-value">{results.score['structure score'].toFixed(1)}%</div>
        </div>
        <div className={`score-card ${getScoreColor(results.score['keyword score'])}`}>
          <div className="score-label">Keyword Score</div>
          <div className="score-value">{results.score['keyword score'].toFixed(1)}%</div>
        </div>
      </div>

      {/* Structural Compliance */}
      <div className="results-section">
        <h3 className="section-title">Structural Compliance</h3>
        <div className="compliance-grid">
          {structuralChecks.map((check) => (
            <div key={check.key} className="compliance-item">
              <div className={`compliance-status ${check.value ? 'pass' : 'fail'}`}>
                {check.value ? '✓' : '✗'}
              </div>
              <span className="compliance-label">{check.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Keywords Matched */}
      {results['key words matched'].length > 0 && (
        <div className="results-section">
          <h3 className="section-title">
            Keywords Matched
            <span className="keyword-count">{results['key words matched'].length}</span>
          </h3>
          <div className="keyword-list">
            {results['key words matched'].map((keyword, index) => (
              <span key={index} className="keyword-tag keyword-matched">
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Missing Keywords */}
      {results['keyword missing'].length > 0 && (
        <div className="results-section">
          <h3 className="section-title">
            Missing Keywords
            <span className="keyword-count missing">{results['keyword missing'].length}</span>
          </h3>
          <div className="keyword-list">
            {results['keyword missing'].map((keyword, index) => (
              <span key={index} className="keyword-tag keyword-missing">
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Suggestions */}
      {results.suggestions && (
        <div className="results-section">
          <h3 className="section-title">Suggestions</h3>
          <div className="suggestions-box">
            {isComplexSuggestions(results.suggestions) ? (
              renderComplexSuggestions(results.suggestions)
            ) : (
              <p className="suggestions-text">{results.suggestions}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
