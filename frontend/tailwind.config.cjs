/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
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
        // Colores semánticos conectados a las variables CSS del sistema de diseño.
        // Al usar canales RGB permiten modificadores de opacidad (ej. bg-surface/80).
        body: 'rgb(var(--body-rgb) / <alpha-value>)',
        surface: 'rgb(var(--surface-rgb) / <alpha-value>)',
        'surface-alt': 'rgb(var(--surface-alt-rgb) / <alpha-value>)',
        main: 'rgb(var(--main-rgb) / <alpha-value>)',
        muted: 'rgb(var(--muted-rgb) / <alpha-value>)',
        subtle: 'rgb(var(--subtle-rgb) / <alpha-value>)',
        inverse: 'rgb(var(--inverse-rgb) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1.25rem',
      },
      boxShadow: {
        soft: '0 1px 2px 0 rgb(15 23 42 / 0.04), 0 1px 3px 0 rgb(15 23 42 / 0.06)',
        card: '0 1px 3px 0 rgb(74 157 156 / 0.10), 0 1px 2px -1px rgb(74 157 156 / 0.08)',
        lifted: '0 10px 30px -12px rgb(74 157 156 / 0.25)',
      },
    },
  },
  plugins: [],
}
