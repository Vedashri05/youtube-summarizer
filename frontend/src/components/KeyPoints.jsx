function KeyPoints({ points }) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-8">

      <h2 className="text-2xl font-bold text-slate-800 mb-6">
        Key Points
      </h2>

      <div className="space-y-5">

        {points.map((point, index) => (

          <div
            key={index}
            className="border-l-4 border-blue-500 pl-4"
          >

            <p className="text-blue-600 font-semibold">
              🕒 {point.timestamp}
            </p>

            <p className="text-slate-700 mt-1">
              {point.point}
            </p>

          </div>

        ))}

      </div>

    </div>
  );
}

export default KeyPoints;