import { useEffect, useRef, useState } from "react";
import api from "../services/api";

const STEPS = ["transcribing", "indexing", "chunking", "summarizing"];

const STEP_LABELS = {
  transcribing: "Extracting transcript",
  indexing: "Indexing for chat",
  chunking: "Chunking",
  summarizing: "Generating summary",
};

function JobStatus({ jobId, onComplete }) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const intervalRef = useRef(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const response = await api.get(`/videos/${jobId}`);
        setJob(response.data);

        if (response.data.status === "complete") {
          clearInterval(intervalRef.current);
          onComplete(response.data);
        }

        if (response.data.status === "failed") {
          clearInterval(intervalRef.current);
          setError(response.data.error || "Processing failed");
        }
      } catch (err) {
        clearInterval(intervalRef.current);
        setError(err.response?.data?.detail || "Could not fetch job status");
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 2000);

    return () => clearInterval(intervalRef.current);
  }, [jobId, onComplete]);

  if (error) {
    return (
      <div className="max-w-xl mx-auto mt-8 bg-red-100 text-red-700 border border-red-300 rounded-lg p-4">
        {error}
      </div>
    );
  }

  if (!job) return null;

  const currentIndex = STEPS.indexOf(job.status);

  return (
    <div className="max-w-xl mx-auto mt-8 bg-white rounded-lg shadow p-6 space-y-3">
      {STEPS.map((step, index) => {
        const done = currentIndex > index || job.status === "complete";
        const active = currentIndex === index;

        return (
          <div key={step} className="flex items-center gap-2 text-sm">
            <span>{done ? "✓" : active ? "⏳" : "○"}</span>
            <span className={done ? "text-slate-800" : "text-slate-400"}>
              {STEP_LABELS[step]}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default JobStatus;