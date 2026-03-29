import os

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
JOBS_FOLDER = "jobs"

MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
PASSWORD_RESET_HOURS = int(os.getenv("PASSWORD_RESET_HOURS", "1"))
LLAMA_CPP_URL = os.getenv("LLAMA_CPP_URL", "http://localhost:8080")
LLAMA_CPP_MODEL = os.getenv("LLAMA_CPP_MODEL", "local-llama")
YTDLP_COOKIES_FROM_BROWSER = os.getenv("YTDLP_COOKIES_FROM_BROWSER", "")
YTDLP_COOKIES_FILE = os.getenv("YTDLP_COOKIES_FILE", "")

for folder in (UPLOAD_FOLDER, OUTPUT_FOLDER, JOBS_FOLDER):
    os.makedirs(folder, exist_ok=True)
