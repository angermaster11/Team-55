import { useState, useRef } from "react";
import { motion, useInView, AnimatePresence } from "framer-motion";
import { FAQS } from "../data";

export default function FAQSection() {
  const [open, setOpen] = useState<number | null>(null);
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  const toggle = (i: number) => setOpen(open === i ? null : i);

  return (
    <section
      id="faq"
      ref={ref}
      className="py-24 px-6 bg-base"
    >
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <motion.div
          className="text-center mb-14"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-xs font-semibold tracking-widest uppercase mb-4 block font-mono text-coral">
            FAQ
          </span>
          <h2
            className="text-4xl md:text-5xl font-black font-mono text-snow"
            style={{ letterSpacing: "-0.02em" }}
          >
            Got questions?
          </h2>
        </motion.div>

        {/* Accordion */}
        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="rounded-2xl overflow-hidden bg-card transition-all duration-200"
              style={{
                border:
                  open === i
                    ? "1px solid rgba(255,107,53,0.3)"
                    : "1px solid rgba(255,255,255,0.05)",
              }}
            >
              {/* Question Row */}
              <button
                className="w-full text-left px-6 py-5 flex items-center justify-between gap-4"
                onClick={() => toggle(i)}
              >
                <span className="font-semibold text-sm font-mono text-snow">
                  {faq.q}
                </span>
                <motion.div
                  animate={{ rotate: open === i ? 45 : 0 }}
                  transition={{ duration: 0.25 }}
                  className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-lg font-light transition-colors duration-200"
                  style={{
                    background:
                      open === i ? "#FF6B35" : "rgba(255,255,255,0.07)",
                    color: open === i ? "#0A0E1A" : "#6B7280",
                  }}
                >
                  +
                </motion.div>
              </button>

              {/* Answer */}
              <AnimatePresence initial={false}>
                {open === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="px-6 pb-5 pt-4 text-sm leading-relaxed font-serif text-muted border-t border-white/[0.05]">
                      {faq.a}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
