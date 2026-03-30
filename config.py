import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "outputs")
JOBS_FOLDER = os.path.abspath(
    os.path.expanduser(
        os.getenv("JOBS_FOLDER", os.path.join(PROJECT_ROOT, "jobs"))
    )
)
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
GCS_UPLOAD_PREFIX = os.getenv("GCS_UPLOAD_PREFIX", "uploads")
GCS_JOBS_PREFIX = os.getenv("GCS_JOBS_PREFIX", "jobs")
GCS_OUTPUT_PREFIX = os.getenv("GCS_OUTPUT_PREFIX", "outputs")

MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB

SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("VITE_SUPABASE_URL", ""))
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", os.getenv("VITE_SUPABASE_ANON_KEY", ""))
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
