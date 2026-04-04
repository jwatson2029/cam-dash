"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import VideoInput from "@/components/VideoInput";
import ResultsCard from "@/components/ResultsCard";
import HistorySidebar from "@/components/HistorySidebar";
import { useAnalysisStore } from "@/lib/store";
import { Sparkles, Zap, Shield } from "lucide-react";

export default function Home() {
  const { currentResult, isLoading } = useAnalysisStore();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex min-h-screen">
      <HistorySidebar />
      <div className="flex-1 flex flex-col">
        {/* Hero Section */}
        <section className="relative overflow-hidden">
          {/* Background layers */}
          <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-purple-950/15 to-slate-950" />
          {/* Dot grid */}
          <div
            className="absolute inset-0 opacity-20"
            style={{
              backgroundImage:
                "radial-gradient(circle, rgb(100 60 180 / 0.4) 1px, transparent 1px)",
              backgroundSize: "32px 32px",
            }}
          />
          <div className="absolute inset-0">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-purple-500/8 rounded-full blur-3xl" />
            <div className="absolute top-20 right-1/4 w-[350px] h-[350px] bg-pink-500/6 rounded-full blur-3xl" />
          </div>

          <div className="relative z-10 container mx-auto px-4 pt-20 pb-16 max-w-4xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center"
            >
              {/* Badge */}
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm mb-8"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Real-time analytics · No login required</span>
              </motion.div>

              {/* Headline */}
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-5">
                <span className="text-slate-50">Get Real-Time</span>
                <br />
                <span className="gradient-text">TikTok Views &amp; Stats</span>
                <br />
                <span className="text-slate-50">in Seconds</span>
              </h1>

              {/* Subheadline */}
              <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
                Paste any public TikTok video URL and get instant analytics.{" "}
                <span className="text-slate-300">No login. No API keys.</span>
              </p>

              {/* Input */}
              <VideoInput inputRef={inputRef} />

              {/* Trust bar */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="flex items-center justify-center gap-6 mt-8 text-sm text-slate-500"
              >
                <div className="flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-green-500" />
                  <span>Works on any public video</span>
                </div>
                <div className="hidden sm:block w-px h-4 bg-slate-800" />
                <div className="hidden sm:flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                  <span>Updated April 2026</span>
                </div>
                <div className="hidden sm:block w-px h-4 bg-slate-800" />
                <div className="hidden sm:flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-yellow-400" />
                  <span>Powered by real-time scraping</span>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Results Section */}
        <section className="container mx-auto px-4 pb-20 max-w-5xl">
          <AnimatePresence mode="wait">
            {(currentResult || isLoading) && (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
              >
                <ResultsCard />
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      </div>
    </div>
  );
}
