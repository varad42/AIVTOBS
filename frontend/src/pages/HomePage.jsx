import { useState } from "react";
import { useNavigate } from "react-router-dom";
import UploadCard from "../components/UploadCard";
import ProgressBar from "../components/ProgressBar";
import StatusFeed from "../components/StatusFeed";
import api from "../services/api";
import { useHistoryState } from "../context/HistoryContext";

export default function HomePage({ pushToast }) {
  const navigate = useNavigate();
  const { addHistoryItem } = useHistoryState();
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(0);

  const handleSubmit = async ({ file, videoUrl }) => {
    if (!file && !videoUrl) {
      pushToast("Please upload a file or provide a YouTube URL.", "error");
      return;
    }

    setLoading(true);
    setLogs(["Starting upload..."]);
    setProgress(10);

    try {
      let response;
      if (file) {
        response = await api.uploadVideo(file);
        setLogs((prev) => [...prev, "Video uploaded successfully."]);
      } else {
        response = await api.processYoutube(videoUrl);
        setLogs((prev) => [...prev, "YouTube URL accepted and queued."]);
      }

      const jobId = response?.jobId;
      if (!jobId) {
        throw new Error("Backend did not return a job id.");
      }

      addHistoryItem({
        id: jobId,
        label: file?.name || videoUrl,
        source: file ? "upload" : "youtube",
      });

      setProgress(35);
      navigate(`/processing/${jobId}`);
    } catch (error) {
      pushToast(error?.response?.data?.message || error.message || "Failed to start processing.", "error");
      setLogs((prev) => [...prev, "Request failed. Please retry."]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <UploadCard onSubmit={handleSubmit} loading={loading} />
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card dark:border-slate-800 dark:bg-slate-900">
        <ProgressBar value={progress} />
      </div>
      <StatusFeed logs={logs} />
    </div>
  );
}
