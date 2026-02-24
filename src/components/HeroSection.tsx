import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { HERO_WORDS, STATS } from "../data";
import GitHubIcon from "./GitHubIcon";
import TerminalPreview from "./TerminalPreview";

export default function HeroSection() {
  const [wordIdx, setWordIdx] = useState<number>(0);

  useEffect(() => {
    const id = setInterval(
      () => setWordIdx((i) => (i + 1) % HERO_WORDS.length),
      2300
    );
    return () => clearInterval(id);
  }, []);

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-6 pt-24 pb-16 bg-base">
      {/* Grid background */}
      <div className="absolute inset-0 grid-bg opacity-100 pointer-events-none" />

      {/* Glow blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-3xl opacity-20 pointer-events-none bg-violet" />
      <div className="absolute bottom-1/4 right-1/4 w-72 h-72 rounded-full blur-3xl opacity-15 pointer-events-none bg-mint" />
      <div className="absolute top-1/3 right-1/3 w-48 h-48 rounded-full blur-3xl opacity-10 pointer-events-none bg-coral" />

      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-6 flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium border border-mint/25 bg-mint/[0.08] text-mint font-mono"
      >
        <span className="w-2 h-2 rounded-full bg-mint animate-pulse2" />
        AI-Powered Code Correction Platform
      </motion.div>

      {/* Headline */}
      <motion.h1
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="text-center font-black leading-none mb-4 font-mono text-snow"
        style={{
          fontSize: "clamp(2.8rem, 7vw, 6rem)",
          letterSpacing: "-0.02em",
        }}
      >
        Your Code,
        <br />
        <AnimatePresence mode="wait">
          <motion.span
            key={wordIdx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
            className="text-gradient-mint"
          >
            {HERO_WORDS[wordIdx]}
          </motion.span>
        </AnimatePresence>
      </motion.h1>

      {/* Subheading */}
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="text-center max-w-2xl mb-10 text-base leading-relaxed text-muted font-serif"
      >
        Connect your GitHub repository and let our AI engine scan, diagnose, and
        auto-fix bugs, vulnerabilities, and code smells — then open a pull
        request with every correction applied.
      </motion.p>

      {/* CTA Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.65 }}
        className="flex flex-col sm:flex-row gap-4 items-center"
      >
        <motion.button
          className="flex items-center gap-3 px-7 py-3.5 rounded-xl text-sm font-bold font-mono bg-gradient-brand text-base glow-mint"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.97 }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.boxShadow =
              "0 0 48px rgba(0,255,178,0.45)")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.boxShadow =
              "0 0 32px rgba(0,255,178,0.25)")
          }
        >
          <GitHubIcon size={18} />
          Continue with GitHub
        </motion.button>

        <motion.button
          className="px-7 py-3.5 rounded-xl text-sm font-semibold font-mono border border-violet/40 text-snow bg-transparent hover:border-violet hover:bg-violet/[0.08] transition-all duration-200"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          Watch Demo →
        </motion.button>
      </motion.div>

      {/* Terminal */}
      <TerminalPreview />

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.1 }}
        className="mt-14 grid grid-cols-3 gap-8 text-center"
      >
        {STATS.map((s) => (
          <div key={s.label}>
            <div className="text-2xl font-black font-mono text-gradient-mint">
              {s.val}
            </div>
            <div className="text-xs mt-1 text-slate font-mono">{s.label}</div>
          </div>
        ))}
      </motion.div>
    </section>
  );
}
