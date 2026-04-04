"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Copy, Share2, Download, RefreshCw, Play, Music2, Eye, Wifi, WifiOff, Info } from "lucide-react";
import { toast } from "sonner";
import Image from "next/image";
import { useAnalysisStore } from "@/lib/store";
import StatCard from "./StatCard";
import AnimatedCounter from "./AnimatedCounter";
import VideoModal from "./VideoModal";
import { timeAgo } from "@/lib/utils";

function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 animate-pulse">
      <div className="flex gap-6">
        <div className="w-36 h-48 rounded-xl bg-slate-800 flex-shrink-0" />
        <div className="flex-1 space-y-4">
          <div className="h-6 bg-slate-800 rounded w-3/4" />
          <div className="h-4 bg-slate-800 rounded w-1/2" />
          <div className="h-16 bg-slate-800 rounded w-full" />
          <div className="grid grid-cols-4 gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-slate-800 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

type DataSource = "live" | "oembed" | "generated";

const DATA_SOURCE_CONFIG: Record<DataSource, { label: string; description: string; className: string; icon: React.ReactNode }> = {
  live: {
    label: "Live Data",
    description: "Stats fetched directly from TikTok",
    className: "text-green-400 bg-green-500/10 border-green-500/30",
    icon: <Wifi className="w-3 h-3" />,
  },
  oembed: {
    label: "Partial Data",
    description: "Real title & thumbnail · stats are estimated",
    className: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
    icon: <Info className="w-3 h-3" />,
  },
  generated: {
    label: "Estimated",
    description: "Could not reach TikTok — all data is generated",
    className: "text-slate-400 bg-slate-500/10 border-slate-600/50",
    icon: <WifiOff className="w-3 h-3" />,
  },
};

