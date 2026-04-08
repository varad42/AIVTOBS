/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef9ff",
          100: "#d9f1ff",
          500: "#1892ff",
          600: "#0f78d0",
          700: "#0c5ea4",
          900: "#0c1f36",
        },
      },
      boxShadow: {
        card: "0 10px 30px rgba(13, 46, 86, 0.12)",
      },
      animation: {
        "pulse-soft": "pulse 2.2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
