import json
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from backend.app.models.schemas import UploadResponse, JSONUploadRequest
from backend.app.core.rag_pipeline import InvoiceRAGPipeline
from backend.app.core.session_manager import session_manager
from backend.app.core.config import settings
from backend.app.core.logging import logger

router = APIRouter(tags=["Chatbot Upload"])

_pipeline_instance = None

def get_rag_pipeline() -> InvoiceRAGPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = InvoiceRAGPipeline(groq_api_key=settings.groq_api_key)
    return _pipeline_instance


@router.post("/upload/files", response_model=UploadResponse, summary="Upload CSV/JSON files for AI analysis")
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided.")

    processed = []
    for f in files:
        fname = f.filename or "uploaded_file"
        lower = fname.lower()
        if not (lower.endswith(".json") or lower.endswith(".csv")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{fname}'. Only CSV and JSON are supported for chat analysis."
            )

        content = await f.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{fname}' exceeds {settings.max_file_size // (1024*1024)}MB."
            )
        processed.append((fname, content))

    try:
        pipeline = get_rag_pipeline()
        docs = pipeline.load_documents_from_files(processed)
        if not docs:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid documents extracted.")

        vector_store = pipeline.create_vector_store(docs)
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})
        agent = pipeline.create_agent(retriever)

        session_id = session_manager.create_session(vector_store, agent, files_processed=len(processed))
        return UploadResponse(
            session_id=session_id,
            message="Files processed and indexed into AI assistant session.",
            files_processed=len(processed)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during file indexing: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/upload/json", response_model=UploadResponse, summary="Ingest structured JSON into AI assistant")
async def upload_json(request: JSONUploadRequest):
    try:
        json_bytes = json.dumps(request.data, indent=2).encode('utf-8')
        processed = [(request.filename, json_bytes)]

        pipeline = get_rag_pipeline()
        docs = pipeline.load_documents_from_files(processed)
        if not docs:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid invoice content extracted.")

        vector_store = pipeline.create_vector_store(docs)
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})
        agent = pipeline.create_agent(retriever)

        session_id = session_manager.create_session(vector_store, agent, files_processed=1)
        return UploadResponse(
            session_id=session_id,
            message="JSON data indexed successfully.",
            files_processed=1
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing JSON data: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
