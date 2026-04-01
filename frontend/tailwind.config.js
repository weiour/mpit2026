/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: '#080d1d',
          panel: '#0f172a',
          blueA: '#1769ff',
          blueB: '#4db3ff',
          blueCard: '#154fc7',
          blueCard2: '#2f8df0',
          text: '#ffffff',
          muted: 'rgba(255,255,255,0.78)',
          line: 'rgba(255,255,255,0.18)',
          orange: '#f7965b',
          darkBtn: '#2d281f',
          darkBtn2: '#3b3224',
          dock: 'rgba(8,20,44,0.88)',
          dockBtn: 'rgba(255,255,255,0.12)',
        },
      },
      boxShadow: {
        soft: '0 18px 50px rgba(0,0,0,0.28)',
        panel: '0 20px 60px rgba(0, 20, 80, 0.35)',
      },
      fontFamily: {
        rubik: ['Rubik', 'sans-serif'],
        russo: ['"Russo One"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
