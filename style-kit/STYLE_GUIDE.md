# Emotions visual style guide

Design language sampled pixel-exactly from the hero figure and title of
<https://transformer-circuits.pub/2026/emotions/>. Attach this file plus
`emotions-theme.css` (and optionally `example.html`) to any new project and
ask for the site to be built "in this style".

## How to use this kit

1. Copy `emotions-theme.css` into the project and link it in `<head>`.
2. Use the `et-*` classes for standard elements, or reference the CSS variables
   (`var(--blue)`, `var(--panel-bg)`, ...) in new components.
3. Never introduce new colors. Every surface, line, and accent must be one of
   the values below. If a new need arises, pick the closest role from the table.
4. `example.html` is a working showcase of every component. Open it to see the
   intended look, or copy markup from it.

## Color roles (exact values)

| Role | Hex | Use for |
|---|---|---|
| Page background | `#FBFBFA` | `<body>` |
| Panel / cream | `#FAF9F5` | Section containers, code and prompt boxes, quote boxes |
| Card / white | `#FFFFFF` | Cards, strips, chart plot areas, slider thumbs |
| Border | `#DDDDDD` | All borders, chart axes, ticks, baselines, chevron separators |
| Title | `#000000` | Page title and section headings |
| Text | `#3D3D3A` | Body and description text, bold emphasis |
| Muted | `#73726C` | Monospace text, axis labels, captions, readouts, control labels |
| Blue | `#2C84DB` | Positive / calm series, blue labels, blue arrows, primary button |
| Pink | `#C46686` | Negative / afraid / desperate series, pink labels, pink arrows |
| Orange | `#D97757` | One emphasis accent only: italic accent word, icon highlights |
| Blue tint | `#EAF3F7` | Blue confidence band, blue highlight background, blue toggle on |
| Pink tint | `#FCEBEA` | Pink confidence band, pink highlight background, pink toggle on |
| Band overlap | `#E7E1E4` | Color where blue and pink bands overlap |
| Dash on cream | `#B0AEA5` | Dashed connector arrows and underlines drawn over `#FAF9F5` |
| Dash on white | `#BCBBBB` | Dashed arrows, axis direction arrows, hints drawn over `#FFFFFF` |

Rules of thumb:
- Blue means positive, calm, or the "good" direction. Pink means negative,
  afraid, hostile, or the "bad" direction. Orange is never a data color.
- Two levels of text only: `#3D3D3A` for prose, `#73726C` for everything
  secondary. Headings and the title are pure black.
- No shadows, no gradients. Depth comes from the cream-on-white-on-cream layering
  plus the single `#DDDDDD` border.

## Typography

| Element | Font | Size | Weight |
|---|---|---|---|
| Page title | System sans (`-apple-system, "Segoe UI", Roboto, ...`) | 50px, line-height 1.1 | 700, letter-spacing -0.5px, centered |
| Section heading | System sans | 19px (24px when the section is a full-width block) | 700, black |
| Description | System sans | 21px, line-height 1.4 | 400 |
| Pipeline step text | System sans | 18px | 400 |
| Prompt / code | `Consolas, Monaco, "Andale Mono", monospace` | 16px, line-height 1.55 | 400, muted color |
| Readouts and control labels | System sans | 16 to 17px | 400, muted; values bold in `#3D3D3A` |
| Hints | System sans | 14px | 400, `#BCBBBB` |
| Accent word | `Georgia` italic | 30px | 400, orange |
| Chart labels (300-wide viewBox) | System sans | captions 11px, series labels 13px bold | scale with SVG width |

Those sizes are the "presentation" scale. For a dense reading layout halve
them roughly: title 50, headings 15, description 15, code 11.5, readouts 12.

## Layout

- Page: body background, centered title block, then one or more cream panels
  with max-width 1280px and 24/36px padding, rounded 8px.
- Inside a panel: a bold black section heading, then a white card with a
  1px `#DDDDDD` border and 10px radius.
- Full-width interactive blocks use a two-column grid inside the card:
  text, prompt box and controls on the left (5fr), chart on the right (7fr),
  48px gap. Stack to one column under 900px.
- Pipeline / process strip: white, bordered, 84px tall, equal columns,
  separated by full-height `#DDDDDD` chevrons. Each step is icon then two-line
  label.
- Connector arrows between a prompt box and a chart are vertical dashed lines
  (`stroke-dasharray 2 3`) with an open chevron head, 1.2px stroke.

## Charts (SVG)

- Draw charts as inline SVG with a 300-unit-wide viewBox so they scale to
  any column width and text scales with them.
- Axes and ticks: `#DDDDDD`, 1px. No grid lines except a single baseline.
- Series: 2px stroke, 3px-radius dots, in blue or pink only.
- Confidence bands: solid `#EAF3F7` / `#FCEBEA` polygons, no stroke.
- Current-value marker: dashed vertical line in `#BCBBBB` plus a 4.5px dot in
  the series color with a 1.5px white stroke.
- Inactive series fade to opacity 0.25 to 0.3; inactive bands to 0.4.
- Horizontal arrow charts (Elo-style): gray `#DDDDDD` baseline per row, a dot
  at zero, an arrow in the series color with an open 7-unit chevron head.
- Series names sit next to the line or at the row start, bold, in the series
  color. Axis titles and tick labels are muted `#73726C`.

## Interactive conventions

- Sliders: 3px `#DDDDDD` track, 20px white round thumb with a 2.5px `#3D3D3A`
  border. Show the live value right-aligned in bold monospace.
- Toggles: bordered pill group; the active option takes the tint background
  and the matching accent color (`.blue.on`, `.pink.on`).
- Highlighting a chosen option in text: tint background plus accent color and
  bold (`.et-hl.blue` / `.et-hl.pink`).
- Quote or example boxes: cream, muted monospace; the active one gets full
  opacity and a 2px accent border, others sit at opacity 0.45.
- Transitions are short (0.2s) and limited to background, color, opacity.

## Icons

Line icons in `#3D3D3A` at 1 to 1.2px stroke, with `#BCBBBB` for secondary
strokes and a single orange `#D97757` starburst or arrow as the highlight.
No filled icons, no other colors.
