"use client";

import Link from "next/link";
import { Music2, Activity, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

export default function Navbar() {
  return (
    <motion.nav
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky top-0 z-50 w-full border-b border-slate-800/50 bg-slate-950/90 backdrop-blur-xl"
    >
      <div className="container mx-auto px-4 h-14 flex items-center justify-between max-w-7xl">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg shadow-purple-500/25">
            <Music2 className="w-4 h-4 text-white" />
            <Activity className="w-2 h-2 text-white absolute -bottom-0.5 -right-0.5" />
          </div>
          <span className="font-semibold text-slate-100 group-hover:text-white transition-colors text-base">
            TikTok Pulse
          </span>
        </Link>

        {/* Right side — live indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/60 border border-slate-800">
          <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-xs text-slate-400 font-medium hidden sm:block">
            Real-time analytics
          </span>
          <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
        </div>
      </div>
    </motion.nav>
  );
}
