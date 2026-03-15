import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        golf: {
          green:  "#16a34a",
          dark:   "#052e16",
          gold:   "#ca8a04",
          light:  "#bbf7d0",
          navy:   "#0f172a",
          slate:  "#1e293b",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["'DM Sans'", "Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "swing":      "swing 2s ease-in-out infinite alternate",
        "float":      "float 4s ease-in-out infinite",
        "gradient":   "gradient 8s ease infinite",
        "spin-slow":  "spin 8s linear infinite",
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
      },
    },
  },
  plugins: [],
};

export default config;
