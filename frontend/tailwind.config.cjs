/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
    "./src/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#4a9d9c',
          dark: '#357a79',
          light: '#6eb7b6',
        },
        accent: {
          DEFAULT: '#edb44d',
          dark: '#d6a13e',
        },
      },
    },
  },
  plugins: [],
}


