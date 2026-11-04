import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Configuration
    app_name: str = "Ledger AI Unified Backend"
    app_description: str = "Integrated OCR, Invoice Processing, and Conversational RAG Analytics API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    serve_frontend: bool = True
    frontend_dist_dir: str = os.getenv("FRONTEND_DIST_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../dist")))

    # Groq API Configuration
    groq_api_key: str = os.getenv("GROQ_API_KEY", "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")
    
    # Models on Groq
    groq_model_extraction: str = os.getenv("GROQ_MODEL_EXTRACTION", "qwen/qwen3.8-27b")
    groq_model_standardization: str = os.getenv("GROQ_MODEL_STANDARDIZATION", "openai/gpt-oss-20b")
    groq_model_chat: str = os.getenv("GROQ_MODEL_CHAT", "openai/gpt-oss-20b")
    
    llm_temperature: float = 0.0
    max_retries: int = 3

    # Session Management
    session_timeout: int = 3600  # 1 hour in seconds

    # File Processing Configuration
    pdf_zoom_factor: float = 2.0
    image_quality: int = 85
    image_format: str = "JPEG"
    max_file_size: int = 50 * 1024 * 1024  # 50MB per file
    max_total_size: int = 200 * 1024 * 1024 # 200MB total
    allowed_file_types_str: str = Field(
        default="pdf,jpg,jpeg,png,tiff,bmp,webp,csv,json",
        alias="ALLOWED_FILE_TYPES"
    )

    # Logging
    log_level: str = "INFO"

    @property
    def allowed_file_types(self) -> List[str]:
        return [item.strip().lower() for item in self.allowed_file_types_str.split(",") if item.strip()]

    def validate_settings(self) -> None:
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required.")

settings = Settings()
