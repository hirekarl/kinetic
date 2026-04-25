/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        zinc: {
          950: '#09090b',
        },
        // Semantic status colors
        status: {
          green: '#10b981', // emerald-500
          yellow: '#f59e0b', // amber-500
          red: '#f43f5e', // rose-500
        },
      },
    },
  },
  plugins: [],
};
