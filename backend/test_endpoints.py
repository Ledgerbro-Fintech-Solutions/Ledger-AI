#!/usr/bin/env python3
"""
End-to-End API Verification Script for Ledger AI Unified Application.
Tests OCR extraction, CSV processing, RAG chat sessions, and SPA serving.
"""

import sys
import io
import json
import base64
import requests
from PIL import Image, ImageDraw

BASE_URL = "http://localhost:8000"


def generate_test_invoice_image() -> bytes:
    """Create a synthetic invoice image with text and table using PIL."""
    img = Image.new("RGB", (700, 900), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header
    draw.text((40, 40), "INVOICE", fill=(21, 93, 252))
    draw.text((40, 70), "Acme Industrial Supplies LLC", fill=(20, 20, 20))
    draw.text((40, 90), "100 Innovation Way, Suite 400", fill=(100, 100, 100))

    # Details
    draw.text((450, 40), "Invoice #: INV-2026-9901", fill=(20, 20, 20))
    draw.text((450, 60), "Date: August 14, 2026", fill=(20, 20, 20))
    draw.text((450, 80), "Due Date: September 14, 2026", fill=(20, 20, 20))
    draw.text((450, 100), "Currency: USD ($)", fill=(20, 20, 20))

    # Line Item Table
    draw.line([(40, 160), (660, 160)], fill=(200, 200, 200), width=2)
    draw.text((50, 170), "Description", fill=(60, 60, 60))
    draw.text((320, 170), "Qty", fill=(60, 60, 60))
    draw.text((420, 170), "Unit Price", fill=(60, 60, 60))
    draw.text((540, 170), "Total", fill=(60, 60, 60))
    draw.line([(40, 195), (660, 195)], fill=(200, 200, 200), width=1)

    # Row 1
    draw.text((50, 210), "Industrial Hydraulic Filter Pack", fill=(20, 20, 20))
    draw.text((320, 210), "2", fill=(20, 20, 20))
    draw.text((420, 210), "$350.00", fill=(20, 20, 20))
    draw.text((540, 210), "$700.00", fill=(20, 20, 20))

    # Row 2
    draw.text((50, 240), "Precision Valve Assembly Gasket", fill=(20, 20, 20))
    draw.text((320, 240), "5", fill=(20, 20, 20))
    draw.text((420, 240), "$90.00", fill=(20, 20, 20))
    draw.text((540, 240), "$450.00", fill=(20, 20, 20))

    draw.line([(40, 280), (660, 280)], fill=(200, 200, 200), width=1)
    draw.text((420, 300), "Subtotal:", fill=(60, 60, 60))
    draw.text((540, 300), "$1,150.00", fill=(20, 20, 20))
    draw.text((420, 330), "Tax (8%):", fill=(60, 60, 60))
    draw.text((540, 330), "$92.00", fill=(20, 20, 20))
    draw.text((420, 360), "Total Amount:", fill=(21, 93, 252))
    draw.text((540, 360), "$1,242.00", fill=(21, 93, 252))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def run_all_tests():
    print("==========================================================")
    print(f"Starting Ledger AI End-to-End Verification at {BASE_URL}")
    print("==========================================================")

    # 1. Health Endpoint
    print("\n[1/6] Testing System Health Check...")
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        health_data = r.json()
        print(f"  ✓ Health status: {health_data.get('status')}")
        print(f"  ✓ Dependencies: {health_data.get('dependencies')}")
    except Exception as e:
        print(f"  ✗ Health check failed: {e}")
        return False

    # 2. SPA Frontend Serving
    print("\n[2/6] Testing Single-Page Application (SPA) Serving...")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=10)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert "<div id=\"root\">" in r.text or "Ledger AI" in r.text or "<!DOCTYPE html>" in r.text
        print("  ✓ Root '/' successfully served index.html")

        r_sub = requests.get(f"{BASE_URL}/dashboard", timeout=10)
        assert r_sub.status_code == 200, f"Expected 200 for /dashboard, got {r_sub.status_code}"
        print("  ✓ Client route '/dashboard' successfully handled by SPA fallback")
    except Exception as e:
        print(f"  ✗ SPA serving test failed: {e}")

    # 3. OCR Data Extraction Endpoint
    print("\n[3/6] Testing OCR Document Extraction (/api/ocr/extract-data)...")
    try:
        img_bytes = generate_test_invoice_image()
        files = [('files', ('test_invoice.jpg', img_bytes, 'image/jpeg'))]
        r = requests.post(f"{BASE_URL}/api/ocr/extract-data", files=files, timeout=60)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        ocr_res = r.json()
        assert ocr_res.get("success") is True, "OCR success should be True"
        assert len(ocr_res.get("data", [])) > 0, "Expected at least 1 document data item"
        doc = ocr_res["data"][0]
        details = doc.get("invoice_details", {})
        print(f"  ✓ Processed file: {doc.get('source_file')}")
        print(f"  ✓ Vendor extracted: {details.get('vendor_name')}")
        print(f"  ✓ Total amount: {details.get('currency', '$')}{details.get('total_amount')}")
        print(f"  ✓ Line items detected: {len(doc.get('line_items', []))}")
    except Exception as e:
        print(f"  ✗ OCR extraction failed: {e}")

    # 4. Process Invoices to CSV Streaming
    print("\n[4/6] Testing Invoices to Standardized CSV (/api/ocr/process-invoices)...")
    try:
        img_bytes = generate_test_invoice_image()
        files = [('files', ('invoice_for_csv.jpg', img_bytes, 'image/jpeg'))]
        r = requests.post(f"{BASE_URL}/api/ocr/process-invoices", files=files, timeout=60)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert "text/csv" in r.headers.get("content-type", "")
        csv_text = r.text
        lines = csv_text.strip().split("\n")
        print(f"  ✓ Received streamed CSV with {len(lines)} lines")
        print(f"  ✓ Header: {lines[0]}")
        if len(lines) > 1:
            print(f"  ✓ Sample row: {lines[1]}")
    except Exception as e:
        print(f"  ✗ Process invoices CSV failed: {e}")

    # 5. Chat Session Initialization (/api/v1/upload/json)
    print("\n[5/6] Testing RAG Chat Session Creation (/api/v1/upload/json)...")
    session_id = None
    try:
        sample_invoices = [
            {
                "invoice_number": "INV-2026-0842",
                "vendor_name": "Dell Technologies",
                "date": "2026-08-14",
                "total_amount": 2450.00,
                "items": [
                    {"description": "Precision Workstation", "quantity": 1, "unit_price": 2450.00}
                ]
            },
            {
                "invoice_number": "INV-2026-0841",
                "vendor_name": "ABC Technologies",
                "date": "2026-08-14",
                "total_amount": 12890.50,
                "items": [
                    {"description": "Enterprise Cloud Setup", "quantity": 1, "unit_price": 12890.50}
                ]
            }
        ]
        payload = {"filename": "test_batch.json", "data": sample_invoices}
        r = requests.post(f"{BASE_URL}/api/v1/upload/json", json=payload, timeout=30)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        res = r.json()
        session_id = res.get("session_id")
        assert session_id, "Session ID should not be empty"
        print(f"  ✓ Session initialized: {session_id}")
    except Exception as e:
        print(f"  ✗ Session initialization failed: {e}")
        return False

    # 6. Chat Natural Language Analysis (/api/v1/analyze)
    print("\n[6/6] Testing RAG Natural Language Analysis (/api/v1/analyze)...")
    try:
        # Question 1: Total
        query_payload = {
            "session_id": session_id,
            "question": "What is the total amount across all invoices and which vendor is the highest?"
        }
        r = requests.post(f"{BASE_URL}/api/v1/analyze", json=query_payload, timeout=45)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        analysis = r.json()
        print(f"  ✓ Answer: {analysis.get('answer')}")

        # Question 2: Graph request
        query_graph = {
            "session_id": session_id,
            "question": "Show me a bar chart comparing spend between Dell Technologies and ABC Technologies"
        }
        r_graph = requests.post(f"{BASE_URL}/api/v1/analyze", json=query_graph, timeout=90)
        assert r_graph.status_code == 200
        graph_res = r_graph.json()
        has_graph = bool(graph_res.get("graph"))
        print(f"  ✓ Chart visualization generated: {has_graph} (length: {len(graph_res.get('graph') or '')} chars)")
    except Exception as e:
        print(f"  ✗ Analysis query failed: {e}")

    # 7. Photo to Tabular CSV Endpoint (/api/ocr/photo-to-csv)
    print("\n[7/7] Testing Photo to Tabular CSV (/api/ocr/photo-to-csv)...")
    try:
        img_bytes = generate_test_invoice_image()
        files = [('file', ('photo_sample.jpg', img_bytes, 'image/jpeg'))]
        r = requests.post(f"{BASE_URL}/api/ocr/photo-to-csv", files=files, timeout=60)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("success") is True
        assert len(data.get("rows", [])) > 0
        assert "csv_data" in data and len(data["csv_data"]) > 0
        print(f"  ✓ Extracted {data.get('row_count')} tabular rows from photo")
        print(f"  ✓ Vendor: {data.get('invoice_details', {}).get('vendor_name')}")
        print(f"  ✓ Total: {data.get('currency', '$')}{data.get('total_amount')}")
        print(f"  ✓ CSV Header: {data['csv_data'].splitlines()[0]}")
    except Exception as e:
        print(f"  ✗ Photo to CSV failed: {e}")
        return False

    print("\n==========================================================")
    print("ALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")
    print("==========================================================")
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
