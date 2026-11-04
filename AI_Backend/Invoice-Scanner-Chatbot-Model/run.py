
import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Check for environment file
env_file = app_dir / ".env"
if not env_file.exists():
    print("WARNING: .env file is not found.")
    print("You need to set GROQ_API_KEY at minimum.")

try:
    from app.main import app
    import uvicorn
    from app.core.config import settings
    
    if __name__ == "__main__":
        print(f"Starting {settings.api_title} v{settings.api_version}")
        print(f"Server will be available at: http://{settings.host}:{settings.port}")
        print(f"API documentation: http://{settings.host}:{settings.port}/docs")
        
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=True,
            log_level="info"
        )

except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure you have installed all dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    sys.exit(1)
