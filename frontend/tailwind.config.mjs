/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1220",
        panel: "#11182b",
        border: "#1f2a44",
        accent: "#7aa2ff",
      },
    },
  },
  plugins: [],
};
