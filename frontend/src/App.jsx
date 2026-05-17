import React, { useState } from "react";
import { AnimatePresence } from "framer-motion";
import HeroSection from "./components/HeroSection";
import InputSection from "./components/InputSection";
import LoadingScreen from "./components/LoadingScreen";
import ResultsDashboard from "./components/ResultsDashboard";
import { prepareInterview } from "./services/api";

function App() {
  const [topic, setTopic] = useState("");
  const [level, setLevel] = useState("beginner");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resultData, setResultData] = useState(null);

  const handleGenerate = async () => {
    setIsLoading(true);
    setError(null);
    setResultData(null);
    try {
      const data = await prepareInterview(topic, level);
      setResultData(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate material. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleTopicClick = (selectedTopic) => {
    setTopic(selectedTopic);
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-400/20 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob"></div>
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-fuchsia-400/20 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-32 left-1/2 w-96 h-96 bg-violet-400/20 rounded-full mix-blend-multiply filter blur-3xl opacity-70 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8">
        {!resultData && !isLoading && (
          <HeroSection onTopicClick={handleTopicClick} />
        )}

        <InputSection
          topic={topic}
          setTopic={setTopic}
          level={level}
          setLevel={setLevel}
          isLoading={isLoading}
          onGenerate={handleGenerate}
        />

        {error && (
          <div className="max-w-2xl mx-auto mb-8 p-4 bg-red-50 border border-red-200 text-red-600 rounded-2xl text-center shadow-sm">
            {error}
          </div>
        )}

        <AnimatePresence mode="wait">
          {isLoading && <LoadingScreen key="loading" />}
          {resultData && !isLoading && (
            <ResultsDashboard key="results" data={resultData} topic={topic} level={level} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;
