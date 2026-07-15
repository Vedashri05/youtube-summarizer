function Topics({ topics }) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-8">

      <h2 className="text-2xl font-bold text-slate-800 mb-6">
        Topics Covered
      </h2>

      <div className="flex flex-wrap gap-3">

        {topics.map((topic, index) => (

          <span
            key={index}
            className="
              bg-blue-100
              text-blue-700
              px-4
              py-2
              rounded-full
              font-medium
            "
          >
            {topic}
          </span>

        ))}

      </div>

    </div>
  );
}

export default Topics;