import { useState, useRef, useEffect } from "react";
import api from "../services/api";

function ChatBox({ videoId }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const bottomRef = useRef(null);

  // Keep the newest message in view
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const askQuestion = async () => {
    const trimmed = question.trim();

    if (!trimmed || loading) return;

    const userMessage = { role: "user", content: trimmed };

    // The backend is stateless, so the client owns the conversation.
    // We send the history as it was BEFORE this question.
    const historyToSend = messages.map(({ role, content }) => ({
      role,
      content,
    }));

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const response = await api.post("/chat", {
        video_id: videoId,
        question: trimmed,
        history: historyToSend.slice(-6),
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.data.answer,
          sources: response.data.sources,
        },
      ]);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Could not get an answer. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const youtubeLinkAt = (seconds) =>
    `https://www.youtube.com/watch?v=${videoId}&t=${Math.floor(seconds)}s`;

  return (
    <div className="bg-white rounded-2xl shadow-md p-8">
      <h2 className="text-2xl font-bold text-slate-800">Chat with the Video</h2>

      <p className="text-slate-500 mt-1">
        Ask anything about this video. Every answer is taken from the
        transcript and links back to the exact moment.
      </p>

      <div className="mt-6 space-y-4 max-h-[26rem] overflow-y-auto pr-2">
        {messages.length === 0 && !loading && (
          <p className="text-slate-400 italic">
            Try: "Explain the part about feature scaling."
          </p>
        )}

        {messages.map((message, index) =>
          message.role === "user" ? (
            <div key={index} className="flex justify-end">
              <div className="bg-blue-600 text-white px-4 py-3 rounded-2xl rounded-br-sm max-w-[80%]">
                {message.content}
              </div>
            </div>
          ) : (
            <div key={index} className="flex justify-start">
              <div className="bg-slate-100 text-slate-800 px-4 py-3 rounded-2xl rounded-bl-sm max-w-[85%]">
                <p className="leading-7">{message.content}</p>

                {message.sources?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-300">
                    <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                      Sources
                    </p>

                    <div className="flex flex-wrap gap-2">
                      {message.sources.map((source, i) => (
                        <a
                          key={i}
                          href={youtubeLinkAt(source.start_seconds)}
                          target="_blank"
                          rel="noreferrer"
                          title={source.snippet}
                          className="bg-white border border-blue-300 text-blue-700 text-sm px-3 py-1 rounded-full hover:bg-blue-50"
                        >
                          {source.timestamp}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 text-slate-500 px-4 py-3 rounded-2xl rounded-bl-sm">
              Searching the transcript...
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="mt-4 bg-red-100 text-red-700 border border-red-300 rounded-lg p-3">
          {error}
        </div>
      )}

      <div className="mt-6 flex flex-col md:flex-row gap-3">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && askQuestion()}
          placeholder="Ask a question about this video..."
          disabled={loading}
          className="flex-1 px-5 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-700 disabled:bg-slate-100"
        />

        <button
          onClick={askQuestion}
          disabled={loading}
          className={`px-8 py-3 rounded-xl font-semibold text-white transition
            ${
              loading
                ? "bg-blue-300 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 cursor-pointer"
            }`}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>
    </div>
  );
}

export default ChatBox;