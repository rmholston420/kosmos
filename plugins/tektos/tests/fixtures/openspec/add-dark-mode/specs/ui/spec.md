# Delta for UI

## ADDED Requirements

### Requirement: Theme toggle control on settings page

The settings page SHALL expose a theme toggle control that lets the user
switch between light and dark themes without a page reload.

#### Scenario: Toggle from light to dark
- GIVEN the app is currently rendered with the light theme
- WHEN the user activates the theme toggle on the settings page
- THEN `document.documentElement.dataset.theme` is set to `"dark"`
- AND the persisted preference in `localStorage["ui.theme"]` becomes `"dark"`

#### Scenario: Toggle from dark to light
- GIVEN the app is currently rendered with the dark theme
- WHEN the user activates the theme toggle on the settings page
- THEN `document.documentElement.dataset.theme` is set to `"light"`

### Requirement: System-preference fallback

The system SHALL respect the OS-level `prefers-color-scheme` value on
first render whenever the user has never explicitly set the theme.

**Priority**: normal
**Owner**: ui-team

#### Scenario: First launch on a dark-mode OS
- GIVEN the user has never persisted a `ui.theme` preference
- AND the OS reports `prefers-color-scheme: dark`
- WHEN the app first mounts
- THEN the app renders with the dark theme

## MODIFIED Requirements

### Requirement: Color contrast on interactive elements

All interactive elements MUST meet WCAG AA color contrast under both the
light and the dark theme.

#### Scenario: Primary button contrast — dark theme
- GIVEN the dark theme is active
- WHEN the primary button is rendered
- THEN the computed foreground/background contrast ratio is at least 4.5:1

## REMOVED Requirements

### Requirement: Legacy body class theme selector

The legacy `body.theme-dark` class-based selector is REMOVED. All theme
switching flows through `document.documentElement.dataset.theme`.
