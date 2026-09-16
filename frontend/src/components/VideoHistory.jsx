import { useEffect, useState } from "react";
import api from "../services/api";

const STATUS_STYLES = {
  pending: { label: "Queued", dot: "bg-slate-300" },
  transcribing: { label: "Extracting transcript", dot: "bg-amber-400" },
  indexing: { label: "Indexing", dot: "bg-amber-400" },
  chunking: { label: "Chunking", dot: "bg-amber-400" },
  summarizing: { label: "Generating summary", dot: "bg-amber-400" },
  complete: { label: "Complete", dot: "bg-emerald-500" },
  failed: { label: "Failed", dot: "bg-red-500" },
};

const MODE_LABELS = {
  beginner: "Beginner",
  technical: "Technical",
  quick_revision: "Quick Revision",
  interview_prep: "Interview Prep",
};

function VideoHistory({ onSelect, refreshKey }) {
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    api
      .get("/videos")
      .then((response) => {
        if (!cancelled) setVideos(response.data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.response?.data?.detail || "Could not load history");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // refreshKey lets the parent force a refetch (e.g. right after a new
    // job is created) without polling constantly.
  }, [refreshKey]);

  return (
    <aside className="w-72 shrink-0 bg-slate-900 text-slate-100 h-screen sticky top-0 flex flex-col overflow-hidden">
      <div className="px-5 py-5 border-b border-slate-800 shrink-0">
        <h2 className="font-semibold text-lg tracking-tight">
          Summary History
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          {videos.length} {videos.length === 1 ? "video" : "videos"}
        </p>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto px-3 py-3 space-y-1.5">
        {loading && (
          <p className="text-sm text-slate-500 px-2 py-2">Loading...</p>
        )}

        {!loading && error && (
          <p className="text-sm text-red-400 px-2 py-2">{error}</p>
        )}

        {!loading && !error && videos.length === 0 && (
          <p className="text-sm text-slate-500 px-2 py-2">
            Nothing summarized yet
          </p>
        )}

        {videos.map((video) => {
          const statusInfo = STATUS_STYLES[video.status] || {
            label: video.status,
            dot: "bg-slate-400",
          };

          const displayTitle = video.title || `Video ${video.video_id}`;

          return (
            <button
              key={video.job_id}
              onClick={() => onSelect(video.job_id)}
              className="w-full text-left rounded-lg px-3 py-2.5 hover:bg-slate-800 transition group"
            >
              <div className="text-sm font-medium text-slate-100 truncate group-hover:text-white">
                {displayTitle}
              </div>
              <div className="flex items-center gap-2 mt-1.5">
                <span className="text-[11px] uppercase tracking-wide bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                  {MODE_LABELS[video.mode] || video.mode}
                </span>
                <span className="flex items-center gap-1 text-xs text-slate-400">
                  <span className={`w-1.5 h-1.5 rounded-full ${statusInfo.dot}`} />
                  {statusInfo.label}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

export default VideoHistory;