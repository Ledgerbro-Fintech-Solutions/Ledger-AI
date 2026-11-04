#!/usr/bin/env python3
"""
Simple test script for the Invoice Analysis API
"""

import json
import requests
import time
from pathlib import Path


def create_sample_invoice_json():
    """Create a sample invoice JSON file for testing"""
    sample_data = {
        "invoices": [
            {
                "invoice_id": "INV-001",
                "date": "2024-01-15",
                "vendor": "Tech Supplies Inc",
                "amount": 1250.00,
                "items": [
                    {"description": "Laptop", "quantity": 1, "price": 1000.00},
                    {"description": "Mouse", "quantity": 2, "price": 125.00}
                ]
            },
            {
                "invoice_id": "INV-002", 
                "date": "2024-01-20",
                "vendor": "Office Depot",
                "amount": 350.75,
                "items": [
                    {"description": "Paper", "quantity": 10, "price": 25.00},
                    {"description": "Pens", "quantity": 5, "price": 20.15}
                ]
            }
        ]
    }
    
    with open("sample_invoices.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    return "sample_invoices.json"


def test_api(base_url="http://localhost:8000"):
    """Test the API endpoints"""
    print(f"Testing Invoice Analysis API at {base_url}")
    
    # Test health endpoint
    print("\\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Create sample file
    print("\\n2. Creating sample invoice file...")
    sample_file = create_sample_invoice_json()
    print(f"Created: {sample_file}")
    
    # Test upload endpoint
    print("\\n3. Testing file upload...")
    try:
        with open(sample_file, 'rb') as f:
            files = [('files', (sample_file, f, 'application/json'))]
            response = requests.post(f"{base_url}/api/v1/upload/invoices", files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            session_id = upload_result['session_id']
            print(f"Upload successful: {upload_result}")
        else:
            print(f"Upload failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"Upload failed: {e}")
        return
    
    # Test analyze endpoint
    print("\\n4. Testing analysis...")
    test_questions = [
        "What is the total amount of all invoices?",
        "List all vendors and their invoice amounts",
        "Show me a breakdown of invoice amounts by vendor"
    ]
    
    for i, question in enumerate(test_questions):
        print(f"\\n4.{i+1}. Question: {question}")
        try:
            response = requests.post(f"{base_url}/api/v1/analyze", json={
                'session_id': session_id,
                'question': question
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"Answer: {result['answer']}")
                if result.get('table'):
                    print(f"Table data: {len(result['table'])} rows")
                if result.get('graph'):
                    print("Graph: Generated (base64 encoded)")
            else:
                print(f"Analysis failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Analysis failed: {e}")
    
    # Cleanup
    Path(sample_file).unlink(missing_ok=True)
    print(f"\\nTest completed. Cleaned up {sample_file}")


if __name__ == "__main__":
    test_api()
