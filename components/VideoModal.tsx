"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, ExternalLink } from "lucide-react";
import Image from "next/image";

interface VideoModalProps {
  isOpen: boolean;
  onClose: () => void;
  thumbnailUrl: string;
  playUrl: string;
  videoId: string;
  authorId: string;
}

export default function VideoModal({
  isOpen,
  onClose,
  thumbnailUrl,
  playUrl,
  videoId,
  authorId,
}: VideoModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" />
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            onClick={(e) => e.stopPropagation()}
            className="relative z-10 w-full max-w-sm rounded-2xl overflow-hidden bg-slate-900 border border-slate-700 shadow-2xl"
          >
            {/* Close button */}
            <button
              onClick={onClose}
              className="absolute top-3 right-3 z-10 p-1.5 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
              aria-label="Close video"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Video / Thumbnail */}
            <div className="relative aspect-[9/16] w-full bg-slate-800">
              {playUrl ? (
                <video
                  src={playUrl}
                  controls
                  autoPlay
                  className="w-full h-full object-cover"
                  aria-label="TikTok video"
                />
              ) : thumbnailUrl ? (
                <Image
                  src={thumbnailUrl}
                  alt="Video thumbnail"
                  fill
                  className="object-cover"
                  unoptimized
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-500">
                  <p>Preview unavailable</p>
                </div>
              )}
            </div>

            {/* Open on TikTok */}
            <div className="p-3">
              <a
                href={`https://www.tiktok.com/@${authorId}/video/${videoId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-2 px-4 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-medium hover:from-purple-500 hover:to-pink-500 transition-all"
              >
                <ExternalLink className="w-4 h-4" />
                Open on TikTok
              </a>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
