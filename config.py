import os

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
PASSWORD_RESET_HOURS = int(os.getenv("PASSWORD_RESET_HOURS", "1"))
