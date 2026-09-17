import { useEffect, useMemo, useState } from "react";
import { PanelLeftClose, PanelLeft, Search, RotateCw } from "lucide-react";
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

function VideoHistory({ onSelect, onRetry, refreshKey }) {
  const [videos, setVideos] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [collapsed, setCollapsed] = useState(false);

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

  const filteredVideos = useMemo(() => {
    const trimmed = query.trim().toLowerCase();

    if (!trimmed) return videos;

    return videos.filter((video) =>
      (video.title || video.video_id || "").toLowerCase().includes(trimmed)
    );
  }, [videos, query]);

  // Collapsed = a slim icon rail, same idea as ChatGPT's collapsed sidebar.
  if (collapsed) {
    return (
      <aside className="w-14 shrink-0 bg-slate-900 text-slate-100 h-screen sticky top-0 flex flex-col items-center py-5 gap-4">
        <button
          onClick={() => setCollapsed(false)}
          title="Expand history"
          className="p-2 rounded-lg hover:bg-slate-800 transition"
        >
          <PanelLeft size={20} />
        </button>

        <button
          onClick={() => setCollapsed(false)}
          title="Search videos"
          className="p-2 rounded-lg hover:bg-slate-800 transition"
        >
          <Search size={18} />
        </button>
      </aside>
    );
  }

  return (
    <aside className="w-72 shrink-0 bg-slate-900 text-slate-100 h-screen sticky top-0 flex flex-col overflow-hidden">
      {/* Thin, ChatGPT-style scrollbar - only affects elements with this class */}
      <style>{`
        .thin-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .thin-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .thin-scrollbar::-webkit-scrollbar-thumb {
          background-color: rgba(148, 163, 184, 0.3);
          border-radius: 9999px;
        }
        .thin-scrollbar::-webkit-scrollbar-thumb:hover {
          background-color: rgba(148, 163, 184, 0.55);
        }
        .thin-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: rgba(148, 163, 184, 0.3) transparent;
        }
      `}</style>

      <div className="px-4 py-4 border-b border-slate-800 shrink-0 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-lg tracking-tight">
            Summary History
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            {videos.length} {videos.length === 1 ? "video" : "videos"}
          </p>
        </div>

        <button
          onClick={() => setCollapsed(true)}
          title="Collapse sidebar"
          className="p-1.5 rounded-lg hover:bg-slate-800 transition text-slate-400 hover:text-white shrink-0"
        >
          <PanelLeftClose size={18} />
        </button>
      </div>

      {/* Search sits right under the header, like ChatGPT's top search bar */}
      <div className="px-3 pt-3 shrink-0">
        <div className="relative">
          <Search
            size={15}
            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500"
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search videos"
            className="w-full bg-slate-800 text-sm text-slate-100 placeholder-slate-500 rounded-lg pl-8 pr-3 py-2 focus:outline-none focus:ring-1 focus:ring-slate-600"
          />
        </div>
      </div>

      <div className="thin-scrollbar flex-1 min-h-0 overflow-y-auto px-3 py-3 space-y-1.5 mt-1">
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

        {!loading && !error && videos.length > 0 && filteredVideos.length === 0 && (
          <p className="text-sm text-slate-500 px-2 py-2">
            No videos match "{query}"
          </p>
        )}

        {filteredVideos.map((video) => {
          const statusInfo = STATUS_STYLES[video.status] || {
            label: video.status,
            dot: "bg-slate-400",
          };

          const displayTitle = video.title || `Video ${video.video_id}`;
          const isFailed = video.status === "failed";

          return (
            <div
              key={video.job_id}
              className="relative group rounded-lg hover:bg-slate-800 transition"
            >
              <button
                onClick={() => onSelect(video.job_id)}
                className="w-full text-left px-3 py-2.5"
              >
                <div className="text-sm font-medium text-slate-100 truncate group-hover:text-white pr-6">
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

              {/* Failed jobs get a retry action instead of being a dead end.
                  stopPropagation so clicking retry doesn't also select the
                  (failed, empty) job underneath it. */}
              {isFailed && onRetry && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRetry(video);
                  }}
                  title="Retry this video"
                  className="absolute right-2 top-2.5 p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-700 transition"
                >
                  <RotateCw size={14} />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}

export default VideoHistory;