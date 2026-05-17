import React from "react";
import { motion } from "framer-motion";
import { Search, Loader2 } from "lucide-react";

export default function InputSection({ topic, setTopic, level, setLevel, isLoading, onGenerate }) {
  const levels = ["Beginner", "Intermediate", "Senior"];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim() && !isLoading) {
      onGenerate();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="w-full max-w-3xl mx-auto px-4 mb-16"
    >
      <form onSubmit={handleSubmit} className="glass rounded-3xl p-4 flex flex-col md:flex-row items-center gap-4 relative z-10">
        <div className="flex-1 w-full relative">
          <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-slate-400" />
          </div>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="React, System Design..."
            disabled={isLoading}
            className="w-full pl-12 pr-4 py-4 rounded-2xl bg-slate-50/50 border border-slate-200 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all text-lg disabled:opacity-50"
          />
        </div>

        <div className="w-full md:w-auto min-w-[160px]">
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            disabled={isLoading}
            className="w-full px-4 py-4 rounded-2xl bg-slate-50/50 border border-slate-200 text-slate-800 focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all text-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2364748b'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
              backgroundRepeat: "no-repeat",
              backgroundPosition: "right 1rem center",
              backgroundSize: "1.5em 1.5em",
            }}
          >
            {levels.map((lvl) => (
              <option key={lvl} value={lvl.toLowerCase()}>
                {lvl}
              </option>
            ))}
          </select>
        </div>

        <motion.button
          whileHover={!isLoading ? { scale: 1.02 } : {}}
          whileTap={!isLoading ? { scale: 0.98 } : {}}
          type="submit"
          disabled={isLoading || !topic.trim()}
          className="w-full md:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold text-lg flex items-center justify-center gap-2 shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Preparing...
            </>
          ) : (
            <>
              Generate
            </>
          )}
        </motion.button>
      </form>
    </motion.div>
  );
}
