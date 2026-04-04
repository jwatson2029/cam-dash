"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Clock, Trash2, ChevronRight } from "lucide-react";
import { useAnalysisStore } from "@/lib/store";
import { timeAgo, formatNumber } from "@/lib/utils";
import Image from "next/image";

export default function HistorySidebar() {
  const { history, loadFromHistory, clearHistory } = useAnalysisStore();

  if (history.length === 0) return null;

  return (
    <motion.aside
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="hidden lg:flex flex-col w-64 xl:w-72 min-h-screen border-r border-slate-800/50 bg-slate-950/50 p-4 gap-3 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Clock className="w-4 h-4" />
          <span className="font-medium">Recent Analyses</span>
        </div>
        <button
          onClick={clearHistory}
          className="p-1 rounded-md text-slate-600 hover:text-slate-400 hover:bg-slate-800 transition-all"
          aria-label="Clear history"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="flex flex-col gap-2">
        <AnimatePresence>
          {history.map((record, i) => (
            <motion.button
              key={record.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => loadFromHistory(record)}
              className="group flex items-center gap-3 p-2.5 rounded-xl border border-slate-800 hover:border-slate-600 bg-slate-900/30 hover:bg-slate-800/50 text-left transition-all w-full"
            >
              {/* Thumbnail */}
              <div className="relative w-10 h-14 rounded-lg overflow-hidden bg-slate-800 flex-shrink-0">
                {record.data.video.thumbnailUrl ? (
                  <Image
                    src={record.data.video.thumbnailUrl}
                    alt=""
                    fill
                    className="object-cover"
                    unoptimized
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-purple-800 to-pink-800" />
                )}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-300 group-hover:text-white truncate transition-colors">
                  @{record.data.author.uniqueId}
                </p>
                <p className="text-xs text-slate-500 truncate">
                  {formatNumber(record.data.stats.playCount)} views
                </p>
                <p className="text-xs text-slate-600 mt-0.5">
                  {timeAgo(record.analyzedAt / 1000)}
                </p>
              </div>

              <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400 flex-shrink-0 transition-colors" />
            </motion.button>
          ))}
        </AnimatePresence>
      </div>
    </motion.aside>
  );
}
