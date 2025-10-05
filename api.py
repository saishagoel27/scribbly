from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import time
import uuid
from pydantic import BaseModel

# Import your existing modules
from file_handler import file_handler
from workflow import ProcessingPipeline, ProcessingContext
from config import Config
from flashcards import gemini_generator
from azure_language import azure_language_processor
from azure_document import AzureDocumentProcessor
from fallbacks import create_basic_flashcards

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Scribbly API", description="AI Study Helper Backend")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for job status (would use Redis/DB in production)
processing_jobs = {}

class ProgressReporter:
    """Progress reporter for API processing"""
    def __init__(self, job_id: str):
        self.job_id = job_id
        
    def report(self, message: str, progress: float) -> None:
        """Report progress to the in-memory store"""
        if self.job_id in processing_jobs:
            processing_jobs[self.job_id]["progress"] = min(progress * 100, 100)
            processing_jobs[self.job_id]["message"] = message
            processing_jobs[self.job_id]["last_update"] = time.time()
            logger.info(f"Job {self.job_id}: {message} - {progress:.2f}")

class ProcessRequest(BaseModel):
    """Model for process request data"""
    fileData: Dict[str, Any]
    studyConfig: Dict[str, Any]

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

def process_content_task(job_id: str, context: ProcessingContext) -> None:
    """Background task for content processing"""
    try:
        logger.info(f"Starting processing job {job_id}")
        processing_jobs[job_id]["status"] = "processing"
        
        # Initialize the progress reporter
        progress_reporter = ProgressReporter(job_id)
        
        # Create and execute pipeline
        pipeline = ProcessingPipeline()
        success = pipeline.execute(context, progress_reporter)
        
        if success:
            # Format results to match the frontend's expected structure
            formatted_results = {
                "flashcards": [],
                "summary": None,
                "processingMetrics": {
                    "processingTime": 0,
                    "confidence": 0,
                    "method": "Azure AI Enhanced"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add flashcards if available
            if context.flashcards_result and "flashcards" in context.flashcards_result:
                formatted_results["flashcards"] = [
                    {
                        "id": str(i+1),
                        "question": card["question"],
                        "answer": card["answer"],
                        "concept": card["concept"],
                        "difficulty": card["difficulty"]
                    }
                    for i, card in enumerate(context.flashcards_result["flashcards"])
                ]
                
                # Add metrics
                if "generation_metadata" in context.flashcards_result:
                    metadata = context.flashcards_result["generation_metadata"]
                    formatted_results["processingMetrics"]["processingTime"] = metadata.get("generation_time_seconds", 0)
                    formatted_results["processingMetrics"]["confidence"] = metadata.get("quality_score", 0.8)
                    formatted_results["processingMetrics"]["method"] = metadata.get("method", "AI Enhanced")
            
            # Add summary if available
            if context.language_result:
                summary_text = context.language_result.get("summary", {}).get("extractive_summary", "")
                key_points = context.language_result.get("key_phrases", {}).get("azure_key_phrases", [])
                concepts = [phrase for phrase in key_points[:10]]  # Use top key phrases as concepts
                
                formatted_results["summary"] = {
                    "main": summary_text,
                    "keyPoints": key_points[:15],  # Limit to top 15
                    "concepts": concepts
                }
            
            # Store the results
            processing_jobs[job_id]["results"] = formatted_results
            processing_jobs[job_id]["status"] = "completed"
            processing_jobs[job_id]["progress"] = 100
            processing_jobs[job_id]["message"] = "Processing completed successfully"
            
            logger.info(f"Job {job_id} completed successfully")
            
        else:
            # Handle failure
            processing_jobs[job_id]["status"] = "failed"
            processing_jobs[job_id]["error"] = context.error or "Unknown error occurred"
            logger.error(f"Job {job_id} failed: {context.error}")
            
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)

@app.post("/api/process")
async def process_content(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Process content with AI services"""
    try:
        # Validate required keys
        if "fileData" not in request.dict() or "studyConfig" not in request.dict():
            raise HTTPException(status_code=400, detail="Missing required data")
            
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Create processing context
        context = ProcessingContext(
            file_data=request.fileData,
            generation_choice=request.studyConfig["studyMode"],
            study_settings={
                "num_flashcards": request.studyConfig.get("flashcardCount", Config.DEFAULT_FLASHCARD_COUNT),
                "difficulty": request.studyConfig.get("difficultyFocus", "mixed")
            }
        )
        
        # Initialize job status
        processing_jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "Job queued",
            "created": time.time(),
            "last_update": time.time(),
            "results": None,
            "error": None
        }
        
        # Start background processing task
        background_tasks.add_task(process_content_task, job_id, context)
        
        return {"job_id": job_id, "status": "processing_started"}
        
    except Exception as e:
        logger.error(f"Process request error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{job_id}")
async def check_progress(job_id: str):
    """Check the progress of a processing job"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = processing_jobs[job_id]
    
    # Clean up old jobs (production would use a better solution)
    current_time = time.time()
    for jid in list(processing_jobs.keys()):
        if current_time - processing_jobs[jid]["created"] > 3600:  # 1 hour
            if processing_jobs[jid]["status"] != "processing":
                del processing_jobs[jid]
    
    # Return job status
    response = {
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"]
    }
    
    # Include results if completed
    if job["status"] == "completed" and job["results"]:
        response["results"] = job["results"]
    
    # Include error if failed
    if job["status"] == "failed" and job["error"]:
        response["error"] = job["error"]
        
    return response

@app.get("/api/health")
def health_check():
    """Check service health"""
    azure_doc_available = AzureDocumentProcessor.is_available()
    azure_lang_available = azure_language_processor.is_available()
    gemini_available = gemini_generator.available
    
    services = {
        "azure_document_intelligence": azure_doc_available,
        "azure_language_services": azure_lang_available,
        "gemini_ai": gemini_available
    }
    
    status = "healthy" if (azure_doc_available or gemini_available) else "degraded"
    
    return {
        "status": status,
        "services": services,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)