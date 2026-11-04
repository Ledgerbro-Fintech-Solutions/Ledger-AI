# Invoice Analysis API

A professional FastAPI application for intelligent invoice analysis using RAG (Retrieval-Augmented Generation) and LangGraph.

## Features

- **File Upload**: Upload multiple invoice files in JSON or CSV format
- **Natural Language Queries**: Ask questions about your invoices in plain English
- **Multi-format Responses**: Get answers as text, structured tables, or visualized graphs
- **Session Management**: Secure session-based processing for concurrent users
- **Scalable Architecture**: Modular design following FastAPI best practices

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

Copy the environment template and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 3. Run the Application

```bash
# From the deployment_api directory
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## API Endpoints

### POST /api/v1/upload/invoices

Upload invoice files and create a new analysis session.

**Request**: Multipart form data with one or more files (JSON or CSV)

**Response**:
```json
{
  "session_id": "uuid-string",
  "message": "Files uploaded and processed successfully",
  "files_processed": 2
}
```

### POST /api/v1/analyze

Analyze invoices using natural language questions.

**Request**:
```json
{
  "session_id": "uuid-from-upload-response",
  "question": "What is the total amount of all invoices?"
}
```

**Response**:
```json
{
  "answer": "The total amount of all invoices is $15,750.00",
  "table": null,
  "graph": null,
  "session_id": "uuid-string"
}
```

The response may include:
- `answer`: Always present - text response to your question
- `table`: Optional - structured data as list of dictionaries
- `graph`: Optional - base64-encoded graph image

## Example Usage

### Using curl

1. Upload files:
```bash
curl -X POST "http://localhost:8000/api/v1/upload/invoices" \
  -F "files=@invoice1.json" \
  -F "files=@invoice2.csv"
```

2. Analyze data:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "question": "Show me all invoices over $1000"
  }'
```

### Using Python requests

```python
import requests

# Upload files
with open('invoice1.json', 'rb') as f1, open('invoice2.csv', 'rb') as f2:
    files = [
        ('files', ('invoice1.json', f1, 'application/json')),
        ('files', ('invoice2.csv', f2, 'text/csv'))
    ]
    response = requests.post('http://localhost:8000/api/v1/upload/invoices', files=files)
    session_id = response.json()['session_id']

# Analyze
analysis_response = requests.post('http://localhost:8000/api/v1/analyze', json={
    'session_id': session_id,
    'question': 'What is the average invoice amount?'
})
result = analysis_response.json()
print(result['answer'])
```

## Project Structure

```
deployment_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application setup
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Environment configuration
│   │   ├── rag_pipeline.py  # RAG and LangGraph logic
│   │   └── session_manager.py # Session management
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic models
│   └── routers/
│       ├── __init__.py
│       ├── upload.py        # File upload endpoints
│       ├── analyze.py       # Analysis endpoints
│       └── health.py        # Health check endpoints
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md              # This file
```

## Configuration

All configuration is handled through environment variables. See `.env.example` for available options.

### Required Environment Variables

- `GROQ_API_KEY`: Your Groq API key

### Optional Environment Variables

- `SESSION_TIMEOUT`: Session timeout in seconds (default: 3600)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10MB)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

## Deployment

### Production Deployment

For production, consider:

1. Use a process manager like Gunicorn:
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. Set appropriate CORS origins in production
3. Use a reverse proxy like Nginx
4. Consider using a persistent vector store instead of in-memory FAISS
5. Implement proper logging and monitoring

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the `deployment_api` directory
2. **Groq API Errors**: Verify your API key is correct and has sufficient quota
3. **File Upload Issues**: Check file format and size limits
4. **Session Expired**: Sessions expire after 1 hour by default

### Logs

The application logs to stdout. In production, configure proper logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```
