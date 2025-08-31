import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './globals.css';
import './components.css';

// Import all real components
import UploadPage from './pages/UploadPage.tsx';
import ConfigurePage from './pages/ConfigurePage.tsx';
import ProcessingPage from './pages/ProcessingPage.tsx';
import StudyPage from './pages/StudyPage.tsx';

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

export default App;