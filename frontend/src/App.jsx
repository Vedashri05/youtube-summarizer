import { useState } from "react";
import Navbar from "./components/Navbar";
import SearchBox from "./components/SearchBox";
import SummaryCard from "./components/SummaryCard";
import KeyPoints from "./components/KeyPoints";
import Topics from "./components/Topics";
import api from "./services/api";
import Loader from "./components/Loader";

function App() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSummary = async (url) => {
    try {
      setLoading(true);
      setError("");
      setSummary(null);

      const response = await api.post("/summary", {
        url: url,
      });

      setSummary(response.data);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <SearchBox
        onSummarize={handleSummary}
        loading={loading}
      />

      {loading && <Loader />}

      {error && (
        <div className="max-w-5xl mx-auto mt-6 bg-red-100 text-red-700 border border-red-300 rounded-lg p-4">
          {error}
        </div>
      )}

      {summary && (
        <div className="max-w-5xl mx-auto mt-8 space-y-6 pb-10">
          <SummaryCard summary={summary.overall_summary} />

          <KeyPoints points={summary.key_points} />

          <Topics topics={summary.topics_covered} />
        </div>
      )}
    </div>
  );
}

export default App;