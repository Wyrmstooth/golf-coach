import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      screens: {
        xs: "420px",
      },
      colors: {
        golf: {
          green:  "#10b981",
          dark:   "#022c22",
          gold:   "#f59e0b",
          light:  "#a7f3d0",
          navy:   "#090d14",
          slate:  "#131c31",
          turf:   "#047857",
          cream:  "#fafaf5",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["'DM Sans'", "Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow":   "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "swing":        "swing 2s ease-in-out infinite alternate",
        "float":        "float 4s ease-in-out infinite",
        "gradient":     "gradient 8s ease infinite",
        "spin-slow":    "spin 8s linear infinite",
        "golf-bounce":  "golf-bounce 1s ease-in-out infinite",
        "golf-spin":    "golf-spin 2s linear infinite",
        "ball-shadow":  "ball-shadow 1s ease-in-out infinite",
        "ball-roll":    "ball-roll 2s linear infinite",
        "tee-wobble":   "tee-wobble 2s ease-in-out infinite",
        "grass-wave":   "grass-wave 3s ease-in-out infinite",
        "fairway-pulse":"fairway-pulse 4s ease-in-out infinite",
        "float-particle":"float-particle 6s ease-in-out infinite",
      },
      keyframes: {
        swing: {
          "0%":   { transform: "rotate(-20deg)" },
          "100%": { transform: "rotate(20deg)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%":      { transform: "translateY(-12px)" },
        },
        gradient: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%":      { backgroundPosition: "100% 50%" },
        },
      },
      backgroundSize: {
        "300%": "300%",
      },
      boxShadow: {
        glow:        "0 0 24px rgba(16, 185, 129, 0.35)",
        "glow-gold": "0 0 24px rgba(245, 158, 11, 0.35)",
        "glow-lg":   "0 0 48px rgba(16, 185, 129, 0.45)",
        card:        "0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.24)",
      },
    },
  },
  plugins: [],
};

export default config;
