/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        card: "#111827",
        primary: "#6366f1",
        success: "#10b981",
        warning: "#f59e0b",
        error: "#ef4444",
        text: "#f8fafc",
        subtext: "#94a3b8",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
}
