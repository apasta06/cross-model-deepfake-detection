import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}", "./.storybook/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        forensic: {
          bg: "#0d1117",
          panel: "#111827",
          panelSoft: "#172033",
          border: "rgba(255,255,255,0.1)",
          text: "#f3f4f6",
          muted: "#9ca3af",
          blue: "#38bdf8",
          real: "#2E8B57",
          uncertain: "#D98E04",
          fake: "#C0392B",
        },
      },
      boxShadow: {
        forensic: "0 24px 80px rgba(0,0,0,0.35)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
