import io
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Query, Request
from fastapi.responses import StreamingResponse

from backend.app.models.schemas import (
    OCRDataResponse, ErrorResponse, PhotoToCSVResponse,
    DocumentData, InvoiceDetails, LineItem, RawTextContent, DocumentMetadata
)
from backend.app.services.ocr_service import ocr_service
from backend.app.utils.image_processing import pdf_to_images, bytes_to_image, is_pdf_file
from backend.app.utils.file_validation import validate_uploaded_files, get_file_content_type, read_file_bytes
from backend.app.utils.data_processing import clean_dataframe, reorder_and_rename_columns
from backend.app.core.logging import logger

router = APIRouter(tags=["OCR Extraction"])


def _create_document_data(
    filename: str,
    page_idx: int,
    total_pages: int,
    file_type: str,
    extracted_data: Dict[str, Any]
) -> DocumentData:
    details_raw = extracted_data.get('invoice_details', {}) or {}
    line_items_raw = extracted_data.get('line_items', []) or []

    invoice_details = InvoiceDetails(
        invoice_number=details_raw.get('invoice_number'),
        vendor_name=details_raw.get('vendor_name'),
        vendor_address=details_raw.get('vendor_address'),
        invoice_date=details_raw.get('invoice_date'),
        due_date=details_raw.get('due_date'),
        total_amount=details_raw.get('total_amount'),
        tax_amount=details_raw.get('tax_amount'),
        subtotal=details_raw.get('subtotal'),
        currency=details_raw.get('currency')
    )

    line_items = [
        LineItem(
            description=item.get('description'),
            quantity=item.get('quantity'),
            unit_price=item.get('unit_price'),
            total_price=item.get('total_price'),
            item_code=item.get('item_code')
        ) for item in line_items_raw
    ]

    curr = invoice_details.currency or "$"
    tot = invoice_details.total_amount or 0.0
    invoice_summary = (
        f"Invoice {invoice_details.invoice_number or 'N/A'} from {invoice_details.vendor_name or 'Unknown'} "
        f"issued on {invoice_details.invoice_date or 'N/A'}. Total: {curr}{tot:,.2f}."
    )

    items_summaries = [
        f"{it.description or 'Item'}: Qty {it.quantity or 1} @ {curr}{it.unit_price or 0.0} = {curr}{it.total_price or 0.0}"
        for it in line_items
    ]
    line_items_summary = "; ".join(items_summaries) if items_summaries else "No line items detected."

    raw_text_content = RawTextContent(
        invoice_summary=invoice_summary,
        line_items_summary=line_items_summary
    )

    metadata = DocumentMetadata(
        has_line_items=len(line_items) > 0,
        line_items_count=len(line_items),
        has_invoice_details=bool(invoice_details.invoice_number or invoice_details.vendor_name),
        extracted_fields=[k for k, v in details_raw.items() if v is not None],
        processing_status="success"
    )

    return DocumentData(
        document_id=f"doc_{uuid.uuid4().hex[:12]}",
        source_file=filename,
        page_number=page_idx + 1,
        total_pages=total_pages,
        file_type=file_type,
        extraction_timestamp=datetime.now(timezone.utc).isoformat(),
        invoice_details=invoice_details,
        line_items=line_items,
        raw_text_content=raw_text_content,
        metadata=metadata
    )


@router.post(
    "/extract-ocr-data",
    response_model=OCRDataResponse,
    summary="Extract structured invoice data from PDFs/images"
)
@router.post(
    "/extract-data",
    response_model=OCRDataResponse,
    summary="Extract structured invoice data from PDFs/images (alias)"
)
async def extract_ocr_data(files: List[UploadFile] = File(..., description="Upload PDF or image invoices")):
    validate_uploaded_files(files)

    all_docs: List[DocumentData] = []
    errors: List[str] = []
    files_processed = 0
    pages_processed = 0

    for upload_file in files:
        fname = upload_file.filename or "unknown_file"
        try:
            fbytes = await read_file_bytes(upload_file)
            ctype = get_file_content_type(upload_file, fbytes)

            if is_pdf_file(ctype, fname):
                images = pdf_to_images(fbytes)
            else:
                images = [bytes_to_image(fbytes)]

            for idx, img in enumerate(images):
                extracted = ocr_service.extract_structured_data(img)
                doc_data = _create_document_data(
                    filename=fname,
                    page_idx=idx,
                    total_pages=len(images),
                    file_type=ctype,
                    extracted_data=extracted
                )
                all_docs.append(doc_data)
                pages_processed += 1

            files_processed += 1
        except Exception as e:
            err = f"Failed processing {fname}: {str(e)}"
            logger.error(err)
            errors.append(err)

    if not all_docs and errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract invoice data: {'; '.join(errors)}"
        )

    return OCRDataResponse(
        success=len(all_docs) > 0,
        message=f"Processed {files_processed} files ({pages_processed} pages).",
        data=all_docs,
        total_files_processed=files_processed,
        total_pages_processed=pages_processed,
        processing_errors=errors or None,
        total_errors=len(errors) if errors else None
    )


