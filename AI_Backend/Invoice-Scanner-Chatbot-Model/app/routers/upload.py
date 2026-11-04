from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import json
from dotenv import load_dotenv
load_dotenv()

from app.models.schemas import UploadResponse, ErrorResponse, JSONUploadRequest
from app.core.rag_pipeline import InvoiceRAGPipeline
from app.core.session_manager import session_manager
from app.core.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])

def get_rag_pipeline() -> InvoiceRAGPipeline:
    return InvoiceRAGPipeline(groq_api_key=os.getenv("GROQ_API_KEY"))

@router.post("/files", response_model=UploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    rag_pipeline: InvoiceRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Upload CSV/JSON files and create a session for chatting
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    processed_files = []
    for file in files:
        if not any(file.filename.lower().endswith(f".{ext}") for ext in settings.allowed_file_types):
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} has unsupported format. Allowed: {settings.allowed_file_types}"
            )
        
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds maximum size"
            )
        
        processed_files.append((file.filename, content))
    
    try:
        documents = rag_pipeline.load_documents_from_files(processed_files)
        if not documents:
            raise HTTPException(status_code=400, detail="No valid documents extracted")
        
        vector_store = rag_pipeline.create_vector_store(documents)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        agent = rag_pipeline.create_agent(retriever)
        
        session_id = session_manager.create_session(vector_store, agent)
        
        return UploadResponse(
            session_id=session_id,
            message="Files uploaded successfully",
            files_processed=len(processed_files)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/json", response_model=UploadResponse)
async def upload_json(
    request: JSONUploadRequest,
    rag_pipeline: InvoiceRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Upload JSON data and create a session for chatting
    """
    try:
        json_str = json.dumps(request.data, indent=2)
        processed_files = [(request.filename, json_str.encode('utf-8'))]
        
        documents = rag_pipeline.load_documents_from_files(processed_files)
        if not documents:
            raise HTTPException(status_code=400, detail="No valid documents extracted")
        
        vector_store = rag_pipeline.create_vector_store(documents)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        agent = rag_pipeline.create_agent(retriever)
        
        session_id = session_manager.create_session(vector_store, agent)
        
        return UploadResponse(
            session_id=session_id,
            message="JSON data uploaded successfully",
            files_processed=1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")