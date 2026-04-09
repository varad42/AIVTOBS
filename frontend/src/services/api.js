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

const parseHtml = (html) => {
  const parser = new DOMParser();
  return parser.parseFromString(html, "text/html");
};

export const extractStateFromHtml = (html, scriptId) => {
  try {
    const doc = parseHtml(html);
    const script = doc.getElementById(scriptId);
    if (!script) return null;
    return JSON.parse(script.textContent || "{}");
  } catch {
    return null;
  }
};

export const extractFlashesFromHtml = (html) => {
  try {
    const doc = parseHtml(html);
    return [...doc.querySelectorAll(".flash")].map((element) => ({
      category:
        [...element.classList].find((className) => className.startsWith("flash-"))?.replace("flash-", "") ||
        "info",
      message: element.textContent?.replace(/\s+/g, " ").trim() || "",
    }));
  } catch {
    return [];
  }
};

const extractDashboardEnvelope = (html) => {
  const state = extractStateFromHtml(html, "dashboardInitialState");
  const doc = parseHtml(html);
  const unauthenticated = Boolean(doc.querySelector(".login-overlay"));
  return {
    authenticated: Boolean(state?.user_email) && !unauthenticated,
    dashboard: state,
    flashes: extractFlashesFromHtml(html),
  };
};

const extractJobIdFromHtml = (html) => {
  if (!html) return "";

  const dashboardState = extractStateFromHtml(html, "dashboardInitialState");
  const fromState = dashboardState?.active_job?.job_id || "";
  if (fromState) return fromState;

  const match = String(html).match(/job_id=([a-f0-9-]{8,})/i);
  return match?.[1] || "";
};

const isLikelyLoginPageHtml = (html) => {
  const text = String(html || "").toLowerCase();
  return (
    text.includes("user login") ||
    text.includes("name=\"password\"") ||
    text.includes("continue with google")
  );
};

const isLikelyDashboardHtml = (html) => {
  const text = String(html || "").toLowerCase();
  return text.includes("dashboardreactroot") || text.includes("dashboardinitialstate");
};

const normalizeModelValue = (model) => {
  const value = String(model || "").toLowerCase();
  if (value === "bart") return "distilbart";
  return value;
};

const requestHtml = async (config) => {
  const response = await client.request({
    responseType: "text",
    maxRedirects: 5,
    ...config,
  });
  return response.data;
};

