import { LogOut, Video } from "lucide-react";
import { useAuth } from "../context/AuthContext";

function Navbar() {
  const { logout } = useAuth();

  return (
    <nav className="bg-white shadow-sm border-b">

      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">

        <div className="flex items-center gap-3">
          <span className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
            <Video size={18} className="text-white" />
          </span>

          <h1 className="text-2xl font-bold text-blue-600">
            YouTube Video Summarizer
          </h1>
        </div>

        <button
          onClick={logout}
          title="Log out"
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition"
        >
          <LogOut size={16} />
          Log out
        </button>

      </div>

    </nav>
  );
}

export default Navbar;