import React, { useState, useCallback } from 'react';
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

interface UploadPageProps {
  onFileUploaded: (fileData: FileData) => void;
  currentFileData: FileData | null;
}

const UploadPage: React.FC<UploadPageProps> = ({ onFileUploaded, currentFileData }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Handle file drop
  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  // Handle file input change
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  // Upload file to backend
  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000, // 30 second timeout
      });

      // Transform backend response to match our FileData interface
      const fileData: FileData = {
        file,
        metadata: {
          filename: response.data.metadata.filename,
          size: response.data.metadata.file_size_bytes,
          type: response.data.metadata.file_extension,
          estimatedPages: response.data.metadata.estimated_pages,
          estimatedReadingTime: response.data.metadata.estimated_reading_time,
          processingComplexity: response.data.metadata.processing_complexity,
        },
      };

      onFileUploaded(fileData);
    } catch (error: any) {
      console.error('Upload failed:', error);
      if (error.response?.data?.detail) {
        setUploadError(error.response.data.detail);
      } else if (error.code === 'ECONNABORTED') {
        setUploadError('Upload timed out. Please try a smaller file.');
      } else {
        setUploadError('Upload failed. Please try again.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="upload-page">
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">📚 Upload Your Study Material</h1>
        <p className="page-subtitle">
          Transform your notes into personalized flashcards and summaries with AI
        </p>
      </div>

      {/* Upload Section */}
      {!currentFileData ? (
        <div className="upload-section">
          {/* Drop Zone */}
          <div
            className={`upload-dropzone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            {isUploading ? (
              <div className="upload-progress">
                <div className="upload-spinner"></div>
                <h3>Processing your file...</h3>
                <p>Analyzing content and extracting metadata</p>
              </div>
            ) : (
              <div className="upload-content">
                <div className="upload-icon">
                  📄
                </div>
                <h3>Drag and drop your file here</h3>
                <p>or click to browse your files</p>
                
                <input
                  type="file"
                  id="file-input"
                  className="file-input"
                  accept=".pdf,.jpg,.jpeg,.png,.txt,.docx"
                  onChange={handleFileInputChange}
                  disabled={isUploading}
                />
                <label htmlFor="file-input" className="btn btn-primary btn-lg">
                  📁 Choose File
                </label>
              </div>
            )}
          </div>

          {/* Supported Formats */}
          <div className="supported-formats">
            <h4>📋 Supported File Types</h4>
            <div className="format-grid">
              <div className="format-item">
                <span className="format-icon">📄</span>
                <span className="format-label">PDF Documents</span>
              </div>
              <div className="format-item">
                <span className="format-icon">🖼️</span>
                <span className="format-label">Images (JPG, PNG)</span>
              </div>
              <div className="format-item">
                <span className="format-icon">📝</span>
                <span className="format-label">Text Files</span>
              </div>
              <div className="format-item">
                <span className="format-icon">📋</span>
                <span className="format-label">Word Documents</span>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {uploadError && (
            <div className="error-message">
              <span className="error-icon">❌</span>
              <div className="error-content">
                <h4>Upload Failed</h4>
                <p>{uploadError}</p>
              </div>
            </div>
          )}

          {/* Tips Section */}
          <div className="upload-tips">
            <h4>💡 Tips for Best Results</h4>
            <div className="tips-grid">
              <div className="tip-item">
                <span className="tip-icon">✨</span>
                <p><strong>High Quality:</strong> Use clear, high-resolution images</p>
              </div>
              <div className="tip-item">
                <span className="tip-icon">📖</span>
                <p><strong>Readable Text:</strong> Ensure text is clearly visible</p>
              </div>
              <div className="tip-item">
                <span className="tip-icon">📏</span>
                <p><strong>File Size:</strong> Maximum 10MB per file</p>
              </div>
              <div className="tip-item">
                <span className="tip-icon">🎯</span>
                <p><strong>Content:</strong> Study materials work best</p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* File Preview - when file is uploaded */
        <div className="file-preview-section">
          <div className="file-preview-card">
            <div className="file-info">
              <div className="file-icon">
                📄
              </div>
              <div className="file-details">
                <h3 className="file-name">{currentFileData.metadata.filename}</h3>
                <div className="file-meta">
                  <span className="meta-item">
                    📊 {(currentFileData.metadata.size / (1024 * 1024)).toFixed(1)} MB
                  </span>
                  <span className="meta-item">
                    📖 {currentFileData.metadata.estimatedPages} pages
                  </span>
                  <span className="meta-item">
                    ⏱️ {currentFileData.metadata.estimatedReadingTime}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="file-actions">
              <button 
                className="btn btn-outline"
                onClick={() => {
                  setUploadError(null);
                  onFileUploaded(null as any); // Reset to allow new upload
                }}
              >
                🔄 Upload Different File
              </button>
              <button 
                className="btn btn-primary"
                onClick={() => {
                  // This will be handled by the App component routing
                  window.location.href = '/configure';
                }}
              >
                Continue → 
              </button>
            </div>
          </div>

          {/* Processing Preview */}
          <div className="processing-preview">
            <h4>🔍 What happens next?</h4>
            <div className="preview-steps">
              <div className="preview-step">
                <span className="step-number">1</span>
                <div className="step-content">
                  <h5>Choose Your Options</h5>
                  <p>Select flashcards, summaries, or both</p>
                </div>
              </div>
              <div className="preview-step">
                <span className="step-number">2</span>
                <div className="step-content">
                  <h5>AI Processing</h5>
                  <p>Our AI analyzes your content</p>
                </div>
              </div>
              <div className="preview-step">
                <span className="step-number">3</span>
                <div className="step-content">
                  <h5>Start Studying</h5>
                  <p>Use your personalized materials</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;