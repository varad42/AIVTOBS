# AI Video Summarizer Frontend (React + Vite + Tailwind)

This is a fully new frontend for the AI Video Summarizer & Blog Generator, built without backend changes.

## Stack

- React + Vite
- Tailwind CSS
- React Router
- Axios
- React Markdown

## Structure

- `src/components` reusable UI pieces
- `src/pages` flow pages (Home, Model Selection, Processing, Result)
- `src/services/api.js` backend API calls
- `src/hooks/useJobStatus.js` polling hook
- `src/context/HistoryContext.jsx` sidebar history state

## Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Configure API base URL:

```bash
cp .env.example .env
```

3. Run dev server:

```bash
npm run dev
```

4. Open app:

```txt
http://localhost:5173
```

## API Endpoints Used

- `POST /upload-video`
- `POST /process-youtube`
- `POST /start-processing`
- `GET /status/{id}`
- `GET /result/{id}`

If your backend currently uses different routes, keep backend unchanged and add a gateway/rewrite/proxy layer or map endpoints in `src/services/api.js`.

## Features Included

- Drag & drop video upload
- YouTube URL input
- Model + summary length selection
- Processing lock screen with thinking animation
- Real-time style status feed + progress polling
- Final output sections for transcript, summary, blog
- Markdown rendering for blog
- Copy + download actions
- Sidebar history (local storage)
- Dark/light mode toggle
- Toast notifications
- Skeleton loaders
