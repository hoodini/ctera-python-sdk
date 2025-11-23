/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ctera: {
          navy: '#0A1628',
          space: '#1A2540',
          cyan: '#00D4FF',
          cyanLight: '#4DD4FF',
          purple: '#3B2F85',
          purpleDeep: '#1E1A3D',
          pink: '#FF1493',
          gray: '#A0A5B8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Montserrat', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

