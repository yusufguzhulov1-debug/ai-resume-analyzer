import UploadResume from "../components/UploadResume";

function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-10">
      
      <h1 className="text-5xl font-bold mb-4">
        AI Resume Analyzer
      </h1>

      <p className="text-gray-400 mb-10 text-center max-w-xl">
        Analyze your resume, improve ATS score and get AI-powered career recommendations.
      </p>

      <UploadResume />

    </div>
  );
}

export default App;