from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# ----------------- OCR & Invoice Schemas ----------------- #

class InvoiceDetails(BaseModel):
    """Extracted invoice header details."""
    invoice_number: Optional[str] = Field(None, description="Invoice identifier")
    vendor_name: Optional[str] = Field(None, description="Vendor or company name")
    vendor_address: Optional[str] = Field(None, description="Vendor physical/mailing address")
    invoice_date: Optional[str] = Field(None, description="Date invoice was issued")
    due_date: Optional[str] = Field(None, description="Invoice payment due date")
    total_amount: Optional[float] = Field(None, description="Total billed amount")
    tax_amount: Optional[float] = Field(None, description="Tax amount")
    subtotal: Optional[float] = Field(None, description="Subtotal amount before tax")
    currency: Optional[str] = Field(None, description="Detected currency symbol or code")


class LineItem(BaseModel):
    """Extracted invoice item row."""
    description: Optional[str] = Field(None, description="Item or service description")
    quantity: Optional[float] = Field(None, description="Billed quantity")
    unit_price: Optional[float] = Field(None, description="Individual unit price")
    total_price: Optional[float] = Field(None, description="Total line price")
    item_code: Optional[str] = Field(None, description="SKU or product code")


class RawTextContent(BaseModel):
    """Human-readable text summaries for RAG embedding."""
    invoice_summary: str = Field(..., description="High-level invoice summary")
    line_items_summary: str = Field(..., description="Summary of parsed line items")


class DocumentMetadata(BaseModel):
    """Metadata regarding processing outcomes and confidence."""
    has_line_items: bool = Field(..., description="Whether line items were detected")
    line_items_count: int = Field(..., description="Number of detected line items")
    has_invoice_details: bool = Field(..., description="Whether header details were extracted")
    extracted_fields: List[str] = Field(default_factory=list, description="Extracted keys")
    processing_status: str = Field(..., description="Processing status (success/error)")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class DocumentData(BaseModel):
    """Single page / document extraction object."""
    document_id: str = Field(..., description="Unique generated document ID")
    source_file: str = Field(..., description="Original filename")
    page_number: int = Field(..., description="Page number")
    total_pages: int = Field(..., description="Total pages in document")
    file_type: str = Field(..., description="File MIME type")
    extraction_timestamp: str = Field(..., description="Timestamp of extraction")
    invoice_details: InvoiceDetails = Field(..., description="Header details")
    line_items: List[LineItem] = Field(default_factory=list, description="List of line items")
    raw_text_content: RawTextContent = Field(..., description="Text summaries")
    metadata: DocumentMetadata = Field(..., description="Processing metadata")


class OCRDataResponse(BaseModel):
    """Response returned by OCR extraction endpoint."""
    success: bool = Field(..., description="Overall extraction outcome")
    message: str = Field(..., description="Descriptive status message")
    data: List[DocumentData] = Field(default_factory=list, description="Extracted documents list")
    total_files_processed: int = Field(..., description="Number of processed files")
    total_pages_processed: int = Field(..., description="Number of processed pages")
    processing_errors: Optional[List[str]] = Field(None, description="Encountered errors")
    total_errors: Optional[int] = Field(None, description="Error count")


class PhotoToCSVResponse(BaseModel):
    """Response returned by photo-to-csv extraction endpoint."""
    success: bool = Field(..., description="Extraction success status")
    filename: str = Field(..., description="Name of the processed image file")
    invoice_details: InvoiceDetails = Field(..., description="Extracted invoice header metadata")
    columns: List[str] = Field(..., description="Ordered column names for the table")
    rows: List[Dict[str, Any]] = Field(..., description="Extracted table rows")
    row_count: int = Field(..., description="Total extracted row count")
    csv_data: str = Field(..., description="Full CSV text string")
    total_amount: Optional[float] = Field(None, description="Total invoice amount")
    currency: Optional[str] = Field("$", description="Detected currency symbol")


# ----------------- Chatbot & RAG Schemas ----------------- #

class UploadResponse(BaseModel):
    """Response returned upon uploading documents to RAG chat."""
    session_id: str = Field(..., description="Active session UUID")
    message: str = Field(..., description="Status message")
    files_processed: int = Field(..., description="Number of ingested files")


class JSONUploadRequest(BaseModel):
    """Payload to initiate chat directly from structured JSON."""
    filename: str = Field(default="invoice_data.json", description="Filename label")
    data: Any = Field(..., description="Invoice JSON object or array")


class AnalyzeRequest(BaseModel):
    """Chat question payload."""
    session_id: str = Field(..., description="Session ID from upload")
    question: str = Field(..., description="Natural language question")


class AnalyzeResponse(BaseModel):
    """Structured response from LangGraph assistant."""
    answer: str = Field(..., description="Natural language response")
    table: Optional[List[Dict[str, Any]]] = Field(None, description="Structured table rows if applicable")
    graph: Optional[str] = Field(None, description="Base64 encoded PNG chart if applicable")
    session_id: str = Field(..., description="Current session ID")


# ----------------- Shared Responses ----------------- #

class HealthCheckResponse(BaseModel):
    """API healthcheck status response."""
    status: str = Field(..., description="Health status (e.g. healthy)")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    version: str = Field(..., description="Application version")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependent service status")


class ErrorResponse(BaseModel):
    """Standardized error response."""
    detail: str = Field(..., description="Error message details")
    error_code: Optional[str] = Field(None, description="Internal error code")
    timestamp: Optional[str] = Field(None, description="Error timestamp")
