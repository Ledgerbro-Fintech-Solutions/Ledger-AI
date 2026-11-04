import io
from typing import List
import pandas as pd
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse

from backend.app.models.schemas import ErrorResponse
from backend.app.services.ocr_service import ocr_service
from backend.app.utils.image_processing import pdf_to_images, bytes_to_image, is_pdf_file
from backend.app.utils.data_processing import (
    merge_dataframes_intelligently, clean_dataframe, reorder_and_rename_columns
)
from backend.app.utils.file_validation import validate_uploaded_files, get_file_content_type, read_file_bytes
from backend.app.core.logging import logger

router = APIRouter(tags=["Invoice Processing"])


@router.post(
    "/process-invoices",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "Standardized CSV file containing merged line items."
        },
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Process invoices and download standardized CSV"
)
async def process_invoices(files: List[UploadFile] = File(..., description="PDF or image invoices to merge into CSV")):
    validate_uploaded_files(files)

    all_dfs = []
    errors = []
    files_processed = 0

    for upload_file in files:
        fname = upload_file.filename or "unknown_file"
        try:
            fbytes = await read_file_bytes(upload_file)
            ctype = get_file_content_type(upload_file, fbytes)

            images = pdf_to_images(fbytes) if is_pdf_file(ctype, fname) else [bytes_to_image(fbytes)]

            for page_idx, img in enumerate(images):
                try:
                    data = ocr_service.extract_structured_data(img)
                    line_items = data.get("line_items", [])
                    details = data.get("invoice_details", {}) or {}

                    if line_items:
                        df = pd.DataFrame(line_items)
                    else:
                        # Create at least one row summarizing invoice if no table found
                        df = pd.DataFrame([{
                            "description": f"Invoice {details.get('invoice_number', 'Total')}",
                            "quantity": 1,
                            "unit_price": details.get("total_amount", 0.0),
                            "total_price": details.get("total_amount", 0.0)
                        }])

                    df['source_file'] = fname
                    df['page_no'] = page_idx + 1
                    df['invoice_number'] = details.get('invoice_number')
                    df['address'] = details.get('vendor_address')
                    df['date'] = details.get('invoice_date')
                    df['due_date'] = details.get('due_date')
                    df['company_name'] = details.get('vendor_name')
                    df['currency'] = details.get('currency', '$')

                    cleaned_df = clean_dataframe(df)
                    if not cleaned_df.empty:
                        all_dfs.append(cleaned_df)
                except Exception as ex:
                    errors.append(f"Page {page_idx + 1} of {fname}: {ex}")

            files_processed += 1
        except Exception as e:
            errors.append(f"{fname}: {e}")

    if not all_dfs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not extract tabular line items from provided documents: {'; '.join(errors)}"
        )

    # Standardize columns
    standardized_dfs = ocr_service.standardize_columns(all_dfs)

    # Merge into unified table
    final_df = merge_dataframes_intelligently(standardized_dfs)
    if final_df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid data remained after column normalization."
        )

    final_df = reorder_and_rename_columns(final_df)

    csv_buffer = io.StringIO()
    final_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    logger.info(f"Generated CSV with {len(final_df)} rows from {files_processed} files.")
    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=processed_invoices.csv"}
    )
