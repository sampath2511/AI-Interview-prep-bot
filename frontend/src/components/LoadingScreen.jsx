import React from "react";
import { motion } from "framer-motion";

export default function LoadingScreen() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="w-full flex flex-col items-center justify-center py-20"
    >
      <div className="relative w-24 h-24 mb-8">
        <div className="absolute inset-0 rounded-full border-4 border-pink-100"></div>
        <div className="absolute inset-0 rounded-full border-4 border-fuchsia-500 border-t-transparent animate-spin-slow"></div>
        <div className="absolute inset-2 rounded-full border-4 border-fuchsia-200 border-b-transparent animate-spin"></div>
      </div>

      <motion.h2
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-fuchsia-600 mb-2 text-center"
      >
        Scraping GeeksforGeeks & LeetCode...
      </motion.h2>

      <motion.p
        animate={{ opacity: [0.4, 0.8, 0.4] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
        className="text-slate-500 text-center"
      >
        Gemini is summarizing the best answers.
      </motion.p>
    </motion.div>
  );
}
