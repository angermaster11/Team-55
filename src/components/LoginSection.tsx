import { motion } from "framer-motion";
import GitHubIcon from "./GitHubIcon";

export default function LoginSection() {
  return (
    <section
      id="login"
      className="py-24 px-6 relative overflow-hidden bg-surface"
    >
      {/* Grid bg */}
      <div
        className="absolute inset-0 pointer-events-none opacity-5"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0,255,178,0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,255,178,0.3) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />

      {/* Center violet glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full blur-3xl opacity-10 pointer-events-none bg-violet" />

      <div className="max-w-md mx-auto relative">
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.97 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="p-8 rounded-3xl bg-card card-border-mint"
          style={{
            boxShadow:
              "0 0 60px rgba(0,255,178,0.06), 0 40px 80px rgba(0,0,0,0.4)",
          }}
        >
          {/* Card Header */}
          <div className="text-center mb-8">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center font-black text-lg mx-auto mb-4 bg-gradient-brand text-base">
              FF
            </div>
            <h2
              className="text-2xl font-black mb-2 font-mono text-snow"
              style={{ letterSpacing: "-0.02em" }}
            >
              Welcome back
            </h2>
            <p className="text-sm text-muted font-serif">
              Sign in to start fixing your repositories.
            </p>
          </div>

          {/* GitHub OAuth Button */}
          <motion.button
            className="w-full flex items-center justify-center gap-3 py-4 rounded-xl font-bold text-sm font-mono bg-snow text-base mb-4"
            whileHover={{ scale: 1.02, backgroundColor: "#ffffff" }}
            whileTap={{ scale: 0.98 }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.boxShadow =
                "0 0 32px rgba(226,232,240,0.15)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.boxShadow = "none")
            }
          >
            <GitHubIcon size={20} />
            Continue with GitHub
          </motion.button>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-white/[0.07]" />
            <span className="text-xs text-slate font-mono">or</span>
            <div className="flex-1 h-px bg-white/[0.07]" />
          </div>

          {/* Email & Password */}
          <div className="space-y-3 mb-6">
            <input
              type="email"
              placeholder="Email address"
              className="w-full px-4 py-3 rounded-xl text-sm font-mono outline-none bg-base border border-white/[0.07] text-snow placeholder:text-slate focus:border-mint/30 focus:ring-2 focus:ring-mint/[0.08] transition-all duration-200"
            />
            <input
              type="password"
              placeholder="Password"
              className="w-full px-4 py-3 rounded-xl text-sm font-mono outline-none bg-base border border-white/[0.07] text-snow placeholder:text-slate focus:border-mint/30 focus:ring-2 focus:ring-mint/[0.08] transition-all duration-200"
            />
          </div>

          {/* Sign In Button */}
          <motion.button
            className="w-full py-3.5 rounded-xl text-sm font-bold font-mono bg-gradient-brand text-base"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.boxShadow =
                "0 0 32px rgba(0,255,178,0.3)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.boxShadow = "none")
            }
          >
            Sign In
          </motion.button>

          <p className="text-center text-xs mt-5 font-mono text-slate">
            No account?{" "}
            <span className="text-mint cursor-pointer hover:underline">
              Get started free →
            </span>
          </p>
        </motion.div>
      </div>
    </section>
  );
}
