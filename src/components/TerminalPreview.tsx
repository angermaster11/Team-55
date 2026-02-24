import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TERMINAL_LINES } from "../data";

export default function TerminalPreview() {
  const [visible, setVisible] = useState<number>(0);

  useEffect(() => {
    if (visible >= TERMINAL_LINES.length) return;
    const id = setTimeout(() => setVisible((v) => v + 1), 380);
    return () => clearTimeout(id);
  }, [visible]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 40, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: 0.85, duration: 0.7 }}
      className="mt-16 w-full max-w-3xl rounded-2xl overflow-hidden card-border-mint"
      style={{
        boxShadow:
          "0 0 60px rgba(0,255,178,0.07), 0 40px 80px rgba(0,0,0,0.5)",
      }}
    >
      {/* Terminal Header */}
      <div className="flex items-center gap-2 px-4 py-3 bg-card border-b border-mint/10">
        <div className="w-3 h-3 rounded-full bg-coral" />
        <div className="w-3 h-3 rounded-full bg-yellow-400" />
        <div className="w-3 h-3 rounded-full bg-mint" />
        <span className="ml-3 text-xs text-snow/30 font-mono">
          fixflowai — analysis
        </span>
      </div>

      {/* Terminal Body */}
      <div className="p-6 bg-surface font-mono text-xs leading-relaxed min-h-[180px]">
        {TERMINAL_LINES.slice(0, visible).map((line, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
            className="mb-1"
            style={{ color: line.color }}
          >
            {line.text}
          </motion.div>
        ))}
        {visible < TERMINAL_LINES.length && (
          <span className="text-mint animate-blink">█</span>
        )}
      </div>
    </motion.div>
  );
}
