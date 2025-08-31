import React, { useState, useEffect } from 'react';

interface ProcessingResults {
  flashcards?: Array<{
    question: string;
    answer: string;
    concept: string;
    difficulty: 'basic' | 'intermediate' | 'advanced';
    id: string;
  }>;
  summary?: {
    main: string;
    keyPoints: string[];
    concepts: string[];
  };
  processingMetrics: {
    processingTime: number;
    confidence: number;
    method: string;
  };
  timestamp: string;
}

interface StudyPageProps {
  results: ProcessingResults;
  onNewSession: () => void;
}

const StudyPage: React.FC<StudyPageProps> = ({ results, onNewSession }) => {
  const [currentView, setCurrentView] = useState<'overview' | 'flashcards' | 'summary'>('overview');
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [studyProgress, setStudyProgress] = useState<{[key: string]: 'unseen' | 'learning' | 'mastered'}>({});

  const hasFlashcards = results.flashcards && results.flashcards.length > 0;
  const hasSummary = results.summary;

  useEffect(() => {
    // Initialize study progress
    if (hasFlashcards) {
      const initialProgress: {[key: string]: 'unseen' | 'learning' | 'mastered'} = {};
      results.flashcards!.forEach(card => {
        initialProgress[card.id] = 'unseen';
      });
      setStudyProgress(initialProgress);
    }
  }, [results.flashcards, hasFlashcards]);

  const handleCardAction = (action: 'again' | 'hard' | 'good' | 'easy') => {
    if (!hasFlashcards) return;

    const currentCard = results.flashcards![currentCardIndex];
    const newProgress = { ...studyProgress };

    if (action === 'again' || action === 'hard') {
      newProgress[currentCard.id] = 'learning';
    } else {
      newProgress[currentCard.id] = 'mastered';
    }

    setStudyProgress(newProgress);
    
    // Move to next card
    if (currentCardIndex < results.flashcards!.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1);
      setIsFlipped(false);
    }
  };

  const getProgressStats = () => {
    const total = hasFlashcards ? results.flashcards!.length : 0;
    const mastered = Object.values(studyProgress).filter(status => status === 'mastered').length;
    const learning = Object.values(studyProgress).filter(status => status === 'learning').length;
    const unseen = total - mastered - learning;

    return { total, mastered, learning, unseen };
  };

  const resetCards = () => {
    setCurrentCardIndex(0);
    setIsFlipped(false);
    if (hasFlashcards) {
      const resetProgress: {[key: string]: 'unseen' | 'learning' | 'mastered'} = {};
      results.flashcards!.forEach(card => {
        resetProgress[card.id] = 'unseen';
      });
      setStudyProgress(resetProgress);
    }
  };

  if (currentView === 'overview') {
    return (
      <div className="study-page">
        <div className="page-header">
          <h1 className="page-title">📚 Study Session</h1>
          <p className="page-subtitle">Your personalized study materials are ready!</p>
        </div>

        {/* Study Materials Overview */}
        <div className="study-overview">
          <div className="materials-grid">
            {hasFlashcards && (
              <div className="material-card flashcards-card">
                <div className="material-header">
                  <div className="material-icon">🃏</div>
                  <div className="material-info">
                    <h3>Flashcards</h3>
                    <p>{results.flashcards!.length} cards created</p>
                  </div>
                </div>
                
                <div className="material-stats">
                  <div className="stat-item">
                    <span className="stat-value">{getProgressStats().mastered}</span>
                    <span className="stat-label">Mastered</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-value">{getProgressStats().learning}</span>
                    <span className="stat-label">Learning</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-value">{getProgressStats().unseen}</span>
                    <span className="stat-label">Unseen</span>
                  </div>
                </div>

                <button 
                  className="btn btn-primary material-btn"
                  onClick={() => setCurrentView('flashcards')}
                >
                  🚀 Start Flashcards
                </button>
              </div>
            )}

            {hasSummary && (
              <div className="material-card summary-card">
                <div className="material-header">
                  <div className="material-icon">📝</div>
                  <div className="material-info">
                    <h3>Summary</h3>
                    <p>{results.summary!.keyPoints.length} key points</p>
                  </div>
                </div>
                
                <div className="material-preview">
                  <p>"{results.summary!.main.substring(0, 100)}..."</p>
                </div>

                <button 
                  className="btn btn-primary material-btn"
                  onClick={() => setCurrentView('summary')}
                >
                  📖 Read Summary
                </button>
              </div>
            )}
          </div>

          {/* Processing Info */}
          <div className="processing-info-card">
            <h3>📊 Processing Details</h3>
            <div className="processing-details">
              <div className="detail-item">
                <span className="detail-label">⚡ Processing Time:</span>
                <span className="detail-value">{results.processingMetrics.processingTime}s</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">🎯 Confidence:</span>
                <span className="detail-value">{(results.processingMetrics.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">🔧 Method:</span>
                <span className="detail-value">{results.processingMetrics.method}</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="overview-actions">
            <button 
              className="btn btn-outline"
              onClick={onNewSession}
            >
              📚 New Session
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (currentView === 'flashcards' && hasFlashcards) {
    const currentCard = results.flashcards![currentCardIndex];
    const progress = ((currentCardIndex) / results.flashcards!.length) * 100;

    return (
      <div className="study-page flashcard-mode">
        <div className="flashcard-header">
          <button 
            className="btn btn-outline btn-sm"
            onClick={() => setCurrentView('overview')}
          >
            ← Back to Overview
          </button>
          
          <div className="flashcard-progress">
            <span className="progress-text">
              {currentCardIndex + 1} of {results.flashcards!.length}
            </span>
            <div className="progress-bar-container">
              <div 
                className="progress-bar" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          <button 
            className="btn btn-outline btn-sm"
            onClick={resetCards}
          >
            🔄 Reset
          </button>
        </div>

        <div className="flashcard-container">
          <div className={`flashcard ${isFlipped ? 'flipped' : ''}`}>
            <div className="flashcard-front">
              <div className="card-content">
                <div className="card-type">Question</div>
                <h2>{currentCard.question}</h2>
                <div className="card-meta">
                  <span className="difficulty-badge difficulty-{currentCard.difficulty}">
                    {currentCard.difficulty}
                  </span>
                  <span className="concept-tag">{currentCard.concept}</span>
                </div>
              </div>
              <button 
                className="btn btn-primary flip-btn"
                onClick={() => setIsFlipped(true)}
              >
                Show Answer
              </button>
            </div>

            <div className="flashcard-back">
              <div className="card-content">
                <div className="card-type">Answer</div>
                <h2>{currentCard.answer}</h2>
                <div className="card-meta">
                  <span className="difficulty-badge difficulty-{currentCard.difficulty}">
                    {currentCard.difficulty}
                  </span>
                  <span className="concept-tag">{currentCard.concept}</span>
                </div>
              </div>

              <div className="answer-actions">
                <button 
                  className="btn btn-difficulty again"
                  onClick={() => handleCardAction('again')}
                >
                  Again
                </button>
                <button 
                  className="btn btn-difficulty hard"
                  onClick={() => handleCardAction('hard')}
                >
                  Hard
                </button>
                <button 
                  className="btn btn-difficulty good"
                  onClick={() => handleCardAction('good')}
                >
                  Good
                </button>
                <button 
                  className="btn btn-difficulty easy"
                  onClick={() => handleCardAction('easy')}
                >
                  Easy
                </button>
              </div>
            </div>
          </div>
        </div>

        {currentCardIndex >= results.flashcards!.length - 1 && (
          <div className="study-complete">
            <h3>🎉 Study Session Complete!</h3>
            <div className="completion-stats">
              <div className="stat">
                <span className="stat-number">{getProgressStats().mastered}</span>
                <span className="stat-label">Mastered</span>
              </div>
              <div className="stat">
                <span className="stat-number">{getProgressStats().learning}</span>
                <span className="stat-label">Need Review</span>
              </div>
            </div>
            <div className="completion-actions">
              <button className="btn btn-primary" onClick={resetCards}>
                🔄 Study Again
              </button>
              <button className="btn btn-outline" onClick={() => setCurrentView('overview')}>
                📚 Back to Overview
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (currentView === 'summary' && hasSummary) {
    return (
      <div className="study-page summary-mode">
        <div className="summary-header">
          <button 
            className="btn btn-outline btn-sm"
            onClick={() => setCurrentView('overview')}
          >
            ← Back to Overview
          </button>
          <h1>📝 Study Summary</h1>
        </div>

        <div className="summary-content">
          <div className="summary-main">
            <h2>📖 Overview</h2>
            <p>{results.summary!.main}</p>
          </div>

          <div className="summary-keypoints">
            <h2>🎯 Key Points</h2>
            <ul>
              {results.summary!.keyPoints.map((point, index) => (
                <li key={index}>{point}</li>
              ))}
            </ul>
          </div>

          <div className="summary-concepts">
            <h2>🧠 Important Concepts</h2>
            <div className="concepts-grid">
              {results.summary!.concepts.map((concept, index) => (
                <div key={index} className="concept-card">
                  {concept}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default StudyPage;