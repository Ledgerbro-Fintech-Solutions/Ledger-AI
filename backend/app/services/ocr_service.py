import json
import re
from typing import Dict, Any, List
from PIL import Image
import pandas as pd
from langchain_groq import ChatGroq

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.rag_pipeline import clean_llm_json_text, extract_json_object_or_array
from backend.app.utils.image_processing import encode_image_pil


class OCRService:
    """Service for OCR and structured financial data extraction using Groq LLMs."""

    def __init__(self):
        self.extraction_llm = None
        self.standardization_llm = None

    def _get_extraction_llm(self) -> ChatGroq:
        if self.extraction_llm is None:
            self.extraction_llm = ChatGroq(
                groq_api_key=settings.groq_api_key,
                model_name=settings.groq_model_extraction,
                temperature=settings.llm_temperature
            )
        return self.extraction_llm

    def _get_standardization_llm(self) -> ChatGroq:
        if self.standardization_llm is None:
            self.standardization_llm = ChatGroq(
                groq_api_key=settings.groq_api_key,
                model_name=settings.groq_model_standardization,
                temperature=settings.llm_temperature
            )
        return self.standardization_llm

    def extract_structured_data(self, image_obj: Image.Image) -> Dict[str, Any]:
        """
        Extract structured invoice header and line items using Groq vision model.
        """
        extraction_prompt = """
You are an expert invoice processing and OCR AI. Carefully examine this invoice image and extract all structured data.

CRITICAL INSTRUCTIONS:
- You MUST respond with ONLY a valid JSON object. Do not include introductory text, markdown explanations, or reasoning.
- Extract invoice header information and all tabular line items.
- If a value is missing or unreadable, set it to null.
- Extract numeric amounts as numbers (e.g. 1250.50, not "$1,250.50").
- Detect the currency symbol or code (e.g. $, €, £, USD, EUR, etc.).

Required JSON Schema:
{
  "invoice_details": {
    "invoice_number": "string or null",
    "vendor_name": "string or null",
    "vendor_address": "string or null",
    "invoice_date": "string or null",
    "due_date": "string or null",
    "total_amount": 0.00,
    "tax_amount": 0.00,
    "subtotal": 0.00,
    "currency": "$"
  },
  "line_items": [
    {
      "description": "item description",
      "quantity": 1.0,
      "unit_price": 10.00,
      "total_price": 10.00,
      "item_code": "SKU or null"
    }
  ]
}
"""
        image_data_url = f"data:image/jpeg;base64,{encode_image_pil(image_obj)}"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": extraction_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ]

        for attempt in range(settings.max_retries):
            try:
                logger.info(f"Extracting invoice data (attempt {attempt + 1}/{settings.max_retries})...")
                llm = self._get_extraction_llm()
                response = llm.invoke(messages)
                content = response.content.strip() if hasattr(response, 'content') else str(response)

                parsed_json = extract_json_object_or_array(content)
                if not isinstance(parsed_json, dict):
                    raise ValueError(f"Extracted response did not contain a valid JSON object: {content[:100]}")

                if "invoice_details" not in parsed_json:
                    parsed_json["invoice_details"] = {}
                if "line_items" not in parsed_json or not isinstance(parsed_json["line_items"], list):
                    parsed_json["line_items"] = []

                logger.info(f"Successfully extracted data with {len(parsed_json['line_items'])} line items.")
                return parsed_json

            except Exception as e:
                logger.warning(f"Extraction attempt {attempt + 1} failed: {e}")
                if attempt == settings.max_retries - 1:
                    logger.error(f"All {settings.max_retries} attempts failed: {e}")
                    # Return safe empty structure rather than crash
                    return {
                        "invoice_details": {
                            "invoice_number": None,
                            "vendor_name": None,
                            "vendor_address": None,
                            "invoice_date": None,
                            "due_date": None,
                            "total_amount": 0.0,
                            "tax_amount": 0.0,
                            "subtotal": 0.0,
                            "currency": "$"
                        },
                        "line_items": []
                    }

    def standardize_columns(self, dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
        """Standardize column names across multiple DataFrames using LLM."""
        if not dfs:
            return []

        all_cols = set()
        for df in dfs:
            all_cols.update(df.columns.tolist())

        prompt = f"""
Standardize these extracted invoice column names to standard snake_case keys:
Original columns found: {list(all_cols)}

Target standard schema:
- 'description': Item or product description
- 'quantity': Quantity of items
- 'unit_price': Unit rate/price
- 'total_price': Total line price
- 'item_code': Item code / SKU / part number
- 'source_file': Source filename
- 'page_no': Page number
- 'invoice_number': Invoice identifier
- 'address': Vendor address
- 'date': Invoice date
- 'due_date': Due date
- 'company_name': Vendor name
- 'currency': Currency symbol

Respond ONLY with a JSON mapping dictionary:
{{"original_column": "standard_column"}}
"""
        try:
            llm = self._get_standardization_llm()
            res = llm.invoke(prompt)
            content = res.content.strip() if hasattr(res, 'content') else str(res)
            mapping = extract_json_object_or_array(content)
            if isinstance(mapping, dict):
                return [df.rename(columns=mapping) for df in dfs]
        except Exception as e:
            logger.warning(f"LLM standardization failed ({e}), using rule-based fallback.")

        return self.simple_column_standardization(dfs)

    def simple_column_standardization(self, dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
        """Rule-based column standardization fallback."""
        rules = {
            'item': 'description',
            'desc': 'description',
            'product': 'description',
            'qty': 'quantity',
            'count': 'quantity',
            'rate': 'unit_price',
            'price': 'unit_price',
            'amount': 'total_price',
            'total': 'total_price',
            'subtotal': 'total_price',
            'code': 'item_code',
            'sku': 'item_code',
            'vendor': 'company_name',
            'supplier': 'company_name',
            'invoice_no': 'invoice_number',
            'inv_num': 'invoice_number',
            'inv_date': 'date'
        }
        res = []
        for df in dfs:
            col_map = {}
            for col in df.columns:
                lower = str(col).lower().replace(" ", "_")
                for k, v in rules.items():
                    if k in lower:
                        col_map[col] = v
                        break
            res.append(df.rename(columns=col_map))
        return res

ocr_service = OCRService()
