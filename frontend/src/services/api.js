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

export const api = {
  async uploadVideo(file) {
    const formData = new FormData();
    formData.append("video", file);
    const response = await client.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    const redirectJobId = extractJobIdFromResponseUrl(response?.request?.responseURL);
    return { ...response.data, jobId: redirectJobId || extractJobId(response.data) };
  },

  async processYoutube(videoUrl) {
    const formData = new FormData();
    formData.append("video_url", videoUrl);
    const response = await client.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    const redirectJobId = extractJobIdFromResponseUrl(response?.request?.responseURL);
    return { ...response.data, jobId: redirectJobId || extractJobId(response.data) };
  },

  async startProcessing({ jobId, model, length }) {
    const response = await client.post("/start-processing", {
      job_id: jobId,
      model,
      length,
    });
    return response.data;
  },

  async getStatus(jobId) {
    const response = await client.get(`/status/${jobId}`);
    return response.data;
  },

  async getResult(jobId) {
    const response = await client.get(`/result/${jobId}`);
    return response.data;
  },
};

export default api;
