import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        accent: 'rgb(var(--accent-color) / <alpha-value>)',
        'accent-hover': 'rgb(0, 200, 200 / <alpha-value>)',
        dark: {
          900: 'rgb(10 10 10 / <alpha-value>)',
          800: 'rgb(20 20 20 / <alpha-value>)',
          700: 'rgb(40 40 40 / <alpha-value>)',
        }
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
  ],
};
export default config; 