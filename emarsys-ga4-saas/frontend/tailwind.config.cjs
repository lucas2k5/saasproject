/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Space Grotesk", "Sora", "system-ui", "sans-serif"],
        display: ["Sora", "Space Grotesk", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};
