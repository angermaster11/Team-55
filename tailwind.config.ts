import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0A0E1A",
        surface: "#0F1629",
        card: "#141C35",
        mint: "#00FFB2",
        coral: "#FF6B35",
        violet: "#7B61FF",
        slate: "#4A5568",
        snow: "#E2E8F0",
        muted: "#6B7280",
        subtle: "#9CA3AF",
      },
      fontFamily: {
        mono: ["'DM Mono'", "monospace"],
        serif: ["Georgia", "serif"],
      },
      keyframes: {
        pulse2: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
      },
      animation: {
        pulse2: "pulse2 2s ease-in-out infinite",
        blink: "blink 1s step-end infinite",
      },
    },
  },
  plugins: [],
};

export default config;
