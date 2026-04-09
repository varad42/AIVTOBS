import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const client = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

const extractJobId = (payload) =>
  payload?.jobId || payload?.job_id || payload?.id || payload?.data?.jobId || payload?.data?.job_id;

const extractJobIdFromResponseUrl = (responseUrl) => {
  if (!responseUrl) return "";
  try {
    const parsed = new URL(responseUrl);
    return parsed.searchParams.get("job_id") || "";
  } catch {
    return "";
  }
};

const extractStateFromHtml = (html, scriptId) => {
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const script = doc.getElementById(scriptId);
    if (!script) return null;
    return JSON.parse(script.textContent || "{}");
  } catch {
    return null;
  }
};

const extractJobIdFromHtml = (html) => {
  if (!html) return "";

  const dashboardState = extractStateFromHtml(html, "dashboardInitialState");
  const fromState = dashboardState?.active_job?.job_id || "";
  if (fromState) return fromState;

  const match = String(html).match(/job_id=([a-f0-9-]{8,})/i);
  return match?.[1] || "";
};

const normalizeModelValue = (model) => {
  const value = String(model || "").toLowerCase();
  if (value === "bart") return "distilbart";
  return value;
};

export const api = {
  async uploadVideo(file) {
    const formData = new FormData();
    formData.append("video", file);
    const response = await client.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    const redirectJobId = extractJobIdFromResponseUrl(response?.request?.responseURL);
    const htmlJobId = extractJobIdFromHtml(response?.data);
    return { ...response.data, jobId: redirectJobId || htmlJobId || extractJobId(response.data) };
  },

  async processYoutube(videoUrl) {
    const formData = new FormData();
    formData.append("video_url", videoUrl);
    const response = await client.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    const redirectJobId = extractJobIdFromResponseUrl(response?.request?.responseURL);
    const htmlJobId = extractJobIdFromHtml(response?.data);
    return { ...response.data, jobId: redirectJobId || htmlJobId || extractJobId(response.data) };
  },

  async startProcessing({ jobId, model, length }) {
    const formData = new URLSearchParams();
    formData.append("model", normalizeModelValue(model));
    if (length) {
      formData.append("length", length);
    }

    const response = await client.post(`/select_model/${jobId}`, formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return response.data;
  },

  async getStatus(jobId) {
    const response = await client.get(`/dashboard?job_id=${encodeURIComponent(jobId)}`, {
      responseType: "text",
    });

    const state = extractStateFromHtml(response.data, "dashboardInitialState");
    const activeJob = state?.active_job || {};
    const status = activeJob?.status || "processing";
    const progress = Number(state?.active_progress || 0);

    const logs = [
      "Uploading video...",
      "Extracting audio...",
      "Transcribing...",
      "Generating summary...",
      "Generating blog...",
    ];

    return { status, progress, logs };
  },

  async getResult(jobId) {
    const [summaryResponse, blogResponse] = await Promise.all([
      client.get(`/summary/${encodeURIComponent(jobId)}`, { responseType: "text" }),
      client.get(`/blog/${encodeURIComponent(jobId)}`, { responseType: "text" }).catch(() => ({ data: "" })),
    ]);

    const summaryState = extractStateFromHtml(summaryResponse.data, "reactPageState") || {};
    const blogState = extractStateFromHtml(blogResponse.data, "reactPageState") || {};

    return {
      videoInfo: {
        title: summaryState.display_name || blogState.display_name || `Job ${String(jobId).slice(0, 8)}`,
        source: "processed",
        thumbnail: "",
      },
      transcript: "",
      summary: summaryState.summary || "",
      blog: blogState.blog || "",
      downloadSummaryPdfUrl: `${API_BASE_URL}/download_summary/${encodeURIComponent(jobId)}`,
      downloadBlogPdfUrl: `${API_BASE_URL}/download_blog/${encodeURIComponent(jobId)}`,
    };
  },
};

export default api;
