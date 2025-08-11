/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#dc2626', // red-600
        secondary: '#374151', // gray-700
        dark: '#0f0f0f',
        'dark-secondary': '#212121',
      },
      fontFamily: {
        sans: ['Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [
    // Plugin personalizado para scrollbar
    function({ addUtilities }) {
      addUtilities({
        '.scrollbar-thin': {
          'scrollbar-width': 'thin',
        },
        '.scrollbar-thin::-webkit-scrollbar': {
          width: '6px',
        },
        '.scrollbar-thumb-gray-500::-webkit-scrollbar-thumb': {
          'background-color': '#6b7280',
          'border-radius': '3px',
        },
        '.scrollbar-track-gray-700::-webkit-scrollbar-track': {
          'background-color': '#374151',
        },
        '.scrollbar-thin::-webkit-scrollbar-thumb:hover': {
          'background-color': '#9ca3af',
        },
      });
    },
  ],
}