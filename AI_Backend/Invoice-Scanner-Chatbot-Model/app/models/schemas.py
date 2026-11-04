from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response model for file upload endpoint"""
    session_id: str = Field(..., description="Unique session identifier for the uploaded documents")
    message: str = Field(..., description="Status message")
    files_processed: int = Field(..., description="Number of files successfully processed")


class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint"""
    session_id: str = Field(..., description="Session identifier from upload response")
    question: str = Field(..., description="Natural language question about the invoices")


class AnalyzeResponse(BaseModel):
    """Response model for analyze endpoint"""
    answer: str = Field(..., description="Text response to the question")
    table: Optional[List[Dict[str, Any]]] = Field(None, description="Table data as list of dictionaries")
    graph: Optional[str] = Field(None, description="Base64-encoded graph image")
    session_id: str = Field(..., description="Session identifier")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")


class JSONUploadRequest(BaseModel):
    """Request model for direct JSON data upload"""
    data: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(..., description="JSON data (object or array of objects)")
    filename: Optional[str] = Field("invoice_data.json", description="Optional filename for the data")


class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint"""
    session_id: str = Field(..., description="Session identifier from upload response")
    question: str = Field(..., description="Natural language question about the invoices")
