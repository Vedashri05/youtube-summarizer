const MODES = [
  {
    id: "beginner",
    label: "Beginner",
    description: "Explain this video in simple language with basic examples.",
  },
  {
    id: "technical",
    label: "Technical",
    description: "Preserve technical terminology, implementation details and mathematical reasoning.",
  },
  {
    id: "quick_revision",
    label: "Quick Revision",
    description: "Give me only the most important points I should remember.",
  },
  {
    id: "interview_prep",
    label: "Interview Prep",
    description: "Extract important concepts, definitions, formulas and likely interview questions.",
  },
];

function ModeSelector({ mode, onChange, disabled }) {
  return (
    <div className="max-w-5xl mx-auto mt-6">
      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
        Summary Style
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {MODES.map((option) => {
          const isActive = option.id === mode;

          return (
            <button
              key={option.id}
              type="button"
              disabled={disabled}
              onClick={() => onChange(option.id)}
              title={option.description}
              className={`text-left p-4 rounded-xl border-2 transition
                ${
                  isActive
                    ? "border-blue-600 bg-blue-50"
                    : "border-slate-200 bg-white hover:border-blue-300"
                }
                ${disabled ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}`}
            >
              <p
                className={`font-semibold ${
                  isActive ? "text-blue-700" : "text-slate-800"
                }`}
              >
                {option.label}
              </p>

              <p className="text-xs text-slate-500 mt-1 leading-5">
                {option.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default ModeSelector;