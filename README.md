# AI Video Summarizer & Blog Generator

Turn long videos into useful, readable outputs in a few steps. This project downloads or uploads a video, extracts the audio, transcribes the content, generates a summary with selectable models, and can also turn the summary into a blog post.

The app includes authentication, job history, PDF exports, and support for both local processing and cloud-backed storage paths.

## Project Overview

AI Video Summarizer & Blog Generator is a full-stack web application for converting video content into:

- Clean transcripts
- Concise or detailed AI summaries
- Timestamped summaries
- Blog-style articles generated from the summary
- Downloadable PDF reports

It supports:

- Local video uploads
- YouTube URL processing
- Multiple summarization backends
- Google Gemini-powered blog generation
- Login, registration, Google sign-in, and password reset
- Dashboard history with job status tracking

## Features

- Upload a local video file or paste a YouTube URL
- Extract audio and transcribe it automatically
- Choose from multiple summary modes, including:
  - `t5`
  - `distilbart`
  - `long_t5`
  - `hybrid`
  - `llama_cpp`
- Generate a blog post from the summary using Gemini
- View cleaned transcripts, summaries, and blog output in the app
- Download summary and blog results as PDF files
- Track processing progress from the dashboard
- Revisit recent jobs from history
- Authenticate with email/password or Google OAuth
- Optional cloud storage support through Supabase or Google Cloud Storage

## Tech Stack

### Backend

- Python
- Flask
- Flask-Bcrypt
- `faster-whisper`
- `transformers`
- `yt-dlp`
- `google-genai`
- `google-cloud-storage`
- `reportlab`
- `Pillow`
- Supabase REST API for job/user/blog persistence

### Frontend

- React 18
- Vite
- Tailwind CSS
- React Router
- Axios
- React Markdown

### Integrations

- Google Gemini API
- Google OAuth
- Supabase Storage or Google Cloud Storage
- Optional local `llama.cpp` server

## Project Structure

```txt
.
├── app.py
├── config.py
├── auth/
├── database/
├── modules/
├── templates/
├── static/
├── frontend/
├── scripts/
├── requirements.txt
└── database/supabase_schema.sql
```

Key folders:

- `auth/` authentication and password reset flows
- `modules/` upload, processing, summarization, blog generation, history, and PDF output
- `database/` Supabase-backed collection layer and schema
- `templates/` Flask/Jinja pages
- `static/` legacy/static assets and frontend bundles
- `frontend/` React + Vite implementation of the UI

## Installation & Setup

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- `pip`
- `npm`
- A working `ffmpeg` installation is recommended for video/audio workflows
- A Supabase project
- A Gemini API key

### 1. Clone the repository

```bash
git clone <repo-url>
cd Ai-Video-Summarizer-and-blog
```

### 2. Set up the backend

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root and add the environment variables you need:

```env
SECRET_KEY=your-secret-key
SUPABASE_URL=your-supabase-project-url
SUPABASE_ANON_KEY=your-supabase-anon-key
GEMINI_API_KEY=your-gemini-api-key

# Optional
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
LLAMA_CPP_URL=http://localhost:8080
LLAMA_CPP_MODEL=local-llama
GCS_BUCKET_NAME=
SUPABASE_STORAGE_BUCKET=
SUPABASE_SERVICE_ROLE_KEY=
YTDLP_COOKIES_FROM_BROWSER=
YTDLP_COOKIES_FILE=
```

If you are using Supabase, apply the schema in `database/supabase_schema.sql` to your project first.

### 3. Set up the frontend

```bash
cd frontend
npm install
```

If the frontend needs to talk to a backend on a different origin, set the base URL to the Flask server itself. For local development with the Vite proxy, the default `/api` path already works:

```env
VITE_API_BASE_URL=http://localhost:5000
```

## Usage

### Run the backend

From the project root:

```bash
python app.py
```

The Flask app runs on:

```txt
http://localhost:5000
```

### Run the React frontend

From `frontend/`:

```bash
npm run dev
```

The Vite dev server usually runs on:

```txt
http://localhost:5173
```

### Typical flow

1. Sign in or create an account.
2. Upload a video file or paste a YouTube URL.
3. Wait for the transcript to finish processing.
4. Select a summarization model.
5. Review the summary, timestamped summary, transcript, and blog output.
6. Download PDF exports if needed.

## Screenshots


- Home or upload screen
![alt text](<Screenshot 2026-04-10 150745.png>) ![alt text](<Screenshot 2026-04-10 150758.png>) ![alt text](<Screenshot 2026-04-10 150834.png>)
- Dashboard with job progress
![alt text](<Screenshot 2026-04-10 150927.png>) ![alt text](<Screenshot 2026-04-10 150944.png>)
- Summary and blog result pages
![alt text](<Screenshot 2026-04-10 151020.png>) ![alt text](<Screenshot 2026-04-10 151101.png>)



-Gif
 <video controls src="AVITOBS_functioning_video-ezgif.com-video-to-gif-converter.mp4" title="Title"></video