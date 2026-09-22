/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./index.html"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        tesseract: {
          dark: "#0f0f1a",
          darker: "#0a0a14",
          accent: "#6366f1",
          "accent-hover": "#818cf8",
          surface: "#1a1a2e",
          border: "#2d2d44",
          text: "#e2e8f0",
          "text-muted": "#94a3b8",
        },
      },
    },
  },
  plugins: [],
};