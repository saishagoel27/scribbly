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
        # Check file size (limit to 50MB)
        MAX_SIZE = 50 * 1024 * 1024  # 50MB
        file_size = 0
        contents = b''
        
        # Read file in chunks to avoid memory issues
        while chunk := await file.read(1024 * 1024):  # Read 1MB at a time
            contents += chunk
            file_size += len(chunk)
            if file_size > MAX_SIZE:
                raise HTTPException(status_code=413, detail="File too large (max 50MB)")
        
        # Get file extension
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        
        # Validate file type
        valid_extensions = ["pdf", "txt", "docx", "jpg", "jpeg", "png"]
        if file_ext not in valid_extensions:
            raise HTTPException(
                status_code=415, 
                detail=f"Unsupported file type. Please upload: {', '.join(valid_extensions)}"
            )
        
        # Process file contents based on file type
        # We're using your existing file_handler for actual processing
        file_metadata = file_handler.process_uploaded_file(
            filename=file.filename,
            content=contents,
            file_type=file_ext
        )
        
        # Return metadata that matches the frontend's expected structure
        return {
            "status": "success",
            "metadata": {
                "filename": file.filename,
                "file_size_bytes": file_size,
                "file_extension": file_ext,
                "estimated_pages": file_metadata.get("page_count", 1),
                "estimated_reading_time": file_metadata.get("reading_time", "1 min"),
                "processing_complexity": file_metadata.get("complexity", "medium")
            }
        }
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Log the error
        logging.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process upload")
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