import { useState } from "react";
import { useAuth } from "../context/AuthContext";

function AuthForm() {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail || "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-6">

        <div className="w-full max-w-5xl bg-white rounded-2xl shadow-xl overflow-hidden flex min-h-[600px]">

        {/* LEFT IMAGE */}
        <div className="hidden md:block md:w-1/2 p-5">
            <div className="h-full rounded-xl overflow-hidden">
            <img
                src="/youtube-ai-image.png"
                alt="YouTube AI Summarizer"
                className="w-full h-full object-cover"
            />
            </div>
        </div>

        {/* RIGHT LOGIN / SIGNUP */}
        <div className="w-full md:w-1/2 flex items-center justify-center p-8">

            <form
            onSubmit={handleSubmit}
            className="bg-white p-8 rounded-lg w-full max-w-sm space-y-4"
            >
            <h1 className="text-xl font-semibold text-slate-800">
                {mode === "login" ? "Log in" : "Create an account"}
            </h1>

            <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full border border-slate-300 rounded-md px-3 py-2"
            />

            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full border border-slate-300 rounded-md px-3 py-2"
            />

            {error && (
                <p className="text-red-600 text-sm">
                {error}
                </p>
            )}

            <button
                type="submit"
                disabled={loading}
                className="w-full bg-slate-800 text-white rounded-md py-2 disabled:opacity-50"
            >
                {loading
                ? "Please wait..."
                : mode === "login"
                ? "Log in"
                : "Sign up"}
            </button>

            <p className="text-sm text-slate-500 text-center">
                {mode === "login"
                ? "No account yet?"
                : "Already have an account?"}{" "}

                <button
                type="button"
                onClick={() =>
                    setMode(mode === "login" ? "register" : "login")
                }
                className="text-slate-800 underline"
                >
                {mode === "login" ? "Sign up" : "Log in"}
                </button>
            </p>
            </form>

        </div>
        </div>
    </div>
    );
}

export default AuthForm;