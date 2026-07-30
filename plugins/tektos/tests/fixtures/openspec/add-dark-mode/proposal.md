# Proposal: Add Dark Mode

## Intent

Users have requested a dark mode option to reduce eye strain during nighttime
usage. Multiple accessibility reports and one open GitHub issue (#412) request
a system-preference-aware theme toggle.

## Scope

- Add a theme toggle in the settings page.
- Support system preference detection via `prefers-color-scheme`.
- Persist the user's explicit choice in `localStorage` under key `ui.theme`.
- Ensure all UI-owned specs and components respect the active theme.

## Approach

Use CSS custom properties (variables) declared on `:root` with a `[data-theme]`
attribute selector. A tiny React `ThemeContext` provider reads the persisted
value on mount, falls back to the system preference otherwise, and exposes a
`toggle()` action to the settings component.

No new runtime dependency. All theme resolution happens in a single hook.

## Out of scope

- Custom user-defined themes beyond dark/light.
- Per-component theming overrides.
- Automatic scheduled theme switching by time-of-day.
