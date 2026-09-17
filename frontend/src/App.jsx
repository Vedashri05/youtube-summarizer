import { useState } from "react";
import { FileVideo } from "lucide-react";
import Navbar from "./components/Navbar";
import SearchBox from "./components/SearchBox";
import ModeSelector from "./components/ModeSelector";
import SummaryCard from "./components/SummaryCard";
import KeyPoints from "./components/KeyPoints";
import Topics from "./components/Topics";
import InterviewQuestions from "./components/InterviewQuestions";
import ChatBox from "./components/ChatBox";
import Loader from "./components/Loader";
import AuthForm from "./components/AuthForm";
import VideoHistory from "./components/VideoHistory";
import JobStatus from "./components/JobStatus";
import api from "./services/api";
import { AuthProvider, useAuth } from "./context/AuthContext";

function EmptyState() {
  return (
    <div className="max-w-5xl mx-auto mt-8">
      <div className="border-2 border-dashed border-slate-300 rounded-2xl py-16 flex flex-col items-center text-center">
        <span className="w-14 h-14 rounded-full bg-blue-50 flex items-center justify-center mb-4">
          <FileVideo size={26} className="text-blue-500" />
        </span>
        <p className="text-slate-600 font-medium">
          No video selected yet
        </p>
        <p className="text-slate-400 text-sm mt-1 max-w-sm">
          Paste a YouTube link above, or pick a video from your history on
          the left, to see its summary here.
        </p>
      </div>
    </div>
  );
}

function Dashboard() {
  const [mode, setMode] = useState("technical");
  const [summary, setSummary] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [historyKey, setHistoryKey] = useState(0);

  const submitVideo = async (url, videoMode) => {
    try {
      setLoading(true);
      setError("");
      setSummary(null);
      setJobId(null);

      const response = await api.post("/videos", { url, mode: videoMode });

      // Kick off polling instead of waiting here - JobStatus takes over
      // and calls handleJobComplete once status === "complete".
      setJobId(response.data.job_id);
      setHistoryKey((key) => key + 1);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSummary = (url) => submitVideo(url, mode);

  // Failed videos get a retry action in the sidebar instead of being a
  // dead end. video_id is the YouTube ID, so the watch URL is
  // reconstructable without needing to have stored the original link.
  const handleRetry = (video) => {
    const url = `https://www.youtube.com/watch?v=${video.video_id}`;
    submitVideo(url, video.mode);
  };

  const handleJobComplete = (job) => {
    setSummary({ ...job.summary, video_id: job.video_id, mode: job.mode });
    setJobId(null);
    setHistoryKey((key) => key + 1);
  };

  const handleSelectFromHistory = async (selectedJobId) => {
    setError("");
    setSummary(null);
    setJobId(null);

    try {
      const response = await api.get(`/videos/${selectedJobId}`);

      if (response.data.status === "complete") {
        setSummary({
          ...response.data.summary,
          video_id: response.data.video_id,
          mode: response.data.mode,
        });
      } else if (response.data.status === "failed") {
        setError(response.data.error || "This video failed to process");
      } else {
        // Still in progress - resume polling it
        setJobId(selectedJobId);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load that video");
    }
  };

  const showEmptyState = !loading && !jobId && !error && !summary;

  return (
    <div className="min-h-screen bg-slate-100 flex">
      <VideoHistory
        onSelect={handleSelectFromHistory}
        onRetry={handleRetry}
        refreshKey={historyKey}
      />

      <div className="flex-1">
        <Navbar />

        <SearchBox onSummarize={handleSummary} loading={loading} />

        <ModeSelector mode={mode} onChange={setMode} disabled={loading} />

        {loading && <Loader />}

        {jobId && <JobStatus jobId={jobId} onComplete={handleJobComplete} />}

        {error && (
          <div className="max-w-5xl mx-auto mt-6 bg-red-100 text-red-700 border border-red-300 rounded-lg p-4">
            {error}
          </div>
        )}

        {showEmptyState && <EmptyState />}

        {summary && (
          <div className="max-w-5xl mx-auto mt-8 space-y-6 pb-10">
            <SummaryCard
              title={summary.title}
              videoId={summary.video_id}
              summary={summary.overall_summary}
            />

            <KeyPoints points={summary.key_points} />

            <Topics topics={summary.topics_covered} />

            <InterviewQuestions questions={summary.likely_interview_questions} />

            {summary.video_id && (
              <ChatBox key={`chat-${summary.video_id}`} videoId={summary.video_id} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function AppShell() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Dashboard /> : <AuthForm />;
}

function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}

export default App;