import ReactMarkdown from "react-markdown";

const copyText = async (text) => {
  await navigator.clipboard.writeText(text || "");
};

const downloadFile = (name, content) => {
  const blob = new Blob([content || ""], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
};

export default function ResultSections({ result, onToast }) {
  const {
    videoInfo = {},
    transcript = "",
    summary = "",
    timestampSummary = "",
    blog = "",
    downloadSummaryPdfUrl,
    downloadBlogPdfUrl,
  } = result || {};

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-lg font-semibold">Video Info</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-[140px_1fr]">
          {videoInfo.thumbnail ? (
            <img src={videoInfo.thumbnail} alt="video thumbnail" className="h-24 w-full rounded-xl object-cover" />
          ) : (
            <div className="h-24 rounded-xl bg-slate-100 dark:bg-slate-800" />
          )}
          <div>
            <p className="font-medium">{videoInfo.title || "Untitled Video"}</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">{videoInfo.source || "Unknown source"}</p>
          </div>
        </div>
      </section>

      <details className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900">
        <summary className="cursor-pointer text-lg font-semibold">Transcript</summary>
        <p className="mt-4 whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">{transcript || "No transcript available."}</p>
      </details>

      <section className="rounded-2xl border border-brand-200 bg-brand-50/70 p-5 shadow-card dark:border-brand-900 dark:bg-brand-900/20">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Summary</h2>
          <div className="flex gap-2">
            <button
              onClick={async () => {
                await copyText(summary);
                onToast("Summary copied.");
              }}
              className="rounded-lg border border-brand-300 px-3 py-1.5 text-xs font-medium"
            >
              Copy Summary
            </button>
            <button
              onClick={() => downloadFile("summary.txt", summary)}
              className="rounded-lg border border-brand-300 px-3 py-1.5 text-xs font-medium"
            >
              Download .txt
            </button>
            {downloadSummaryPdfUrl ? (
              <a href={downloadSummaryPdfUrl} className="rounded-lg border border-brand-300 px-3 py-1.5 text-xs font-medium">
                Download .pdf
              </a>
            ) : null}
          </div>
        </div>
        <p className="mt-3 whitespace-pre-wrap text-sm">{timestampSummary || summary || "Summary not ready."}</p>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Blog</h2>
          <div className="flex gap-2">
            <button
              onClick={async () => {
                await copyText(blog);
                onToast("Blog copied.");
              }}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium dark:border-slate-700"
            >
              Copy Blog
            </button>
            <button
              onClick={() => downloadFile("blog.txt", blog)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium dark:border-slate-700"
            >
              Download .txt
            </button>
            {downloadBlogPdfUrl ? (
              <a href={downloadBlogPdfUrl} className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium dark:border-slate-700">
                Download .pdf
              </a>
            ) : null}
          </div>
        </div>
        <article className="prose mt-4 max-w-none dark:prose-invert">
          <ReactMarkdown>{blog || "Blog not ready."}</ReactMarkdown>
        </article>
      </section>
    </div>
  );
}
