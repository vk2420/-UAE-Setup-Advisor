/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sand: {
          50: "#faf8f4",
          100: "#f3eee4",
        },
        desert: {
          600: "#b9762f",
          700: "#9c5f22",
        },
      },
    },
  },
  plugins: [],
};
