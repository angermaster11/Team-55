import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { STEPS } from "../data";

export default function HowItWorksSection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      id="how-it-works"
      ref={ref}
      className="py-24 px-6 bg-base"
    >
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-xs font-semibold tracking-widest uppercase mb-4 block font-mono text-violet">
            How It Works
          </span>
          <h2
            className="text-4xl md:text-5xl font-black font-mono text-snow"
            style={{ letterSpacing: "-0.02em" }}
          >
            Four steps to perfect code.
          </h2>
        </motion.div>

        {/* Steps */}
        <div className="relative">
          {/* Center vertical line */}
          <div
            className="hidden md:block absolute left-1/2 top-0 bottom-0 w-px -translate-x-1/2"
            style={{
              background:
                "linear-gradient(to bottom, transparent, rgba(123,97,255,0.25), transparent)",
            }}
          />

          <div className="flex flex-col gap-10">
            {STEPS.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, x: i % 2 === 0 ? -40 : 40 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.6, delay: i * 0.15 }}
                className={`flex items-center gap-8 ${
                  i % 2 !== 0 ? "md:flex-row-reverse" : ""
                }`}
              >
                {/* Text side */}
                <div
                  className={`flex-1 ${
                    i % 2 === 0 ? "md:text-right" : "md:text-left"
                  }`}
                >
                  <div className="text-xs font-bold tracking-widest mb-1 font-mono text-violet">
                    {step.num}
                  </div>
                  <h3 className="text-xl font-bold mb-1 font-mono text-snow">
                    {step.title}
                  </h3>
                  <p className="text-sm font-serif text-muted">{step.desc}</p>
                </div>

                {/* Node */}
                <div
                  className="relative z-10 w-14 h-14 rounded-full flex items-center justify-center font-black text-sm flex-shrink-0 font-mono text-base bg-gradient-brand glow-violet"
                >
                  {step.num}
                </div>

                <div className="flex-1 hidden md:block" />
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
