import { useEffect, useRef, useState } from "react";
import api from "../services/api";

export default function UploadCard({ onSubmit, loading }) {
  const [videoUrl, setVideoUrl] = useState("");
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState(null);
  const inputRef = useRef(null);

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  };

  const process = () => {
    onSubmit({ file, videoUrl: videoUrl.trim() });
  };

  useEffect(() => {
    if (!videoUrl.trim()) {
      setPreview(null);
      return undefined;
    }

    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const result = await api.getYoutubePreview(videoUrl.trim());
        if (!cancelled) {
          setPreview(result);
        }
      } catch {
        if (!cancelled) {
          setPreview(null);
        }
      }
    }, 500);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [videoUrl]);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">AI Video Summarizer & Blog Generator</h1>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
        Upload a file or paste a YouTube URL to start.
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`mt-5 rounded-2xl border-2 border-dashed p-8 text-center transition ${
          dragging
            ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
            : "border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50"
        }`}
      >
        <p className="text-sm text-slate-600 dark:text-slate-300">
          {file ? `Selected file: ${file.name}` : "Drag & drop video here"}
        </p>
        <button
          onClick={() => inputRef.current?.click()}
          type="button"
          className="mt-3 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
        >
          Browse File
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="hidden"
        />
      </div>

      <div className="mt-4">
        <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">YouTube URL</label>
        <input
          type="url"
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 transition focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        {preview?.title ? (
          <div className="mt-3 flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
            {preview.thumbnail_url ? (
              <img src={preview.thumbnail_url} alt={preview.title} className="h-16 w-24 rounded-lg object-cover" />
            ) : null}
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">{preview.title}</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Ready to queue this YouTube video.</p>
            </div>
          </div>
        ) : null}
      </div>

      <button
        disabled={loading}
        onClick={process}
        className="mt-5 w-full rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Starting..." : "Process Video"}
      </button>
    </section>
  );
}
