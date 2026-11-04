import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # API Configuration
    api_title: str = "Invoice Analysis API"
    api_description: str = "Intelligent invoice analysis using RAG and LangGraph"
    api_version: str = "1.0.0"
    
    # Groq Configuration
    groq_api_key: str
    
    # Session Configuration
    session_timeout: int = 3600  # 1 hour in seconds
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types_str: str = Field(default="json,csv", alias="ALLOWED_FILE_TYPES")
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    @property
    def allowed_file_types(self) -> List[str]:
        """Parse comma-separated file types from environment variable"""
        return [item.strip() for item in self.allowed_file_types_str.split(',') if item.strip()]


# Global settings instance
settings = Settings()
