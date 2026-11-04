# ==========================================
# Stage 1: Build React 19 Frontend
# ==========================================
FROM node:20-slim AS frontend-builder
WORKDIR /frontend

# Copy dependencies first for layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source files
COPY index.html vite.config.js tailwind.config.js postcss.config.js ./
COPY public ./public
COPY src ./src

# Build static SPA assets into /frontend/dist
RUN npm run build

# ==========================================
# Stage 2: Unified Backend & Static Server
# ==========================================
FROM python:3.11-slim
WORKDIR /app

# Install system libraries needed for PyMuPDF, file inspection, and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend /app/backend

# Copy built frontend assets from stage 1 into /app/dist
COPY --from=frontend-builder /frontend/dist /app/dist

# Set Python path and default environment variables
ENV PYTHONPATH=/app
ENV GROQ_API_KEY=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
ENV GROQ_MODEL_EXTRACTION=qwen/qwen3.8-27b
ENV GROQ_MODEL_STANDARDIZATION=openai/gpt-oss-20b
ENV GROQ_MODEL_CHAT=openai/gpt-oss-20b
ENV HOST=0.0.0.0
ENV PORT=8000
ENV SERVE_FRONTEND=true
ENV FRONTEND_DIST_DIR=/app/dist

# Expose single port serving both frontend and backend
EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
