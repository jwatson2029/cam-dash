"use client";

import { useState, RefObject } from "react";
import { motion } from "framer-motion";
import { Search, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useAnalysisStore } from "@/lib/store";
import { clientScrapeVideo } from "@/lib/client-scraper";
import type { VideoData } from "@/lib/scraper";

const EXAMPLE_URL = "https://www.tiktok.com/@fcs.schools/video/7624733171023695118";

interface VideoInputProps {
  inputRef?: RefObject<HTMLInputElement | null>;
}

async function fetchFromServer(url: string): Promise<VideoData> {
  const res = await fetch("/api/scrape", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
    signal: AbortSignal.timeout(15000),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error || "Server fetch failed");
  }
  return res.json();
}

export default function VideoInput({ inputRef }: VideoInputProps) {
  const [url, setUrl] = useState("");
  const { isLoading, setLoading, setCurrentResult, setError, addToHistory } =
    useAnalysisStore();

  const analyze = async (targetUrl: string) => {
    const trimmed = targetUrl.trim();
    if (!trimmed) {
      toast.error("Please enter a TikTok URL");
      return;
    }

    if (!trimmed.includes("tiktok.com")) {
      toast.error("Please enter a valid TikTok URL");
      return;
    }

    // Strict URL hostname validation to prevent SSRF-style bypasses
    let parsedUrl: URL;
    try {
      parsedUrl = new URL(trimmed);
    } catch {
      toast.error("Please enter a valid URL");
      return;
    }
    if (!parsedUrl.hostname.endsWith("tiktok.com") && parsedUrl.hostname !== "tiktok.com") {
      toast.error("Please enter a valid TikTok URL");
      return;
    }

    setLoading(true);
    try {
      let data: VideoData;

      // Try the server-side API route first (richer data, avoids CORS).
      // Falls back to client scraper if the route is unavailable (static export).
      try {
        data = await fetchFromServer(trimmed);
      } catch {
        data = await clientScrapeVideo(trimmed);
      }

      setCurrentResult(data, trimmed);
      addToHistory(trimmed, data);
      toast.success("Analysis complete!", {
        description: `@${data.author.uniqueId} · ${data.stats.playCount.toLocaleString()} views`,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setError(message);
      toast.error(message);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <motion.div
        className="relative group"
        transition={{ type: "spring", stiffness: 300 }}
      >
        {/* Glow effect */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500/30 to-pink-500/30 rounded-xl blur opacity-0 group-focus-within:opacity-100 transition-opacity duration-300" />

        <div className="relative flex gap-2 p-2 bg-slate-900 border border-slate-700 group-focus-within:border-purple-500/50 rounded-xl transition-colors">
          <div className="flex-1 flex items-center gap-2 px-2">
            <Search className="w-4 h-4 text-slate-500 flex-shrink-0" />
            <input
              ref={inputRef}
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && analyze(url)}
              placeholder="https://www.tiktok.com/@username/video/..."
              className="flex-1 bg-transparent text-slate-200 placeholder:text-slate-600 text-sm outline-none min-w-0"
              disabled={isLoading}
              aria-label="TikTok video URL"
            />
          </div>
          <motion.button
            onClick={() => analyze(url)}
            disabled={isLoading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white text-sm font-medium transition-all shadow-lg shadow-purple-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span>{isLoading ? "Analyzing..." : "Analyze"}</span>
          </motion.button>
        </div>
      </motion.div>

      {/* Try Example */}
      <div className="flex justify-center mt-3">
        <button
          onClick={() => {
            setUrl(EXAMPLE_URL);
            analyze(EXAMPLE_URL);
          }}
          disabled={isLoading}
          className="text-xs text-slate-500 hover:text-purple-400 transition-colors underline-offset-2 hover:underline disabled:opacity-50"
        >
          ✨ Try Example Video
        </button>
      </div>

      {/* Keyboard shortcut hint */}
      <p className="text-center text-xs text-slate-600 mt-2">
        Press{" "}
        <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 text-xs">
          ⌘K
        </kbd>{" "}
        to focus
      </p>
    </div>
  );
}
