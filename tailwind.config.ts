import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        arabic: ['var(--font-arabic)', 'Traditional Arabic', 'serif'],
        bangla: ['var(--font-bangla)', 'SolaimanLipi', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#f4f8f4',
          100: '#e3ede3',
          500: '#2f6d3c',
          600: '#255a30',
          700: '#1d4726',
        },
      },
    },
  },
  plugins: [],
};

export default config;
