function Loader() {
  return (
    <div className="flex flex-col items-center mt-10">

      <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>

      <p className="mt-4 text-blue-600 font-medium">
        Generating AI Summary...
      </p>

    </div>
  );
}

export default Loader;