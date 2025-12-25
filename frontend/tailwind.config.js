// Force a writable temp dir for Tailwind's loader (WSL/hosted paths can be read-only)
process.env.TMPDIR = process.env.TMPDIR || '/tmp';

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
