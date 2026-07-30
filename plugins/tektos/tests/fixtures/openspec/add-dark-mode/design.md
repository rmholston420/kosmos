# Design: Add Dark Mode

## Architecture

Two layers:

1. **CSS layer.** All colors defined as CSS custom properties on `:root`, with
   dark-theme overrides under `:root[data-theme="dark"]`. Every existing rule
   that referenced a hard-coded color is rewritten to reference the variable.

2. **State layer.** A single React `ThemeContext` provider wraps the app root.
   It:
   - Reads `localStorage["ui.theme"]` at mount; if absent, reads
     `window.matchMedia('(prefers-color-scheme: dark)').matches`.
   - Writes the resolved theme to `document.documentElement.dataset.theme`.
   - Persists user toggles back to `localStorage`.

## Non-goals

- No third-party theming library (Emotion, styled-components, etc.).
- No server-side rendering support in this change — client-only.

## Migration

All color literals in `src/styles/*.css` are replaced in one commit. The old
`src/styles/dark-mode.css.disabled` file (referenced in issue #412) is
removed.

## Open questions

- Should the settings page expose a "Follow system" third option, or is
  "toggle" enough? **Decision:** two-option toggle for v1; system fallback
  applies only when no explicit choice has been persisted.
