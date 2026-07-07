# Design

Visual system for Zebra Label Gateway. Register: **product** (industrial
utility). Source of truth: `web/src/styles/tokens.css`. See `PRODUCT.md` for
strategy and `docs/refactor-plan.md` for the roadmap.

## Theme

Dark "equipment panel" is the default so the white 4×6 label preview is the
brightest object on screen — the preview is the contract. Light mode is a full
peer (pure-white surfaces), selectable via the toolbar toggle and honored from
`prefers-color-scheme`. Brand and semantic hues are invariant across themes;
only surfaces and ink re-derive.

## Color (OKLCH, restrained strategy)

Green primary = ready / go / print; amber = attention/paused; red = error.
Surfaces are pure-neutral (chroma 0) — no cream/beige tint anywhere.

| Role | Dark | Light |
|---|---|---|
| `--bg` | `oklch(0.11 0 0)` | `oklch(1 0 0)` |
| `--surface` | `oklch(0.16 0 0)` | `oklch(0.985 0 0)` |
| `--surface-2` | `oklch(0.205 0 0)` | `oklch(0.96 0 0)` |
| `--line` | `oklch(0.30 0 0)` | `oklch(0.90 0 0)` |
| `--ink` | `oklch(0.93 0 0)` | `oklch(0.22 0 0)` |
| `--ink-muted` | `oklch(0.68 0 0)` | `oklch(0.44 0 0)` |
| `--primary` | `oklch(0.65 0.10 140)` | `oklch(0.55 0.12 140)` |
| `--warn` | `oklch(0.78 0.14 75)` | `oklch(0.62 0.15 75)` |
| `--err` | `oklch(0.64 0.19 25)` | `oklch(0.55 0.20 25)` |
| `--info` / `--focus` | `oklch(0.72 0.10 230)` | `oklch(0.52–0.55 0.12–0.14 230)` |

White (`--on-primary`) text on all saturated fills. State vocabulary:
default / hover / focus-visible / active / disabled / loading / error.

## Typography

- **Inter Variable** (self-hosted) for everything; **JetBrains Mono** for machine
  data (IPs, dimensions, ZPL byte counts, tracking numbers) via `.mono`.
- Fixed rem scale, ratio ~1.125: `--fs-xs` 12 → `--fs-2xl` 28. No fluid clamps.
- `text-wrap: balance` on headings.

## Space, radius, elevation

- 4px spacing base (`--sp-1`…`--sp-12`). Density is a feature in the adjust panel;
  the preview breathes.
- Radius: 4 (inputs) / 6 (buttons) / 10 (panels). No pill buttons.
- Elevation = border + shadow (`--shadow-1/2/pop`). No glassmorphism.
- Semantic z-scale: sticky < dropdown < backdrop < dialog < toast < tooltip.

## Motion

`--dur` 130–320ms, `--ease-out` `cubic-bezier(0.22,1,0.36,1)`. Motion conveys
state only (preview crossfade, status pulse while checking, toast entry). Full
`prefers-reduced-motion` reset in `global.css`.

## Components (`web/src/lib/components/`)

Button, SegmentedControl, Slider, StatusPill, DropZone (drag/click/paste),
CropStage (drag box + handles + keyboard nudge + page nav), PreviewViewport
(fit / 100% zoom), AdjustPanel, HistoryPanel, Toaster, and native `<dialog>`
surfaces (ProfileSaveDialog, StatusDialog, SettingsDialog). No `prompt()`/`alert()`.

## Layout

App shell = sticky toolbar (brand · theme · settings · status pill) + three-pane
editor (Source · Adjust · Preview). Breakpoints collapse structurally:
≥1100px three-pane → ≥720px two-pane (adjust on top) → <720px single column with
a thumb-reachable sticky Print bar. Safe-area insets on toolbar and print bar.

## Stack

Vite + Svelte 5 + TypeScript (`web/`), built to
`src/zebra_label_gateway/webapp/static/dist/`, served by FastAPI. Fonts bundled
(no external requests → offline / PWA ready). Multi-stage Docker: `node:22` build
→ `python:3.12` runtime.