export default function ResultsCard() {
  const { currentResult, currentUrl, isLoading, reset } = useAnalysisStore();
  const [modalOpen, setModalOpen] = useState(false);

  if (isLoading) return <SkeletonCard />;
  if (!currentResult) return null;

  const { id, desc, createTime, video, author, stats, music, hashtags, dataSource } = currentResult;
  const sourceConfig = DATA_SOURCE_CONFIG[dataSource ?? "generated"];

  const copyJSON = () => {
    navigator.clipboard.writeText(JSON.stringify(currentResult, null, 2));
    toast.success("JSON copied to clipboard!");
  };

  const copyLink = () => {
    navigator.clipboard.writeText(currentUrl);
    toast.success("Link copied!");
  };

  const exportCSV = () => {
    const rows = [
      ["Metric", "Value"],
      ["Video ID", id],
      ["Author", `@${author.uniqueId}`],
      ["Description", desc.replace(/,/g, ";")],
      ["Views", stats.playCount],
      ["Likes", stats.diggCount],
      ["Comments", stats.commentCount],
      ["Shares", stats.shareCount],
      ["Saves", stats.collectCount],
      ["Music", music.title],
      ["Hashtags", hashtags.join(" ")],
    ];
    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tiktok-${id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("CSV exported!");
  };

  const shareOnX = () => {
    const text = encodeURIComponent(
      `TikTok by @${author.uniqueId}: ${stats.playCount.toLocaleString()} views! Check it out →`
    );
    window.open(
      `https://twitter.com/intent/tweet?text=${text}&url=${encodeURIComponent(currentUrl)}`,
      "_blank"
    );
  };

  return (
    <>
      <motion.div
        layout
        className="rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-slate-800/50 bg-slate-900/30">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-sm text-slate-400">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span>Analysis complete</span>
            </div>
            {/* Data source badge */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${sourceConfig.className}`}
              title={sourceConfig.description}
            >
              {sourceConfig.icon}
              {sourceConfig.label}
            </div>
          </div>
          <button
            onClick={reset}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            New Search
          </button>
        </div>

        <div className="p-6">
          <div className="flex flex-col sm:flex-row gap-6">
            {/* Thumbnail */}
            <div className="flex-shrink-0">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setModalOpen(true)}
                className="relative w-full sm:w-36 h-52 sm:h-52 rounded-xl overflow-hidden bg-slate-800 group cursor-pointer shadow-lg"
                aria-label="Play video"
              >
                {video.thumbnailUrl ? (
                  <Image
                    src={video.thumbnailUrl}
                    alt="Video thumbnail"
                    fill
                    className="object-cover"
                    unoptimized
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-purple-800 to-pink-800" />
                )}
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center ring-2 ring-white/20">
                    <Play className="w-5 h-5 text-white ml-0.5" fill="white" />
                  </div>
                </div>
              </motion.button>
            </div>

            {/* Main content */}
            <div className="flex-1 min-w-0">
              {/* Author */}
              <div className="flex items-center gap-3 mb-4">
                <div className="relative w-10 h-10 rounded-full overflow-hidden bg-slate-700 flex-shrink-0 ring-2 ring-slate-700">
                  {author.avatarUrl ? (
                    <Image
                      src={author.avatarUrl}
                      alt={author.nickname}
                      fill
                      className="object-cover"
                      unoptimized
                    />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center text-white font-bold text-sm">
                      {author.nickname.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>
                <div>
                  <p className="font-semibold text-slate-100 leading-tight">{author.nickname}</p>
                  <p className="text-sm text-slate-500">@{author.uniqueId}</p>
                </div>
                <div className="ml-auto text-xs text-slate-600 shrink-0">
                  Posted {timeAgo(createTime)}
                </div>
              </div>

              {/* View count hero */}
              <div className="flex items-center gap-4 mb-4 p-4 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20">
                <Eye className="w-5 h-5 text-purple-400 flex-shrink-0" />
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-0.5">Total Views</p>
                  <p className="text-3xl font-bold gradient-text leading-none">
                    <AnimatedCounter value={stats.playCount} />
                  </p>
                </div>
              </div>

              {/* Description */}
              <p className="text-sm text-slate-400 line-clamp-2 mb-3 leading-relaxed">{desc}</p>

              {/* Hashtags */}
              {hashtags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {hashtags.slice(0, 6).map((tag) => (
                    <a
                      key={tag}
                      href={`https://www.tiktok.com/tag/${tag}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20 hover:bg-purple-500/20 transition-colors"
                    >
                      #{tag}
                    </a>
                  ))}
                </div>
              )}

              {/* Music */}
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Music2 className="w-3.5 h-3.5 text-pink-400 flex-shrink-0" />
                <span className="truncate">{music.title}</span>
                {music.authorName && (
                  <span className="text-slate-600 flex-shrink-0">• {music.authorName}</span>
                )}
              </div>
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
            <StatCard icon="❤️" label="Likes" value={stats.diggCount} delay={0.1} />
            <StatCard icon="💬" label="Comments" value={stats.commentCount} delay={0.2} />
            <StatCard icon="🔗" label="Shares" value={stats.shareCount} delay={0.3} />
            <StatCard icon="📌" label="Saves" value={stats.collectCount} delay={0.4} />
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2 mt-5 pt-4 border-t border-slate-800/50">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={copyJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 rounded-lg border border-slate-700 hover:border-slate-500 transition-all bg-slate-800/50"
            >
              <Copy className="w-3.5 h-3.5" />
              Copy JSON
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={copyLink}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 rounded-lg border border-slate-700 hover:border-slate-500 transition-all bg-slate-800/50"
            >
              <Copy className="w-3.5 h-3.5" />
              Copy Link
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={shareOnX}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 rounded-lg border border-slate-700 hover:border-slate-500 transition-all bg-slate-800/50"
            >
              <Share2 className="w-3.5 h-3.5" />
              Share on X
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={exportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 rounded-lg border border-slate-700 hover:border-slate-500 transition-all bg-slate-800/50"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </motion.button>
          </div>
        </div>
      </motion.div>

      <VideoModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        thumbnailUrl={video.thumbnailUrl}
        playUrl={video.playUrl}
        videoId={id}
        authorId={author.uniqueId}
      />
    </>
  );
}
