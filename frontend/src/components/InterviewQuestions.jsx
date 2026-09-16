function InterviewQuestions({ questions }) {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl shadow-md p-8">
      <h3 className="text-2xl font-semibold text-slate-800 mb-4">
        Likely Interview Questions
      </h3>

      <ol className="space-y-3">
        {questions.map((question, index) => (
          <li key={index} className="flex gap-3 text-slate-700 leading-7">
            <span className="font-semibold text-blue-600 shrink-0">
              Q{index + 1}.
            </span>
            <span>{question}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

export default InterviewQuestions;