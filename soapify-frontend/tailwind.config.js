/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: '#060b16',
        panel: '#111a2e',
        card: '#1a2642',
        accent: '#38bdf8',
        mint: '#34d399',
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(56,189,248,0.25), 0 8px 32px rgba(2,6,23,0.45)',
      },
      backgroundImage: {
        aura: 'radial-gradient(circle at 10% 10%, rgba(56,189,248,0.20), transparent 45%), radial-gradient(circle at 90% 0%, rgba(52,211,153,0.16), transparent 35%)',
      },
    },
  },
  plugins: [],
};
