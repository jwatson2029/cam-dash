"use client";

import Link from "next/link";
import { GitFork, Music2, Activity } from "lucide-react";
import { motion } from "framer-motion";

export default function Navbar() {
  return (
    <motion.nav
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky top-0 z-50 w-full border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-xl"
    >
      <div className="container mx-auto px-4 h-14 flex items-center justify-between max-w-7xl">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg shadow-purple-500/25">
            <Music2 className="w-4 h-4 text-white" />
            <Activity className="w-2 h-2 text-white absolute -bottom-0.5 -right-0.5" />
          </div>
          <span className="font-semibold text-slate-100 group-hover:text-white transition-colors">
            TikTok Pulse
          </span>
        </Link>

        {/* Center links */}
        <div className="hidden md:flex items-center gap-1">
          {[
            { href: "/", label: "Dashboard" },
            { href: "#", label: "History" },
            { href: "#", label: "Docs" },
            { href: "https://github.com", label: "GitHub" },
          ].map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="px-3 py-1.5 text-sm text-slate-400 hover:text-slate-100 rounded-md hover:bg-slate-800/50 transition-all"
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          <span className="hidden lg:block text-sm text-slate-500">
            Made with ❤️ for TikTok creators
          </span>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-300 rounded-lg border border-slate-700 hover:border-slate-500 hover:text-white transition-all bg-slate-900/50 hover:bg-slate-800/50"
          >
            <GitFork className="w-4 h-4" />
            <span className="hidden sm:block">Star</span>
          </a>
        </div>
      </div>
    </motion.nav>
  );
}