export const api = {
  async getDashboardState({ jobId = "", newChat = false } = {}) {
    const params = new URLSearchParams();
    if (jobId) params.set("job_id", jobId);
    if (newChat) params.set("new_chat", "1");
    const suffix = params.toString() ? `?${params.toString()}` : "";
    const html = await requestHtml({ method: "GET", url: `/dashboard${suffix}` });
    return extractDashboardEnvelope(html);
  },

  async login({ email, password }) {
    const body = new URLSearchParams();
    body.append("email", email);
    body.append("password", password);

    const html = await requestHtml({
      method: "POST",
      url: "/",
      data: body,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    return extractDashboardEnvelope(html);
  },

  async signup({ email, password }) {
    const body = new URLSearchParams();
    body.append("email", email);
    body.append("password", password);

    const html = await requestHtml({
      method: "POST",
      url: "/register",
      data: body,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    return extractDashboardEnvelope(html);
  },

  async logout() {
    await client.get("/logout");
  },

  async getYoutubePreview(videoUrl) {
    const response = await client.get(`/youtube_preview?url=${encodeURIComponent(videoUrl)}`);
    return response.data;
  },

  async uploadVideo(file) {
    const formData = new FormData();
    formData.append("video", file);
    const response = await client.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      responseType: "text",
    });
    const redirectJobId = extractJobIdFromResponseUrl(response?.request?.responseURL);
    const htmlJobId = extractJobIdFromHtml(response?.data);
    const jobId = redirectJobId || htmlJobId || extractJobId(response.data);
    if (!jobId && isLikelyLoginPageHtml(response?.data)) {
      throw new Error("No active backend session. Please login first.");
    }
    return { ...response.data, jobId };
  },

  async processYoutube(videoUrl) {
    const formData = new FormData();
    formData.append("video_url", videoUrl);
    const response = await client.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      responseType: "text",
    });
    const redirectJobId = extractJobIdFromResponseUrl(response?.request?.responseURL);
    const htmlJobId = extractJobIdFromHtml(response?.data);
    const jobId = redirectJobId || htmlJobId || extractJobId(response.data);
    if (!jobId && isLikelyLoginPageHtml(response?.data)) {
      throw new Error("No active backend session. Please login first.");
    }
    return { ...response.data, jobId };
  },

  async getModelSelection(jobId) {
    const html = await requestHtml({
      method: "GET",
      url: `/select_model/${encodeURIComponent(jobId)}`,
    });
    return extractStateFromHtml(html, "reactPageState") || {};
  },

  async startProcessing({ jobId, model, transcriptSource = "processed" }) {
    const formData = new URLSearchParams();
    formData.append("model", normalizeModelValue(model));
    formData.append("transcript_source", transcriptSource);

    await client.post(`/select_model/${jobId}`, formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },

  async getStatus(jobId) {
    const envelope = await api.getDashboardState({ jobId });
    const activeJob = envelope?.dashboard?.active_job || {};
    const status = activeJob?.status || "processing";
    const progress = Number(envelope?.dashboard?.active_progress || 0);

    const statusLogMap = {
      uploading: ["Receiving upload...", "Queuing job..."],
      uploaded: ["Upload completed.", "Waiting for worker..."],
      processing: ["Worker claimed the job.", "Preparing processing pipeline..."],
      downloading: ["Downloading source video..."],
      extracting_audio: ["Extracting audio track..."],
      transcribing: ["Transcribing audio..."],
      waiting_for_model: ["Transcript ready.", "Waiting for model selection..."],
      summarize_requested: ["Model selected.", "Generating summary..."],
      summary_ready: ["Summary ready."],
      blog_requested: ["Generating blog draft..."],
      blog_ready: ["Blog ready."],
      error: ["Processing failed."],
    };

    return {
      status,
      progress,
      logs: statusLogMap[status] || ["Processing..."],
      dashboard: envelope.dashboard,
      authenticated: envelope.authenticated,
      flashes: envelope.flashes,
    };
  },

  async triggerBlog(jobId) {
    await client.get(`/generate_blog/${encodeURIComponent(jobId)}`);
  },

  async getResult(jobId) {
    const [summaryResponse, blogResponse, transcriptResponse] = await Promise.all([
      client.get(`/summary/${encodeURIComponent(jobId)}`, { responseType: "text" }),
      client.get(`/blog/${encodeURIComponent(jobId)}`, { responseType: "text" }).catch(() => ({ data: "" })),
      client
        .get(`/cleaned_transcript/${encodeURIComponent(jobId)}`, { responseType: "text" })
        .catch(() => ({ data: "" })),
    ]);

    const summaryState = extractStateFromHtml(summaryResponse.data, "reactPageState") || {};
    const blogState = extractStateFromHtml(blogResponse.data, "reactPageState") || {};
    const transcriptState = extractStateFromHtml(transcriptResponse.data, "reactPageState") || {};

    return {
      videoInfo: {
        title:
          summaryState.display_name ||
          blogState.display_name ||
          transcriptState.job_title ||
          `Job ${String(jobId).slice(0, 8)}`,
        source: "processed",
        thumbnail: "",
      },
      transcript: transcriptState.cleaned_transcript || "",
      summary: summaryState.summary || "",
      timestampSummary: summaryState.timestamp_summary || "",
      blog: blogState.blog || "",
      modelName: summaryState.model_name || blogState.model_name || "",
      downloadSummaryPdfUrl: `${API_BASE_URL}/download_summary/${encodeURIComponent(jobId)}`,
      downloadBlogPdfUrl: `${API_BASE_URL}/download_blog/${encodeURIComponent(jobId)}`,
    };
  },
};

export default api;
