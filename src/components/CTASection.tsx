import { motion } from "framer-motion";
import GitHubIcon from "./GitHubIcon";

export default function CTASection() {
  return (
    <section className="py-24 px-6 relative overflow-hidden bg-surface">
      {/* Glow */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full blur-3xl opacity-15 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse, #00FFB2 0%, #7B61FF 60%, transparent 100%)",
        }}
      />

      <div className="max-w-3xl mx-auto text-center relative">
        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-4xl md:text-5xl font-black mb-5 font-mono text-snow"
          style={{ letterSpacing: "-0.02em" }}
        >
          Start fixing your code{" "}
          <span className="text-gradient-coral">today.</span>
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-base mb-10 text-muted font-serif"
        >
          Free for public repositories. No credit card required.
        </motion.p>

        <motion.button
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="inline-flex items-center gap-3 px-8 py-4 rounded-xl text-sm font-bold font-mono bg-gradient-brand text-base glow-mint"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.97 }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.boxShadow =
              "0 0 64px rgba(0,255,178,0.5)")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.boxShadow =
              "0 0 32px rgba(0,255,178,0.3)")
          }
        >
          <GitHubIcon size={18} />
          Get Started Free with GitHub
        </motion.button>
      </div>
    </section>
  );
}
