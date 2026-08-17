/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0faf2",
          100: "#dcf4e2",
          200: "#bbeba7",
          300: "#86d470",
          400: "#53b83f",
          500: "#2f9a23",
          600: "#1e7a18",
          700: "#186016",
          800: "#154d14",
          900: "#0f3a0e",
          950: "#15502A",
        },
        emerald: {
          950: "#022c22",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
