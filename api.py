from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import Dict, Any

# Import your existing modules
from file_handler import file_handler
from workflow import execute_processing, ProcessingContext
from config import Config

app = FastAPI(title="Scribbly API", description="AI Study Helper Backend")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Scribbly AI Study Helper API"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process file"""
    try:
        # Use your existing file handler
        file_data = file_handler._process_uploaded_file(file)
        
        if "error" in file_data:
            raise HTTPException(status_code=400, detail=file_data["error"])
        
        return JSONResponse(content=file_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process")
async def process_content(request_data: Dict[str, Any]):
    """Process content with AI services"""
    try:
        # Use your existing workflow
        context = ProcessingContext(
            file_data=request_data["fileData"],
            generation_choice=request_data["studyConfig"]["studyMode"],
            study_settings=request_data["studyConfig"]
        )
        
        # Process using your existing pipeline
        # (You'll need to adapt this for FastAPI)
        
        return JSONResponse(content={"status": "processing_started"})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    """Check service health"""
    services = Config.get_available_services()
    return {"status": "healthy", "services": services}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)