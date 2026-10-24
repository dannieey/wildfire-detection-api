# PyroScope Frontend Design System (DIP-10)

## Purpose
A compact dark UI system for reviewing candidate wildfire events inferred from MODIS/VIIRS thermal-anomaly observations. A candidate event is not a confirmed wildfire.

## Color tokens
- Background `#0B1117`; primary surface `#111A23`; raised surface `#151F2A`.
- Text `#EDF4F7`; secondary text `#91A3B2`; borders `#263442`.
- High-priority candidate `#FF784F`; medium `#FFBF69`; low-priority `#6CB8FF`; success `#67D5A5`.
- Severity must never be communicated by color alone: include a text label such as HIGH / MEDIUM / LOW.

## Typography
Use Inter when available and system sans-serif fallbacks. Page title 26–28 px / bold; panel title 13–15 px / semibold; body 13–14 px; metadata 10–12 px. Maintain clear contrast and short labels.

## Layout
- Desktop: compact left navigation, main dashboard, map and filter/detail column.
- Tablet: allow metric cards to wrap and reduce sidebar width or hide it.
- Mobile: one-column layout, accessible controls and a drawer that fits the viewport.
- Use 8 px spacing increments and 8/12/16 px corner-radius levels.

## Components
1. Metric card: label, prominent value, contextual explanation.
2. Priority badge: text + severity color.
3. Filter control: visible label, keyboard-operable select/input, clear state.
4. Event marker: selected/hover state and text label on hover/focus.
5. Event drawer: event ID, source, confidence, count, region, summary and analyst caveat.
6. Empty state: explain that no records match and suggest adjusting filters.
7. Data-source status: distinguish configured, unavailable and demo data.

## Interaction and accessibility
- Visible keyboard focus for all controls.
- Use buttons for actions, labels for form controls and Escape to close a drawer.
- Never imply a demo timestamp is current live telemetry.
- Mark all illustrative event data clearly.
- Do not call a thermal anomaly a confirmed fire without an independent validation source.

## Figma handoff
`design/pyroscope-ui-kit.svg` is a vector reference board intended for import into Figma. After importing, inspect font substitution and layout, convert reusable pieces into Figma components, and add the Figma file URL to the DIP-10 PR and YouTrack issue. SVG import is a starting point, not proof that a native Figma component library has already been built.
