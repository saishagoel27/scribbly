import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './styles/globals.css';
import './styles/components.css';

// Import the UploadPage component 
import UploadPage from '../pages/UploadPage';
import ConfigurePage from '../pages/ConfigurePage'; 
import ProcessingPage from '../pages/ProcessingPage';
import StudyPage from '../pages/StudyPage';

// Types
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

interface AppState {
  currentStep: number;
  fileData: FileData | null;
  studyConfig: StudyConfig | null;
  processingResults: ProcessingResults | null;
  isProcessing: boolean;
}

const App: React.FC = () => {
  // Application state management
  const [appState, setAppState] = useState<AppState>({
    currentStep: 1,
    fileData: null,
    studyConfig: null,
    processingResults: null,
    isProcessing: false
  });

  // Load saved state from localStorage
  useEffect(() => {
    const savedState = localStorage.getItem('scribbly-state');
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        setAppState(parsed);
      } catch (error) {
        console.error('Failed to load saved state:', error);
      }
    }
  }, []);

  // Save state whenever it changes
  useEffect(() => {
    localStorage.setItem('scribbly-state', JSON.stringify(appState));
  }, [appState]);

  // State update functions
  const updateFileData = (fileData: FileData) => {
    setAppState(prev => ({
      ...prev,
      fileData,
      currentStep: 2
    }));
  };

  const updateStudyConfig = (studyConfig: StudyConfig) => {
    setAppState(prev => ({
      ...prev,
      studyConfig,
      currentStep: 3
    }));
  };

  const startProcessing = () => {
    setAppState(prev => ({
      ...prev,
      isProcessing: true
    }));
  };

  const completeProcessing = (results: ProcessingResults) => {
    setAppState(prev => ({
      ...prev,
      processingResults: results,
      isProcessing: false,
      currentStep: 4
    }));
  };

  const resetSession = () => {
    setAppState({
      currentStep: 1,
      fileData: null,
      studyConfig: null,
      processingResults: null,
      isProcessing: false
    });
    localStorage.removeItem('scribbly-state');
  };

  const goToStep = (step: number) => {
    // Only allow going back to completed steps
    if (step <= appState.currentStep) {
      setAppState(prev => ({
        ...prev,
        currentStep: step
      }));
    }
  };

  return (
    <Router>
      <div className="app">
        {/* Professional Header */}
        <header className="app-header">
          <div className="container">
            <div className="header-content">
              <div className="logo-section">
                <h1 className="logo">🧠 Scribbly</h1>
                <p className="tagline">AI Study Helper</p>
              </div>
              
              {/* Progress Indicator */}
              <div className="progress-steps">
                <div 
                  className={`step ${appState.currentStep >= 1 ? 'active' : ''} ${appState.currentStep > 1 ? 'completed' : ''}`}
                  onClick={() => goToStep(1)}
                >
                  <span className="step-icon">📁</span>
                  <span className="step-label">Upload</span>
                </div>
                <div className="step-divider"></div>
                <div 
                  className={`step ${appState.currentStep >= 2 ? 'active' : ''} ${appState.currentStep > 2 ? 'completed' : ''}`}
                  onClick={() => goToStep(2)}
                >
                  <span className="step-icon">🎯</span>
                  <span className="step-label">Choose</span>
                </div>
                <div className="step-divider"></div>
                <div 
                  className={`step ${appState.currentStep >= 3 ? 'active' : ''} ${appState.currentStep > 3 ? 'completed' : ''}`}
                >
                  <span className="step-icon">🔍</span>
                  <span className="step-label">Process</span>
                </div>
                <div className="step-divider"></div>
                <div 
                  className={`step ${appState.currentStep >= 4 ? 'active' : ''}`}
                >
                  <span className="step-icon">📚</span>
                  <span className="step-label">Study</span>
                </div>
              </div>

              <button 
                className="btn btn-outline btn-sm"
                onClick={resetSession}
                title="Start Over"
              >
                🔄 Reset
              </button>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="main-content">
          <div className="container">
            <Routes>
              {/* Step 1: Upload */}
              <Route 
                path="/upload" 
                element={
                  <UploadPage 
                    onFileUploaded={updateFileData}
                    currentFileData={appState.fileData}
                  />
                } 
              />

              {/* Step 2: Configure */}
              <Route 
                path="/configure" 
                element={
                  appState.fileData ? (
                    <ConfigurePage 
                      fileData={appState.fileData}
                      onConfigComplete={updateStudyConfig}
                      currentConfig={appState.studyConfig}
                    />
                  ) : (
                    <Navigate to="/upload" />
                  )
                } 
              />

              {/* Step 3: Processing */}
              <Route 
                path="/processing" 
                element={
                  appState.studyConfig && appState.fileData ? (
                    <ProcessingPage 
                      fileData={appState.fileData}
                      studyConfig={appState.studyConfig}
                      onStartProcessing={startProcessing}
                      onProcessingComplete={completeProcessing}
                      isProcessing={appState.isProcessing}
                    />
                  ) : (
                    <Navigate to="/upload" />
                  )
                } 
              />

              {/* Step 4: Study */}
              <Route 
                path="/study/*" 
                element={
                  appState.processingResults ? (
                    <StudyPage 
                      results={appState.processingResults}
                      onNewSession={resetSession}
                    />
                  ) : (
                    <Navigate to="/upload" />
                  )
                } 
              />

              {/* Default redirect based on current state */}
              <Route 
                path="/" 
                element={
                  <Navigate 
                    to={
                      appState.currentStep === 1 ? "/upload" :
                      appState.currentStep === 2 ? "/configure" :
                      appState.currentStep === 3 ? "/processing" :
                      appState.currentStep === 4 ? "/study" :
                      "/upload"
                    } 
                  />
                } 
              />

              {/* Catch-all redirect */}
              <Route 
                path="*" 
                element={<Navigate to="/" />} 
              />
            </Routes>
          </div>
        </main>

        {/* Professional Footer */}
        <footer className="app-footer">
          <div className="container">
            <div className="footer-content">
              <p>&copy; 2024 Scribbly AI Study Helper. Transform your notes into knowledge.</p>
              <div className="footer-links">
                <button className="footer-link">Help</button>
                <button className="footer-link">About</button>
              </div>
            </div>
          </div>
        </footer>

        {/* Global Processing Overlay */}
        {appState.isProcessing && (
          <div className="processing-overlay">
            <div className="processing-modal">
              <div className="spinner"></div>
              <h3>Creating Your Study Materials</h3>
              <p>Our AI is analyzing your content and generating personalized study materials...</p>
              <div className="processing-steps">
                <div className="processing-step">🔍 Extracting content</div>
                <div className="processing-step">🧠 Analyzing concepts</div>
                <div className="processing-step">🃏 Creating flashcards</div>
                <div className="processing-step">📝 Generating summary</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Router>
  );
};

// Temporary placeholder components (will be replaced with real components)
const ConfigurePage: React.FC<{
  fileData: FileData;
  onConfigComplete: (config: StudyConfig) => void;
  currentConfig: StudyConfig | null;
}> = ({ fileData, onConfigComplete, currentConfig }) => (
  <div className="page-placeholder">
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">🎯 Choose Your Study Options</h2>
        <p className="card-subtitle">Customize how we process "{fileData.metadata.filename}"</p>
      </div>
      
      <div className="placeholder-content">
        <p>Configuration page will be implemented next with options for:</p>
        <ul>
          <li>📚 Study mode selection (flashcards, summary, or both)</li>
          <li>🎯 Number of flashcards</li>
          <li>📈 Difficulty focus</li>
          <li>⚙️ Custom processing options</li>
        </ul>
        
        <div className="placeholder-actions">
          <button 
            className="btn btn-primary"
            onClick={() => onConfigComplete({
              studyMode: 'both',
              flashcardCount: 10,
              difficultyFocus: 'mixed'
            })}
          >
            Continue with Default Settings →
          </button>
        </div>
      </div>
    </div>
  </div>
);

const ProcessingPage: React.FC<{
  fileData: FileData;
  studyConfig: StudyConfig;
  onStartProcessing: () => void;
  onProcessingComplete: (results: ProcessingResults) => void;
  isProcessing: boolean;
}> = ({ fileData, studyConfig, onStartProcessing, onProcessingComplete, isProcessing }) => {
  
  const handleStartProcessing = () => {
    onStartProcessing();
    
    // Simulate processing for demo (replace with real API call)
    setTimeout(() => {
      const mockResults: ProcessingResults = {
        flashcards: [
          {
            id: '1',
            question: 'Sample question from your content',
            answer: 'Sample answer generated by AI',
            concept: 'Main Concept',
            difficulty: 'intermediate'
          }
        ],
        summary: {
          main: 'AI-generated summary of your content',
          keyPoints: ['Key point 1', 'Key point 2', 'Key point 3'],
          concepts: ['Concept A', 'Concept B', 'Concept C']
        },
        processingMetrics: {
          processingTime: 45,
          confidence: 0.92,
          method: 'hybrid'
        },
        timestamp: new Date().toISOString()
      };
      
      onProcessingComplete(mockResults);
    }, 5000);
  };
  
  return (
    <div className="page-placeholder">
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">🔍 Processing Your Material</h2>
          <p className="card-subtitle">
            Ready to create {studyConfig.studyMode} from "{fileData.metadata.filename}"
          </p>
        </div>
        
        {!isProcessing ? (
          <div className="placeholder-content">
            <p>Processing configuration:</p>
            <ul>
              <li>📄 File: {fileData.metadata.filename}</li>
              <li>🎯 Mode: {studyConfig.studyMode}</li>
              <li>📊 Pages: {fileData.metadata.estimatedPages}</li>
              <li>⏱️ Est. time: {fileData.metadata.estimatedReadingTime}</li>
            </ul>
            
            <div className="placeholder-actions">
              <button 
                className="btn btn-primary btn-lg"
                onClick={handleStartProcessing}
              >
                🚀 Start Processing
              </button>
            </div>
          </div>
        ) : (
          <div className="placeholder-content">
            <p>Processing in progress... Please wait.</p>
          </div>
        )}
      </div>
    </div>
  );
};

const StudyPage: React.FC<{
  results: ProcessingResults;
  onNewSession: () => void;
}> = ({ results, onNewSession }) => (
  <div className="page-placeholder">
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">📚 Study Session</h2>
        <p className="card-subtitle">Your personalized study materials are ready!</p>
      </div>
      
      <div className="placeholder-content">
        <p>Study materials generated:</p>
        <ul>
          {results.flashcards && (
            <li>🃏 {results.flashcards.length} flashcards created</li>
          )}
          {results.summary && (
            <li>📝 Summary with {results.summary.keyPoints.length} key points</li>
          )}
          <li>⚡ Processing time: {results.processingMetrics.processingTime}s</li>
          <li>🎯 Confidence: {(results.processingMetrics.confidence * 100).toFixed(0)}%</li>
        </ul>
        
        <div className="placeholder-actions">
          <button className="btn btn-primary">
            🚀 Start Studying
          </button>
          <button 
            className="btn btn-outline"
            onClick={onNewSession}
          >
            📚 New Session
          </button>
        </div>
      </div>
    </div>
  </div>
);

export default App;