import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './styles/globals.css';

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

interface AppState {
  currentStep: number;
  fileData: FileData | null;
  studyConfig: StudyConfig | null;
  isProcessing: boolean;
}

const App: React.FC = () => {
  // Application state management
  const [appState, setAppState] = useState<AppState>({
    currentStep: 1,
    fileData: null,
    studyConfig: null,
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

  const resetSession = () => {
    setAppState({
      currentStep: 1,
      fileData: null,
      studyConfig: null,
      isProcessing: false
    });
    localStorage.removeItem('scribbly-state');
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
                <div className={`step ${appState.currentStep >= 1 ? 'active' : ''}`}>
                  <span className="step-icon">📁</span>
                  <span className="step-label">Upload</span>
                </div>
                <div className="step-divider"></div>
                <div className={`step ${appState.currentStep >= 2 ? 'active' : ''}`}>
                  <span className="step-icon">🎯</span>
                  <span className="step-label">Choose</span>
                </div>
                <div className="step-divider"></div>
                <div className={`step ${appState.currentStep >= 3 ? 'active' : ''}`}>
                  <span className="step-icon">🔍</span>
                  <span className="step-label">Process</span>
                </div>
                <div className="step-divider"></div>
                <div className={`step ${appState.currentStep >= 4 ? 'active' : ''}`}>
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
                  appState.studyConfig ? (
                    <ProcessingPage 
                      fileData={appState.fileData!}
                      studyConfig={appState.studyConfig}
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
                      "/processing"
                    } 
                  />
                } 
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

        {/* Processing Overlay */}
        {appState.isProcessing && (
          <div className="processing-overlay">
            <div className="processing-modal">
              <div className="spinner"></div>
              <h3>Creating Your Study Materials</h3>
              <p>This may take a few moments...</p>
            </div>
          </div>
        )}
      </div>
    </Router>
  );
};

// Placeholder components - we'll create these next
const UploadPage: React.FC<any> = ({ onFileUploaded, currentFileData }) => (
  <div className="page-placeholder">
    <h2>📁 Upload Your Study Material</h2>
    <p>Upload page will be implemented next</p>
  </div>
);

const ConfigurePage: React.FC<any> = ({ fileData, onConfigComplete, currentConfig }) => (
  <div className="page-placeholder">
    <h2>🎯 Choose Your Study Options</h2>
    <p>Configuration page will be implemented next</p>
  </div>
);

const ProcessingPage: React.FC<any> = ({ fileData, studyConfig }) => (
  <div className="page-placeholder">
    <h2>🔍 Processing Your Material</h2>
    <p>Processing page will be implemented next</p>
  </div>
);

export default App;