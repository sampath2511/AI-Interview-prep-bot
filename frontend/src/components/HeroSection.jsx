import React from "react";
import { motion } from "framer-motion";
import { BrainCircuit } from "lucide-react";

export default function HeroSection({ onTopicClick }) {
  const topics = ["System Design", "Python", "React", "Dynamic Programming"];

  return (
    <div className="flex flex-col items-center justify-center pt-20 pb-10 text-center px-4">
      <motion.div
        whileHover={{ scale: 1.05, rotate: 5 }}
        className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-xl shadow-fuchsia-500/30 mb-8"
      >
        <BrainCircuit className="w-10 h-10 text-white" />
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-5xl md:text-6xl font-extrabold tracking-tight mb-4"
      >
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-fuchsia-600">
          AI Interview Prep
        </span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="text-lg md:text-xl text-slate-600 max-w-2xl mb-8"
      >
        Your intelligent co-pilot for technical interviews. Enter any topic, and Gemini AI will curate the top questions, answers, and practice problems from the web.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="flex flex-wrap items-center justify-center gap-3"
      >
        <span className="text-sm font-medium text-slate-500 mr-2">Try examples:</span>
        {topics.map((topic) => (
          <button
            key={topic}
            onClick={() => onTopicClick(topic)}
            className="px-4 py-1.5 rounded-full text-sm font-medium bg-white/60 border border-slate-200 text-slate-700 hover:bg-violet-50 hover:text-violet-700 hover:border-violet-200 transition-all shadow-sm"
          >
            {topic}
          </button>
        ))}
      </motion.div>
    </div>
  );
}
