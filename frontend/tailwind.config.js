/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // 素世 (Soyo) - 亚麻色/栗色系
        soyo: {
          DEFAULT: "#C4A77D", // 亚麻色
          light: "#D4BC94",
          dark: "#8B6914", // 栗色
          cream: "#F5E6D3",
        },
        // 祥子 (Sakiko) - 淡蓝色系
        sakiko: {
          DEFAULT: "#7EB8DA", // 淡蓝色
          light: "#B5D8ED",
          dark: "#4A90B8",
          pale: "#E8F4FA",
        },
        // 主题色 (使用素世的亚麻色作为主色)
        primary: {
          DEFAULT: "#C4A77D",
          dark: "#A68B5B",
          light: "#D4BC94",
        },
        // 次要色 (使用祥子的淡蓝色)
        secondary: {
          DEFAULT: "#7EB8DA",
          dark: "#4A90B8",
          light: "#B5D8ED",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
