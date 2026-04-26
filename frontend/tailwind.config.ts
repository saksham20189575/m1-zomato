import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f6f7f4",
          100: "#e3e7dc",
          500: "#5c6b4a",
          800: "#2d3528",
        },
        zomato: {
          50: "#fff5f5",
          100: "#FDECEC",
          500: "#E23744",
          600: "#cb2f3b",
          700: "#b32832",
        },
      },
      fontFamily: {
        zomato: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "Segoe UI",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
