import { useState } from "react";

function SearchBox({ onSummarize, loading }) {
  const [url, setUrl] = useState("");

  const handleClick = () => {
    if (!url.trim()) {
      alert("Please enter a YouTube URL.");
      return;
    }

    onSummarize(url);
  };

  return (
    <div className="max-w-5xl mx-auto mt-10 bg-white rounded-2xl shadow-md p-8">
      
      <h2 className="text-3xl font-bold text-slate-800">
        YouTube Video Summarizer
      </h2>

      <p className="text-slate-500 mt-2">
        Paste a YouTube video link and get a structured AI-powered summary with
        timestamps.
      </p>

      <div className="mt-8 flex flex-col md:flex-row gap-4">

        <input
          type="text"
          placeholder="Paste YouTube URL here..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={loading}
          className="flex-1 px-5 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 disabled:bg-slate-100"
        />

        <button
          onClick={handleClick}
          disabled={loading}
          className={`px-8 py-3 rounded-xl font-semibold text-white transition
            ${
              loading
                ? "bg-blue-300 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 cursor-pointer"
            }`}
        >
          {loading ? "Generating..." : "Summarize"}
        </button>

      </div>
    </div>
  );
}

export default SearchBox;