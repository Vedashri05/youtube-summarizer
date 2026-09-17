import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";
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
      <div className="max-w-xl mx-auto mt-8 bg-red-50 text-red-700 border border-red-300 rounded-xl p-5 flex items-start gap-3">
        <span className="w-2 h-2 rounded-full bg-red-500 mt-1.5 shrink-0" />
        <div>
          <p className="font-semibold">Processing failed</p>
          <p className="text-sm text-red-600 mt-0.5">{error}</p>
        </div>
      </div>
    );
  }

  if (!job) return null;

  const currentIndex = STEPS.indexOf(job.status);

  return (
    <div className="max-w-xl mx-auto mt-8 bg-white rounded-xl shadow-md p-6">
      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-4">
        Processing Video
      </p>

      <div className="space-y-4">
        {STEPS.map((step, index) => {
          const done = currentIndex > index || job.status === "complete";
          const active = currentIndex === index;

          return (
            <div key={step} className="flex items-center gap-3 text-sm">
              {done ? (
                <CheckCircle2 size={18} className="text-emerald-500 shrink-0" />
              ) : active ? (
                <Loader2 size={18} className="text-amber-500 shrink-0 animate-spin" />
              ) : (
                <Circle size={18} className="text-slate-300 shrink-0" />
              )}

              <span
                className={
                  done
                    ? "text-slate-800 font-medium"
                    : active
                    ? "text-amber-600 font-medium"
                    : "text-slate-400"
                }
              >
                {STEP_LABELS[step]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default JobStatus;