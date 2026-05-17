import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ExternalLink, CheckCircle2, Circle, Copy, Check } from "lucide-react";

const getLevelColor = (level) => {
  if (!level) return "bg-slate-100 text-slate-700 border-slate-200";
  switch (level.toLowerCase()) {
    case "beginner":
      return "bg-green-100 text-green-700 border-green-200";
    case "intermediate":
      return "bg-yellow-100 text-yellow-700 border-yellow-200";
    case "senior":
    case "advanced":
      return "bg-fuchsia-100 text-fuchsia-700 border-fuchsia-200";
    default:
      return "bg-slate-100 text-slate-700 border-slate-200";
  }
};

const getDifficultyColor = (diff) => {
  if (!diff) return "bg-slate-100 text-slate-700";
  const d = diff.toLowerCase();
  if (d.includes("easy")) return "bg-green-100 text-green-700";
  if (d.includes("medium")) return "bg-yellow-100 text-yellow-700";
  if (d.includes("hard")) return "bg-red-100 text-red-700";
  return "bg-slate-100 text-slate-700";
};

export default function ResultsDashboard({ data }) {
  const [openQ, setOpenQ] = useState(0);
  const [doneProblems, setDoneProblems] = useState(new Set());
  const [copiedLink, setCopiedLink] = useState(null);

  const { questions = [], coding_problems = [], sources = [], topic = "Your Topic", level = "Beginner" } = data;

  const toggleProblem = (index) => {
    const newDone = new Set(doneProblems);
    if (newDone.has(index)) {
      newDone.delete(index);
    } else {
      newDone.add(index);
    }
    setDoneProblems(newDone);
  };

  const copyToClipboard = (url) => {
    navigator.clipboard.writeText(url);
    setCopiedLink(url);
    setTimeout(() => setCopiedLink(null), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-5xl mx-auto pb-20"
    >
      {/* SECTION A: HEADER */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-12">
        <h2 className="text-3xl font-bold text-slate-800">
          Interview Guide: <span className="text-violet-600">{topic}</span>
        </h2>
        <span className={`px-4 py-1.5 rounded-full border font-semibold text-sm capitalize ${getLevelColor(level)}`}>
          {level} Level
        </span>
      </div>

      {/* SECTION B: QUESTIONS */}
      <div className="mb-16">
        <h3 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
          <div className="w-2 h-6 bg-fuchsia-500 rounded-full"></div>
          Top Technical Questions
        </h3>
        <div className="space-y-4">
          {questions.map((q, idx) => (
            <div key={idx} className="glass rounded-2xl overflow-hidden transition-all">
              <button
                onClick={() => setOpenQ(openQ === idx ? -1 : idx)}
                className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-slate-50/50 transition-colors"
              >
                <div className="flex items-center gap-4 pr-4">
                  <span className="flex-shrink-0 w-8 h-8 rounded-full bg-fuchsia-100 text-fuchsia-600 flex items-center justify-center font-bold text-sm">
                    Q{idx + 1}
                  </span>
                  <span className="font-semibold text-slate-800 text-lg">{q.question}</span>
                </div>
                <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${openQ === idx ? "rotate-180" : ""}`} />
              </button>
              <AnimatePresence>
                {openQ === idx && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="px-6 pb-6 pt-2">
                      <div className="bg-slate-50/80 rounded-xl p-5 border-l-4 border-violet-500 text-slate-700 leading-relaxed">
                        <p className="mb-3">{q.answer}</p>
                        {q.source && (
                          <a
                            href={q.source}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-sm font-medium text-violet-600 hover:text-violet-800 transition-colors"
                          >
                            Read original source <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
          {questions.length === 0 && (
            <div className="text-slate-500 italic p-4 text-center border border-dashed rounded-xl border-slate-300">
              No questions generated.
            </div>
          )}
        </div>
      </div>

      {/* SECTION C: CODING PROBLEMS */}
      <div className="mb-16">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <div className="w-2 h-6 bg-violet-500 rounded-full"></div>
            Recommended Practice
          </h3>
          <span className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
            {doneProblems.size} / {coding_problems.length} Done
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {coding_problems.map((prob, idx) => {
            const isDone = doneProblems.has(idx);
            
            return (
              <motion.div
                whileHover={{ y: -2 }}
                key={idx}
                className={`p-5 rounded-2xl border transition-all flex flex-col ${
                  isDone 
                    ? "bg-green-50/50 border-green-200" 
                    : "glass border-white/40"
                }`}
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 block">
                      {prob.platform || "Practice"}
                    </span>
                    <h4 className={`font-semibold text-lg ${isDone ? "text-slate-500 line-through" : "text-slate-800"}`}>
                      {prob.title}
                    </h4>
                  </div>
                  <button onClick={() => toggleProblem(idx)} className="mt-1 flex-shrink-0 text-slate-400 hover:text-green-500 transition-colors">
                    {isDone ? <CheckCircle2 className="w-6 h-6 text-green-500" /> : <Circle className="w-6 h-6" />}
                  </button>
                </div>
                
                <div className="flex items-center justify-between mt-auto pt-4 border-t border-slate-100">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-md ${getDifficultyColor(prob.difficulty)}`}>
                    {prob.difficulty || "Medium"}
                  </span>
                  {prob.link && (
                    <a
                      href={prob.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-violet-600 flex items-center gap-1 hover:text-violet-800 transition-colors"
                    >
                      Solve <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </motion.div>
            );
          })}
          {coding_problems.length === 0 && (
            <div className="col-span-1 md:col-span-2 text-slate-500 italic p-4 text-center border border-dashed rounded-xl border-slate-300">
              No coding problems generated.
            </div>
          )}
        </div>
      </div>

      {/* SECTION D: SOURCES */}
      <div className="glass-dark rounded-3xl overflow-hidden border-t-4 border-t-fuchsia-500">
        <div className="p-8">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            Verified AI Sources
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sources.map((source, idx) => (
              <div key={idx} className="flex items-center justify-between bg-slate-800/50 p-3 rounded-xl border border-slate-700/50 hover:bg-slate-800 transition-colors group">
                <a 
                  href={source} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-slate-300 text-sm truncate mr-4 hover:text-fuchsia-400 transition-colors"
                >
                  {source}
                </a>
                <button 
                  onClick={() => copyToClipboard(source)}
                  className="p-2 bg-slate-700/50 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors flex-shrink-0"
                >
                  {copiedLink === source ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            ))}
            {sources.length === 0 && (
              <div className="text-slate-400 italic text-sm">No sources available.</div>
            )}
          </div>
        </div>
      </div>

    </motion.div>
  );
}
