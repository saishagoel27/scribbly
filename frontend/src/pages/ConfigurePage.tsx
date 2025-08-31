import React, { useState, useEffect } from 'react';

interface FileData {
  file: File;
  metadata: {
    filename: string;
    size: number;
    type: string;
    estimatedPages: number;
    estimatedReadingTime: string;
    processingComplexity: 'low' | 'medium' | 'high';
  };
}

interface StudyConfig {
  studyMode: 'flashcards' | 'summary' | 'both';
  flashcardCount?: number;
  difficultyFocus?: 'basic' | 'mixed' | 'advanced' | 'application';
}

interface ConfigurePageProps {
  fileData: FileData;
  onConfigComplete: (config: StudyConfig) => void;
  currentConfig: StudyConfig | null;
}

const ConfigurePage: React.FC<ConfigurePageProps> = ({ 
  fileData, 
  onConfigComplete, 
  currentConfig 
}) => {
  // Form state
  const [studyMode, setStudyMode] = useState<'flashcards' | 'summary' | 'both'>(
    currentConfig?.studyMode || 'both'
  );
  const [flashcardCount, setFlashcardCount] = useState<number>(
    currentConfig?.flashcardCount || 15
  );
  const [difficultyFocus, setDifficultyFocus] = useState<'basic' | 'mixed' | 'advanced' | 'application'>(
    currentConfig?.difficultyFocus || 'mixed'
  );

  // Estimated processing time based on selections
  const getEstimatedTime = () => {
    const baseTime = fileData.metadata.processingComplexity === 'high' ? 180 : 
                     fileData.metadata.processingComplexity === 'medium' ? 120 : 90;
    
    const modeMultiplier = studyMode === 'both' ? 1.5 : 1;
    const countMultiplier = flashcardCount > 20 ? 1.3 : 1;
    
    return Math.round(baseTime * modeMultiplier * countMultiplier);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const config: StudyConfig = {
      studyMode,
      flashcardCount: studyMode !== 'summary' ? flashcardCount : undefined,
      difficultyFocus
    };
    
    onConfigComplete(config);
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    return `${Math.round(seconds / 60)}m`;
  };

  return (
    <div className="configure-page">
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">🎯 Choose Your Study Options</h1>
        <p className="page-subtitle">
          Customize how we process "{fileData.metadata.filename}"
        </p>
      </div>

      {/* File Summary */}
      <div className="file-summary-card">
        <div className="file-summary-info">
          <div className="file-icon">📄</div>
          <div className="file-details">
            <h3>{fileData.metadata.filename}</h3>
            <div className="file-stats">
              <span className="stat-item">📊 {(fileData.metadata.size / (1024 * 1024)).toFixed(1)} MB</span>
              <span className="stat-item">📖 {fileData.metadata.estimatedPages} pages</span>
              <span className="stat-item">⏱️ {fileData.metadata.estimatedReadingTime}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <form onSubmit={handleSubmit} className="config-form">
        {/* Study Mode Selection */}
        <div className="config-section">
          <h3 className="section-title">📚 What would you like to create?</h3>
          <p className="section-subtitle">Choose the study materials that work best for you</p>
          
          <div className="option-grid">
            <div 
              className={`option-card ${studyMode === 'flashcards' ? 'selected' : ''}`}
              onClick={() => setStudyMode('flashcards')}
            >
              <div className="option-icon">🃏</div>
              <h4>Flashcards Only</h4>
              <p>Interactive Q&A cards for active recall and spaced repetition</p>
              <div className="option-benefits">
                <span className="benefit">✨ Quick review sessions</span>
                <span className="benefit">🧠 Memory reinforcement</span>
                <span className="benefit">⚡ Fast generation</span>
              </div>
            </div>

            <div 
              className={`option-card ${studyMode === 'summary' ? 'selected' : ''}`}
              onClick={() => setStudyMode('summary')}
            >
              <div className="option-icon">📝</div>
              <h4>Summary Only</h4>
              <p>Comprehensive overview with key concepts and main points</p>
              <div className="option-benefits">
                <span className="benefit">📋 Organized content</span>
                <span className="benefit">🎯 Key insights</span>
                <span className="benefit">📚 Study guide format</span>
              </div>
            </div>

            <div 
              className={`option-card ${studyMode === 'both' ? 'selected' : ''}`}
              onClick={() => setStudyMode('both')}
            >
              <div className="option-icon">🎯</div>
              <h4>Complete Package</h4>
              <p>Get both flashcards AND summary for comprehensive studying</p>
              <div className="option-benefits">
                <span className="benefit">⭐ Best value</span>
                <span className="benefit">🎨 Multiple formats</span>
                <span className="benefit">📈 Maximum retention</span>
              </div>
              <div className="recommended-badge">Recommended</div>
            </div>
          </div>
        </div>

        {/* Flashcard Configuration */}
        {studyMode !== 'summary' && (
          <div className="config-section">
            <h3 className="section-title">🃏 Flashcard Settings</h3>
            <p className="section-subtitle">Customize your flashcard generation</p>
            
            <div className="setting-group">
              <label className="setting-label">Number of Flashcards</label>
              <div className="count-selector">
                {[5, 10, 15, 20, 25, 30].map(count => (
                  <button
                    key={count}
                    type="button"
                    className={`count-option ${flashcardCount === count ? 'selected' : ''}`}
                    onClick={() => setFlashcardCount(count)}
                  >
                    {count}
                  </button>
                ))}
              </div>
              <p className="setting-hint">
                More cards = better coverage, but longer processing time
              </p>
            </div>
          </div>
        )}

        {/* Difficulty Focus */}
        <div className="config-section">
          <h3 className="section-title">📈 Content Focus</h3>
          <p className="section-subtitle">What level of detail should we emphasize?</p>
          
          <div className="difficulty-options">
            <div 
              className={`difficulty-option ${difficultyFocus === 'basic' ? 'selected' : ''}`}
              onClick={() => setDifficultyFocus('basic')}
            >
              <div className="difficulty-icon">🌱</div>
              <div className="difficulty-content">
                <h4>Basic Concepts</h4>
                <p>Fundamental terms and definitions</p>
              </div>
            </div>

            <div 
              className={`difficulty-option ${difficultyFocus === 'mixed' ? 'selected' : ''}`}
              onClick={() => setDifficultyFocus('mixed')}
            >
              <div className="difficulty-icon">⚖️</div>
              <div className="difficulty-content">
                <h4>Mixed Level</h4>
                <p>Balance of basic and advanced topics</p>
                <span className="recommended-text">Recommended</span>
              </div>
            </div>

            <div 
              className={`difficulty-option ${difficultyFocus === 'advanced' ? 'selected' : ''}`}
              onClick={() => setDifficultyFocus('advanced')}
            >
              <div className="difficulty-icon">🚀</div>
              <div className="difficulty-content">
                <h4>Advanced Topics</h4>
                <p>Complex concepts and detailed analysis</p>
              </div>
            </div>

            <div 
              className={`difficulty-option ${difficultyFocus === 'application' ? 'selected' : ''}`}
              onClick={() => setDifficultyFocus('application')}
            >
              <div className="difficulty-icon">🎯</div>
              <div className="difficulty-content">
                <h4>Application-Based</h4>
                <p>Problem-solving and real-world usage</p>
              </div>
            </div>
          </div>
        </div>

        {/* Processing Summary */}
        <div className="processing-summary">
          <div className="summary-content">
            <h4>📊 Processing Summary</h4>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">Study Mode:</span>
                <span className="summary-value">
                  {studyMode === 'both' ? 'Flashcards + Summary' : 
                   studyMode === 'flashcards' ? 'Flashcards Only' : 'Summary Only'}
                </span>
              </div>
              {studyMode !== 'summary' && (
                <div className="summary-item">
                  <span className="summary-label">Flashcards:</span>
                  <span className="summary-value">{flashcardCount} cards</span>
                </div>
              )}
              <div className="summary-item">
                <span className="summary-label">Difficulty:</span>
                <span className="summary-value">
                  {difficultyFocus.charAt(0).toUpperCase() + difficultyFocus.slice(1)}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Est. Time:</span>
                <span className="summary-value">{formatTime(getEstimatedTime())}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="form-actions">
          <button 
            type="button" 
            className="btn btn-outline"
            onClick={() => window.history.back()}
          >
            ← Back to Upload
          </button>
          <button 
            type="submit" 
            className="btn btn-primary btn-lg"
          >
            🚀 Start Processing →
          </button>
        </div>
      </form>
    </div>
  );
};

export default ConfigurePage;