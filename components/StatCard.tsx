"use client";

import { motion } from "framer-motion";
import { formatNumber } from "@/lib/utils";

interface StatCardProps {
  icon: string;
  label: string;
  value: number;
  delay?: number;
}

export default function StatCard({ icon, label, value, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      whileHover={{ scale: 1.02, y: -2 }}
      className="glass rounded-xl p-4 border border-slate-700/50 hover:border-purple-500/30 transition-all group cursor-default"
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{icon}</span>
        <span className="text-xs text-slate-500 font-medium uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-2xl font-bold text-slate-100 group-hover:text-white transition-colors">
        {formatNumber(value)}
      </p>
      <p className="text-xs text-slate-600 mt-1">{value.toLocaleString()} total</p>
    </motion.div>
  );
}
