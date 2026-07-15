function SummaryCard({ summary }) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-8">

      <h2 className="text-2xl font-bold text-slate-800 mb-4">
        Overall Summary
      </h2>

      <p className="text-slate-700 leading-8 text-justify">
        {summary}
      </p>

    </div>
  );
}

export default SummaryCard;