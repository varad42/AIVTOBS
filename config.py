import os

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
PASSWORD_RESET_HOURS = int(os.getenv("PASSWORD_RESET_HOURS", "1"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_SUMMARY_MODEL = os.getenv("OLLAMA_SUMMARY_MODEL", "llama3.2")
LLAMA_CPP_URL = os.getenv("LLAMA_CPP_URL", "http://localhost:8080")
LLAMA_CPP_MODEL = os.getenv("LLAMA_CPP_MODEL", "local-llama")
