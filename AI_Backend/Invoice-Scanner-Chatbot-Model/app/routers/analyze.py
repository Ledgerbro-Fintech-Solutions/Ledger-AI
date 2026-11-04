from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
import pandas as pd

from app.models.schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.core.session_manager import session_manager
from app.core.rag_pipeline import InvoiceRAGPipeline

router = APIRouter(prefix="/analyze", tags=["analyze"])

@router.post("", response_model=AnalyzeResponse)
async def analyze_invoices(request: AnalyzeRequest):
    """
    Chat with uploaded data using session ID
    """
    session_data = session_manager.get_session(request.session_id)
    if session_data is None:
        raise HTTPException(
            status_code=404, 
            detail="Session not found or expired"
        )
    
    try:
        result = session_data.agent.invoke({"question": request.question})
        
        answer = result.get("answer", '''
                                            
            Whoops, my search came up empty! 😅

To point me in the right direction, try asking with a bit more detail. Also, remember, I can only look for clues inside the data you've given me.

Ready to ask again?
                                            
                            ''')
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
        raise HTTPException(
            status_code=500, 
            detail=f"Error during analysis: {str(e)}"
        )