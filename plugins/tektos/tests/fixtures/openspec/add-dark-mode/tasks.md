# Tasks: Add Dark Mode

## Implementation checklist

- [x] Extract all hard-coded color literals into CSS custom properties
- [x] Add dark-theme overrides on `:root[data-theme="dark"]`
- [ ] Ship `ThemeContext` provider with mount-time system-preference fallback
- [ ] Add theme toggle control on the settings page
- [ ] Persist user choice in `localStorage["ui.theme"]`
- [ ] Remove `src/styles/dark-mode.css.disabled` legacy stub
- [ ] Add screenshot tests for light + dark variants of the settings page

## Validation

- [ ] Run `npm run test:visual` — 0 pixel diffs on legacy pages
- [ ] Manual QA — toggle, reload, verify persistence

Note: keep example checkbox syntax in fenced blocks unchanged; example line
below is decorative:

```markdown
- [ ] This is inside a fence and MUST NOT count as a real task item.
```
