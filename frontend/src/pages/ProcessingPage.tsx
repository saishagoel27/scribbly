import React, { useState, useEffect } from 'react';
import axios from 'axios';

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

interface ProcessingPageProps {
  fileData: FileData;
  studyConfig: StudyConfig;
  onStartProcessing: () => void;
  onProcessingComplete: (results: ProcessingResults) => void;
  isProcessing: boolean;
}

const ProcessingPage: React.FC<ProcessingPageProps> = ({
  fileData,
  studyConfig,
  onStartProcessing,
  onProcessingComplete,
  isProcessing
}) => {
  const [processingStep, setProcessingStep] = useState<string>('ready');
  const [processingProgress, setProcessingProgress] = useState<number>(0);
  const [processingError, setProcessingError] = useState<string | null>(null);

  const processingSteps = [
    { id: 'extracting', label: 'Extracting content', icon: '🔍' },
    { id: 'analyzing', label: 'Analyzing concepts', icon: '🧠' },
    { id: 'generating', label: 'Creating study materials', icon: '✨' },
    { id: 'finalizing', label: 'Finalizing results', icon: '🎯' }
  ];

  const handleStartProcessing = async () => {
    onStartProcessing();
    setProcessingError(null);
    setProcessingStep('extracting');
    setProcessingProgress(10);

    try {
      // ✅ FIXED: Proper FormData creation and sending
      const formData = new FormData();
      formData.append('file', fileData.file);
      formData.append('study_mode', studyConfig.studyMode);
      
      if (studyConfig.flashcardCount) {
        formData.append('flashcard_count', studyConfig.flashcardCount.toString());
      }
      if (studyConfig.difficultyFocus) {
        formData.append('difficulty_focus', studyConfig.difficultyFocus);
      }

      setProcessingStep('analyzing');
      setProcessingProgress(25);

      // ✅ FIXED: Correct endpoint and FormData
      const response = await axios.post('/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minute timeout for AI processing
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setProcessingProgress(25 + Math.round(uploadProgress * 0.25)); // 25% to 50%
          }
        }
      });

      setProcessingStep('generating');
      setProcessingProgress(75);

      // ✅ FIXED: Process the actual response from your backend
      if (response.data.status === 'success') {
        setProcessingStep('finalizing');
        setProcessingProgress(100);

        const results: ProcessingResults = {
          flashcards: response.data.flashcards || [],
          summary: response.data.summary || null,
          processingMetrics: {
            processingTime: response.data.processing_time || 45,
            confidence: response.data.confidence || 0.92,
            method: response.data.method || 'hybrid'
          },
          timestamp: new Date().toISOString()
        };

        // Small delay to show completion
        setTimeout(() => {
          onProcessingComplete(results);
        }, 1000);

      } else {
        throw new Error(response.data.error || 'Processing failed');
      }

    } catch (error: any) {
      console.error('Processing failed:', error);
      
      // ✅ FIXED: Better error handling
      let errorMessage = 'Processing failed. Please try again.';
      
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Processing timed out. Your file may be too large or complex.';
      } else if (error.response?.status === 413) {
        errorMessage = 'File too large. Please try a smaller file.';
      } else if (error.response?.status === 422) {
        errorMessage = 'File format not supported or corrupted.';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error. Our AI services may be temporarily unavailable.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setProcessingError(errorMessage);
      
      // Reset processing state on error
      setProcessingStep('ready');
      setProcessingProgress(0);
    }
  };

  const getCurrentStepIndex = () => {
    return processingSteps.findIndex(step => step.id === processingStep);
  };

  return (
    <div className="processing-page">
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">🔍 Processing Your Material</h1>
        <p className="page-subtitle">
          Creating {studyConfig.studyMode} from "{fileData.metadata.filename}"
        </p>
      </div>

      {/* Configuration Summary */}
      <div className="processing-summary-card">
        <div className="summary-header">
          <h3>📊 Processing Configuration</h3>
        </div>
        <div className="summary-details">
          <div className="summary-row">
            <span className="summary-label">📄 File:</span>
            <span className="summary-value">{fileData.metadata.filename}</span>
          </div>
          <div className="summary-row">
            <span className="summary-label">🎯 Mode:</span>
            <span className="summary-value">
              {studyConfig.studyMode === 'both' ? 'Flashcards + Summary' :
               studyConfig.studyMode === 'flashcards' ? 'Flashcards Only' : 'Summary Only'}
            </span>
          </div>
          {studyConfig.flashcardCount && (
            <div className="summary-row">
              <span className="summary-label">🃏 Cards:</span>
              <span className="summary-value">{studyConfig.flashcardCount} flashcards</span>
            </div>
          )}
          <div className="summary-row">
            <span className="summary-label">📈 Focus:</span>
            <span className="summary-value">
              {studyConfig.difficultyFocus?.charAt(0).toUpperCase() + studyConfig.difficultyFocus?.slice(1)}
            </span>
          </div>
          <div className="summary-row">
            <span className="summary-label">📊 Pages:</span>
            <span className="summary-value">{fileData.metadata.estimatedPages}</span>
          </div>
          <div className="summary-row">
            <span className="summary-label">⏱️ Est. Reading:</span>
            <span className="summary-value">{fileData.metadata.estimatedReadingTime}</span>
          </div>
        </div>
      </div>

      {/* Processing Status */}
      {!isProcessing && !processingError ? (
        /* Ready to Start */
        <div className="processing-ready">
          <div className="ready-content">
            <div className="ready-icon">🚀</div>
            <h3>Ready to Process</h3>
            <p>
              We'll analyze your content and generate personalized study materials
              using advanced AI techniques.
            </p>
            
            <div className="processing-features">
              <div className="feature-item">
                <span className="feature-icon">🔍</span>
                <div className="feature-content">
                  <h4>Content Analysis</h4>
                  <p>Extract and understand key concepts</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🧠</span>
                <div className="feature-content">
                  <h4>AI Processing</h4>
                  <p>Generate intelligent questions and summaries</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">✨</span>
                <div className="feature-content">
                  <h4>Optimization</h4>
                  <p>Tailor content to your learning preferences</p>
                </div>
              </div>
            </div>

            <button 
              className="btn btn-primary btn-lg processing-start-btn"
              onClick={handleStartProcessing}
            >
              🚀 Start Processing
            </button>
          </div>
        </div>
      ) : isProcessing ? (
        /* Processing in Progress */
        <div className="processing-active">
          <div className="processing-progress">
            <div className="progress-header">
              <h3>Processing in Progress...</h3>
              <span className="progress-percentage">{processingProgress}%</span>
            </div>
            
            {/* Progress Bar */}
            <div className="progress-bar-container">
              <div 
                className="progress-bar"
                style={{ width: `${processingProgress}%` }}
              ></div>
            </div>

            {/* Processing Steps */}
            <div className="processing-steps">
              {processingSteps.map((step, index) => {
                const currentIndex = getCurrentStepIndex();
                const isActive = index === currentIndex;
                const isCompleted = index < currentIndex;
                
                return (
                  <div 
                    key={step.id}
                    className={`processing-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                  >
                    <div className="step-icon">{step.icon}</div>
                    <div className="step-content">
                      <h4>{step.label}</h4>
                      {isActive && <div className="step-spinner"></div>}
                      {isCompleted && <div className="step-checkmark">✓</div>}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="processing-tips">
              <h4>💡 While you wait:</h4>
              <ul>
                <li>Our AI is carefully analyzing your content structure</li>
                <li>We're identifying key concepts and relationships</li>
                <li>Questions are being crafted for optimal learning</li>
                <li>Processing time varies based on content complexity</li>
              </ul>
            </div>
          </div>
        </div>
      ) : processingError ? (
        /* Error State */
        <div className="processing-error">
          <div className="error-content">
            <div className="error-icon">❌</div>
            <h3>Processing Failed</h3>
            <p>{processingError}</p>
            
            <div className="error-suggestions">
              <h4>💡 Try these solutions:</h4>
              <ul>
                <li>Check your internet connection</li>
                <li>Ensure your file is readable and not corrupted</li>
                <li>Try with a smaller file or fewer flashcards</li>
                <li>Refresh the page and try again</li>
              </ul>
            </div>

            <div className="error-actions">
              <button 
                className="btn btn-primary"
                onClick={handleStartProcessing}
              >
                🔄 Retry Processing
              </button>
              <button 
                className="btn btn-outline"
                onClick={() => window.history.back()}
              >
                ← Back to Configuration
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Processing Actions */}
      {!isProcessing && !processingError && (
        <div className="processing-actions">
          <button 
            className="btn btn-outline"
            onClick={() => window.history.back()}
          >
            ← Back to Configuration
          </button>
        </div>
      )}
    </div>
  );
};

export default ProcessingPage;