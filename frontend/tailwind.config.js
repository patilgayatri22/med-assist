/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        pass: '#22c55e',
        fail: '#ef4444',
        pending: '#6b7280',
        highalert: '#f59e0b',
      },
    },
  },
  plugins: [],
}

