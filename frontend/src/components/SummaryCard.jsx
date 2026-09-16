import { useState } from "react";

// YouTube always serves these sizes for every video, no API key needed.
// maxresdefault is intentionally NOT tried first - it only exists for
// videos uploaded in HD and 404s silently on a lot of videos, which is
// what was causing the blank box.
const QUALITY_FALLBACKS = ["hqdefault", "mqdefault", "default"];

function SummaryCard({ title, videoId, summary }) {
  const [qualityIndex, setQualityIndex] = useState(0);
  const [thumbnailFailed, setThumbnailFailed] = useState(false);

  const copySummary = async () => {
    try {
      await navigator.clipboard.writeText(summary);
      alert("Summary copied to clipboard!");
    } catch (err) {
      alert("Failed to copy summary.");
    }
  };

  const quality = QUALITY_FALLBACKS[qualityIndex];
  const thumbnailSrc = videoId
    ? `https://img.youtube.com/vi/${videoId}/${quality}.jpg`
    : null;

  const handleThumbnailError = () => {
    if (qualityIndex < QUALITY_FALLBACKS.length - 1) {
      setQualityIndex(qualityIndex + 1);
    } else {
      setThumbnailFailed(true);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-8">

      <div className="flex flex-col md:flex-row gap-6">

        {thumbnailSrc && !thumbnailFailed ? (
          <a
            href={`https://www.youtube.com/watch?v=${videoId}`}
            target="_blank"
            rel="noreferrer"
            className="w-full md:w-72 shrink-0"
          >
            <img
              src={thumbnailSrc}
              alt={title}
              onError={handleThumbnailError}
              className="w-full aspect-video object-cover rounded-xl shadow"
            />
          </a>
        ) : (
          <div className="w-full md:w-72 aspect-video shrink-0 bg-slate-200 rounded-xl flex items-center justify-center text-slate-400 text-sm">
            No thumbnail available
          </div>
        )}

        <div className="flex-1">

          <h2 className="text-3xl font-bold text-slate-800">
            {title}
          </h2>

          <p className="text-slate-500 mt-2">
            ✨ AI Generated Summary
          </p>

          <button
            onClick={copySummary}
            className="mt-5 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg transition"
          >
            📋 Copy Summary
          </button>

        </div>

      </div>

      <hr className="my-8" />

      <h3 className="text-2xl font-semibold text-slate-800 mb-4">
        Overall Summary
      </h3>

      <p className="text-slate-700 leading-8 text-justify">
        {summary}
      </p>

    </div>
  );
}

export default SummaryCard;