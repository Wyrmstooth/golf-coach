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
          green:  "#16a34a",
          dark:   "#052e16",
          gold:   "#ca8a04",
          light:  "#bbf7d0",
          navy:   "#0f172a",
          slate:  "#1e293b",
          turf:   "#0d4a25",
          cream:  "#f8f8f0",
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
        glow:        "0 0 20px rgba(22, 163, 74, 0.4)",
        "glow-gold": "0 0 20px rgba(202, 138, 4, 0.4)",
        "glow-lg":   "0 0 40px rgba(22, 163, 74, 0.5)",
      },
    },
  },
  plugins: [],
};

export default config;
