import { useState } from "react";
import api from "../services/api";

function relevanceLabel(score, topScore) {
  // Gemini's cosine scores for a single-topic video cluster tightly
  // (e.g. 0.5-0.7 for everything, since the whole transcript is "about"
  // the same subject). A fixed global cutoff can't tell those apart -
  // it just calls everything "Good match". Ranking relative to the best
  // result actually returned is what makes the labels mean something.
  const ratio = topScore > 0 ? score / topScore : 0;

  if (ratio >= 0.97) return "Best match";
  if (ratio >= 0.9) return "Good match";
  return "Related";
}

function SemanticSearch({ videoId }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runSearch = async () => {
    const trimmed = query.trim();

    if (!trimmed || loading) return;

    setLoading(true);
    setError("");

    try {
      const response = await api.post("/search", {
        video_id: videoId,
        query: trimmed,
      });

      setResults(response.data.results);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail || "Search failed. Please try again."
      );
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const youtubeLinkAt = (seconds) =>
    `https://www.youtube.com/watch?v=${videoId}&t=${Math.floor(seconds)}s`;

  return (
    <div className="bg-white rounded-2xl shadow-md p-8">
      <h2 className="text-2xl font-bold text-slate-800">Search This Video</h2>

      <p className="text-slate-500 mt-1">
        Search by meaning, not just keywords. Try describing a concept
        instead of quoting the exact words used in the video.
      </p>

      <div className="mt-6 flex flex-col md:flex-row gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runSearch()}
          placeholder='e.g. "how does the model learn?"'
          disabled={loading}
          className="flex-1 px-5 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 disabled:bg-slate-100"
        />

        <button
          onClick={runSearch}
          disabled={loading}
          className={`px-8 py-3 rounded-xl font-semibold text-white transition
            ${
              loading
                ? "bg-blue-300 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 cursor-pointer"
            }`}
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {error && (
        <div className="mt-4 bg-red-100 text-red-700 border border-red-300 rounded-lg p-3">
          {error}
        </div>
      )}

      {results && (
        <div className="mt-6 space-y-3">
          {results.length === 0 && (
            <p className="text-slate-400 italic">
              Nothing in this video closely matches that.
            </p>
          )}

          {results.map((result, index) => (
            <a
              key={index}
              href={youtubeLinkAt(result.start_seconds)}
              target="_blank"
              rel="noreferrer"
              className="block border border-slate-200 hover:border-blue-300 hover:bg-blue-50 rounded-xl p-4 transition"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-blue-700 font-semibold">
                  {result.timestamp}
                </span>

                <span className="text-xs uppercase tracking-wide text-slate-400">
                  {relevanceLabel(result.score, results[0].score)}
                </span>
              </div>

              <p className="text-slate-600 leading-6">{result.snippet}</p>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export default SemanticSearch;