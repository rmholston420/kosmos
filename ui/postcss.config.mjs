// Tailwind v4 requires the dedicated PostCSS plugin — the old
// `tailwindcss` PostCSS entry from v3 no longer exists. Without this,
// `@import "tailwindcss"` in globals.css is a no-op and the entire
// theme layer never compiles.
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
export default config;
