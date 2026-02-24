import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { FEATURES } from "../data";

export default function FeaturesSection() {
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      id="features"
      ref={ref}
      className="py-24 px-6 bg-surface"
    >
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <span className="text-xs font-semibold tracking-widest uppercase mb-4 block font-mono text-mint">
            Features
          </span>
          <h2
            className="text-4xl md:text-5xl font-black font-mono text-snow"
            style={{ letterSpacing: "-0.02em" }}
          >
            Everything your code needs.
          </h2>
          <p className="mt-4 text-base max-w-xl mx-auto text-muted font-serif">
            From surface-level linting to deep architectural review — FixFlow AI
            covers the full spectrum of code quality.
          </p>
        </motion.div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="p-6 rounded-2xl relative overflow-hidden group cursor-default bg-card card-border transition-all duration-300"
              style={
                {
                  "--feature-color": feature.color,
                } as React.CSSProperties
              }
              whileHover={{
                borderColor: feature.color + "40",
                boxShadow: `0 0 32px ${feature.color}12`,
              }}
            >
              {/* Hover glow blob */}
              <div
                className="absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-0 group-hover:opacity-20 transition-opacity duration-500 pointer-events-none"
                style={{ background: feature.color }}
              />

              {/* Icon */}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-4"
                style={{ background: feature.color + "18" }}
              >
                {feature.icon}
              </div>

              <h3 className="text-lg font-bold mb-2 font-mono text-snow">
                {feature.title}
              </h3>
              <p className="text-sm leading-relaxed text-muted font-serif">
                {feature.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
