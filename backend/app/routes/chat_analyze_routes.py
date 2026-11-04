from typing import Dict, Any, Optional, List
import pandas as pd
from fastapi import APIRouter, HTTPException, status

from backend.app.models.schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from backend.app.core.session_manager import session_manager
from backend.app.core.rag_pipeline import InvoiceRAGPipeline
from backend.app.core.logging import logger

router = APIRouter(tags=["Chatbot Analysis"])


@router.post("/analyze", response_model=AnalyzeResponse, summary="Chat with parsed invoices using natural language")
async def analyze_invoices(request: AnalyzeRequest):
    session_data = session_manager.get_session(request.session_id)
    if session_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or has expired. Please upload an invoice or document to start a new chat session."
        )

    try:
        logger.info(f"Invoking analysis on session {request.session_id}: '{request.question}'")
        result = session_data.agent.invoke({"question": request.question})

        answer = result.get("answer") or "I examined the provided documents, but couldn't find a direct answer. Please provide additional details or verify your uploaded data."
        table_df = result.get("table")
        graph_fig = result.get("graph_fig")

        table_data: Optional[List[Dict[str, Any]]] = None
        if table_df is not None and isinstance(table_df, pd.DataFrame):
            table_data = table_df.to_dict('records')

        graph_base64: Optional[str] = None
        if graph_fig is not None:
            graph_base64 = InvoiceRAGPipeline.matplotlib_to_base64(graph_fig)

        return AnalyzeResponse(
            answer=answer,
            table=table_data,
            graph=graph_base64,
            session_id=request.session_id
        )

    except Exception as e:
        logger.error(f"Error during invoice chat analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