@router.post(
    "/photo-to-csv",
    response_model=PhotoToCSVResponse,
    summary="Upload invoice photo and extract tabular data as CSV"
)
@router.post(
    "/image-to-csv",
    response_model=PhotoToCSVResponse,
    summary="Upload invoice image and extract tabular data as CSV (alias)"
)
async def photo_to_csv(
    file: UploadFile = File(..., description="Invoice photo or scan (PNG, JPG, PDF, WebP)"),
    format: Optional[str] = Query(None, description="Output format: 'json' (default) or 'csv'"),
    request: Request = None
):
    """
    Process an uploaded invoice photo or document, extract its tabular line items,
    and return both interactive structured table data and formatted CSV content.
    """
    validate_uploaded_files([file])
    fname = file.filename or "invoice_photo.png"
    fbytes = await read_file_bytes(file)
    ctype = get_file_content_type(file, fbytes)

    images = pdf_to_images(fbytes) if is_pdf_file(ctype, fname) else [bytes_to_image(fbytes)]

    all_line_items = []
    invoice_header = {}

    for page_idx, img in enumerate(images):
        extracted = ocr_service.extract_structured_data(img)
        details = extracted.get("invoice_details", {}) or {}
        if not invoice_header:
            invoice_header = details

        items = extracted.get("line_items", []) or []
        for it in items:
            row_dict = {
                "source_file": fname,
                "company_name": details.get("vendor_name") or invoice_header.get("vendor_name"),
                "invoice_number": details.get("invoice_number") or invoice_header.get("invoice_number"),
                "date": details.get("invoice_date") or invoice_header.get("invoice_date"),
                "due_date": details.get("due_date") or invoice_header.get("due_date"),
                "description": it.get("description"),
                "item_code": it.get("item_code"),
                "quantity": it.get("quantity"),
                "unit_price": it.get("unit_price"),
                "total_price": it.get("total_price"),
                "address": details.get("vendor_address") or invoice_header.get("vendor_address"),
                "page_no": page_idx + 1,
                "currency": details.get("currency") or invoice_header.get("currency") or "$"
            }
            all_line_items.append(row_dict)

    curr = invoice_header.get("currency") or "$"
    tot_amt = invoice_header.get("total_amount")

    if not all_line_items:
        all_line_items.append({
            "source_file": fname,
            "company_name": invoice_header.get("vendor_name"),
            "invoice_number": invoice_header.get("invoice_number"),
            "date": invoice_header.get("invoice_date"),
            "due_date": invoice_header.get("due_date"),
            "description": f"Invoice {invoice_header.get('invoice_number', 'Summary')}",
            "item_code": None,
            "quantity": 1.0,
            "unit_price": tot_amt or 0.0,
            "total_price": tot_amt or 0.0,
            "address": invoice_header.get("vendor_address"),
            "page_no": 1,
            "currency": curr
        })

    df = pd.DataFrame(all_line_items)
    df = clean_dataframe(df)
    df = reorder_and_rename_columns(df)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_text = csv_buffer.getvalue()

    accept_header = request.headers.get("accept", "") if request else ""
    if format == "csv" or "text/csv" in accept_header:
        base_name = os.path.splitext(fname)[0]
        safe_name = f"{base_name}_extracted.csv"
        return StreamingResponse(
            iter([csv_text]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}"'}
        )

    columns = list(df.columns)
    rows = df.to_dict(orient="records")

    inv_details = InvoiceDetails(
        invoice_number=invoice_header.get("invoice_number"),
        vendor_name=invoice_header.get("vendor_name"),
        vendor_address=invoice_header.get("vendor_address"),
        invoice_date=invoice_header.get("invoice_date"),
        due_date=invoice_header.get("due_date"),
        total_amount=invoice_header.get("total_amount"),
        tax_amount=invoice_header.get("tax_amount"),
        subtotal=invoice_header.get("subtotal"),
        currency=curr
    )

    return PhotoToCSVResponse(
        success=True,
        filename=fname,
        invoice_details=inv_details,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        csv_data=csv_text,
        total_amount=tot_amt,
        currency=curr
    )

