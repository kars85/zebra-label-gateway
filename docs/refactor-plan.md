# Zebra Label Gateway — Product Refactor Plan

**Goal:** take the current (functional, session-grown) web app to a commercial-grade
(COTS-quality) product: a deliberate design system instead of ad-hoc CSS, delivered as
(a) a Docker-hosted website, (b) standalone installers for Windows and macOS, and
(c) a first-class iPhone/iPad web experience — plus a grounded feasibility verdict on
Adobe / Word / LibreOffice Writer plugins.

Register: **product** (design serves the task). Personality: **industrial utility** —
precise, sturdy, quiet. See `PRODUCT.md` for principles and anti-references.

---

## 1. Current state, honestly assessed

What exists works and is well-tested (76 tests, verified against the real printer), but
the frontend is not COTS-grade:

| Area | Today | Gap |
|---|---|---|
| Styling | One hand-grown `style.css`, hex colors, no token system | No design tokens, no themable system, inconsistent spacing rhythm |
| Components | Ad-hoc CSS classes per element | No component vocabulary; states (hover/focus/disabled/loading/error) are partial |
| Interactions | `prompt()` for profile naming | Native `prompt()` is the single loudest "not a product" tell |
| States | Toast + spinner only | No empty states, no skeletons, no inline error guidance (offline printer just turns a pill red) |
| Keyboard | None | No shortcuts, no focus management, crop box is mouse/touch-only |
| JS architecture | One 400-line vanilla `app.js`, global `state` object | Fine at this size, but each new surface (history, settings, profiles manager) compounds it |
| Mobile | Responsive grid collapse only | No PWA, no safe areas, no touch-target discipline, no iOS install story |
| Config | Printer IP via env var only | A desktop-installer user cannot set env vars — needs in-app settings |

The backend is in good shape and mostly untouched by this plan: FastAPI, shared
pipeline, profile training, history persistence, env-based config. The refactor is
~90% frontend + packaging.

---

## 2. Design system (the "impeccable" refactor)

### 2.1 Scene and theme

Scene sentence: *a packing bench under mixed warehouse/ambient light; the operator
glances at the screen between taping boxes; the brightest thing on screen should be
the white 4×6 label preview — because the preview is the contract.*

That forces the theme: **dark equipment-panel default** (near-black, chroma 0), with a
pure-white light mode honored via `prefers-color-scheme` and a manual toggle. On a
dark surface the 1-bit label preview becomes the visual anchor of the whole UI,
exactly where the operator's trust needs to live.

### 2.2 Color tokens (OKLCH, restrained strategy)

Brand seed: `oklch(0.65 0.10 140)` — moss green. Semantically right for a print
station: green is "ready / go / print". Amber is the natural counterpoint (attention /
paused / paper-out). Full palette, dark theme first:

```css
:root {
  /* surfaces — pure neutral, no hue tint */
  --bg:        oklch(0.11 0 0);
  --surface:   oklch(0.16 0 0);      /* panels, cards */
  --surface-2: oklch(0.20 0 0);      /* toolbar, inputs */
  --line:      oklch(0.30 0 0);      /* borders */

  /* ink */
  --ink:       oklch(0.93 0 0);
  --ink-muted: oklch(0.68 0 0);

  /* brand */
  --primary:       oklch(0.65 0.10 140);  /* Print action, selection, ready state */
  --primary-hover: oklch(0.70 0.11 140);
  --on-primary:    oklch(0.98 0 0);       /* white text on saturated fill */

  /* semantic */
  --accent-warn: oklch(0.75 0.14 75);     /* amber: paused, paper-out, attention */
  --accent-err:  oklch(0.62 0.19 25);     /* error, offline */
  --accent-info: oklch(0.70 0.10 230);    /* neutral info */
}
```

Light mode swaps surfaces to pure white / near-white neutrals and re-derives ink; the
brand and semantic hues stay identical (that's what makes it one product in both
themes). Rules honored: body contrast ≥ 4.5:1 (target ≥ 7:1 for ink-on-bg), white text
on saturated fills, primary chroma ≤ 0.23, no cream/beige tint anywhere.

### 2.3 Typography

- **One family**: `Inter` (self-hosted, variable) with `system-ui` fallback — product
  register, no display font.
- **Mono accent for machine data**: tracking numbers, ZPL byte counts, printer IPs,
  dimensions render in `ui-monospace / JetBrains Mono`. This carries the "equipment"
  personality without decoration.
- Fixed rem scale, ratio 1.125: 12 / 13.5 / 15 (body) / 17 / 19 / 21.5 / 24.
- `text-wrap: balance` on headings; labels never wrap.

### 2.4 Spacing, radius, elevation, z-index

- 4px base spacing scale (`--sp-1: 4px` … `--sp-8: 48px`); density is a feature —
  the adjust panel runs compact, the preview area breathes.
- Radii: 4 (inputs) / 6 (buttons) / 10 (panels). No pill buttons.
- Semantic z-scale: `--z-dropdown < --z-sticky < --z-backdrop < --z-dialog < --z-toast`.
- Elevation by border + subtle shadow, not glass. No backdrop blur anywhere.

### 2.5 Motion

- 150–250 ms, `cubic-bezier(0.22, 1, 0.36, 1)` (ease-out-quint family). Motion only
  conveys state: preview crossfade on re-render, crop-box handle feedback, toast
  entry, status-pill pulse only while a job is in flight.
- No page-load choreography. `prefers-reduced-motion` ⇒ crossfades become instant.

### 2.6 Component inventory (each ships with default / hover / focus-visible / active / disabled / loading / error)

| Component | Notes |
|---|---|
| Button (primary / secondary / ghost / danger) | Primary = Print only; one primary per view |
| SegmentedControl | Crop mode, rotation — replaces the ad-hoc `.seg` |
| Slider | Threshold, with numeric input twin for keyboard/precision |
| Select | Profile picker with description subtext |
| DropZone | Idle / drag-over / uploading (progress) / error; also a paste target (Ctrl+V screenshot) |
| CropStage | Drag box + 4 handles + **keyboard nudge** (arrows = 1px, shift = 10px) + numeric fraction readout |
| PreviewViewport | Fit / 100% toggle (kept), dimension ruler overlay (812×1218 + inches), render-state shimmer |
| PageNav | Compact stepper; page thumbnails at ≥3 pages |
| StatusPill → StatusPanel | Pill stays in the toolbar; clicking opens a panel with the full `~HS`/SGD readout and guidance ("Head open — close the latch") instead of raw flags |
| Toast | Success / error / info, queued, dismissible |
| **Dialog** | Native `<dialog>`: profile save (named fields, replaces `prompt()`), delete confirms, settings |
| HistoryCard grid | Reprint / delete kept; add filter-by-name and a detail view (full preview + metadata) |
| EmptyState | History empty, no-upload — teach the interface ("Drop a label or press ⌘V") |
| Skeleton | History grid and preview while loading |
| SettingsPanel | **New**: printer host/port (persisted to data dir via new `/api/settings`), theme, default profile — required for the desktop installer where env vars don't exist |

### 2.7 Layout

App shell: slim top toolbar (product name, printer StatusPill, settings) + the
three-pane editor (source / adjust / preview). Panes collapse structurally:
≥1100px three-pane; 700–1100px two-pane (adjust docks under source); <700px single
column with the Print action in a sticky bottom bar (thumb-reachable on phones).

### 2.8 Keyboard & a11y defaults (best-effort, baked into the system)

`Ctrl/⌘+P` print (intercepted), `V` paste-to-upload, arrows nudge crop, `[` `]` page
nav, `Esc` closes dialogs. Focus-visible rings on everything interactive; 44px minimum
targets on coarse pointers; reduced-motion honored. Not gated on a formal audit.

---

## 3. Frontend architecture decision

**Recommendation: Vite + TypeScript + Svelte 5, tokens in plain CSS custom properties.
No Tailwind, no component library imports.**

| Option | Verdict |
|---|---|
| Stay vanilla JS | Cheapest, but component states × new surfaces (settings, dialogs, history detail) push a hand-rolled 400-line file toward the exact "vibe-coded" outcome we're refactoring away from |
| React + shadcn/MUI | The stock-component route is the definition of COTS-*looking*-but-generic; heavier runtime; rejected |
| **Svelte 5 + Vite + TS** | Real components with typed props/states, ~15KB runtime, compiles to static assets FastAPI already serves; design system stays hand-built per this plan |
| Web Components (Lit) | Viable fallback if avoiding a framework is preferred; more boilerplate for the same result |

Consequences: a `web/` source directory with `npm run build` emitting to
`webapp/static/dist/`; Dockerfile gains a `node:22-slim` build stage (multi-stage,
final image unchanged in character); FastAPI serves the built assets exactly as today.
The REST API is already clean — **no backend changes required** beyond the new
`/api/settings` endpoint and CORS configuration (needed later for plugins).

---

## 4. Delivery targets

### 4.1 Docker website (exists — refinements only)

Already shipping. Plan adds: multi-stage frontend build, `/api/settings` persisted in
the `zlg-data` volume, and the TLS story below (which Docker hosting needs for PWA).

### 4.2 Standalone installers — Windows & macOS

The whole backend is Python (PyMuPDF, Pillow, FastAPI), so any desktop app must ship a
frozen Python runtime. The question is only the shell around it:

| Approach | Installer feel | Size | Auto-update | Effort | Verdict |
|---|---|---|---|---|---|
| **Tauri 2 + PyInstaller sidecar** | Native window (WebView2/WKWebView), MSI/NSIS + DMG generation, updater, tray icon | ~15MB shell + ~70MB sidecar | Built-in | M–L (Rust toolchain, sidecar lifecycle) | **Target** |
| pywebview + PyInstaller + Inno Setup / dmgbuild | Native-ish window, hand-built installers | ~80MB | None | S–M | **Fallback / first ship** |
| Electron + Python | Two runtimes, 150MB+ | XL | Built-in | M | Rejected |
| BeeWare Briefcase | Native MSI/DMG from Python | ~90MB | None | M | Viable but weaker webview story |

**Recommended path:** ship v1 with **pywebview + PyInstaller** (all-Python, lowest
risk, ~a week of packaging work including CI), then graduate to **Tauri 2 sidecar**
when auto-update and a system-tray "gateway running" affordance justify the Rust
toolchain. Both reuse the identical FastAPI app and built frontend — zero UI fork.

Hard requirements for COTS credibility (both paths):

- **Code signing.** Windows: Authenticode via Azure Trusted Signing (~$10/mo) or an
  OV/EV cert — unsigned = SmartScreen wall. macOS: Developer ID ($99/yr) +
  notarization — unsigned = Gatekeeper wall. Budget this; it is not optional for COTS.
- **In-app settings** (§2.6) — installer users configure the printer IP in the UI.
- **First-run flow**: detect-printer screen (manual IP entry v1; mDNS/SNMP discovery
  of Zebra printers is a strong v2 differentiator — they announce on the LAN).
- CI: GitHub Actions matrix (windows-latest, macos-14) building signed artifacts per
  tagged release.

### 4.3 iPhone / iPad — native-web features (PWA)

What genuinely works on iOS Safari and is in scope:

- **Add to Home Screen standalone app**: `manifest.webmanifest` (name, icons,
  `display: standalone`, `theme-color` matching `--bg`), `apple-touch-icon`,
  `apple-mobile-web-app-status-bar-style`.
- **Safe areas & viewport**: `viewport-fit=cover` + `env(safe-area-inset-*)` padding
  on the toolbar and the sticky Print bar (iPhone notch/home-indicator correct).
- **Touch ergonomics**: 44pt targets, crop handles enlarged on coarse pointers,
  slider thumb ≥ 28pt, sticky bottom Print bar in one-handed reach.
- **Apple Pencil + touch crop**: already pointer-events-based — verified path; add
  `touch-action` tuning so the page doesn't scroll while dragging the crop box.
- **Camera capture**: `<input accept="image/*,application/pdf" capture="environment">`
  — photograph a paper label/QR sheet directly into the pipeline.
- **iPadOS drag & drop**: dropping a PDF from Files/Mail split-view onto the DropZone
  works in Safari — test and keep.
- **Home-screen web push** (iOS 16.4+): possible for "print completed/failed" — noted
  as optional, likely overkill for a bench tool.

**Honest constraints (the plan must not pretend otherwise):**

1. **Service workers and installable PWAs require a secure context.** `http://<LAN-IP>:8420`
   will never register a service worker. See §4.4 — TLS is the real prerequisite for
   the whole iOS story.
2. **Web Share Target does not exist on iOS Safari.** "Share a PDF from Mail straight
   into the gateway" cannot be done via PWA manifest on iOS. The working equivalent is
   an **Apple Shortcuts recipe**: a share-sheet Shortcut that POSTs the file to
   `/api/upload` (and optionally `/api/print`). This works *today* against the
   existing API, is genuinely native iOS UX, and should ship as a documented,
   downloadable `.shortcut` in Phase 2.

### 4.4 TLS on the LAN (cross-cutting prerequisite)

Three consumers need HTTPS: iOS PWA installability/service worker, Office add-ins
(HTTPS-only hosts), and general COTS credibility (no "Not Secure" chip on the bench
iPad). LAN reality: no public domain, so:

- **Recommended:** add an optional **Caddy sidecar** to `docker-compose.yml` with
  Caddy's internal CA (`tls internal`) serving `https://gateway.local` (mDNS name or
  static-IP SAN cert). One-time: install the Caddy root cert on the bench devices
  (iOS: install + trust profile). Document with screenshots.
- Alternatives: `mkcert` (same trust-install step, no extra container) or Tailscale
  Serve (zero cert pain if the household/shop already uses Tailscale; `*.ts.net` certs
  are publicly valid).

---

## 5. Plugin feasibility — Adobe / Word / LibreOffice Writer

Key architectural insight: every plugin reduces to the same thin operation —
**"render current document to PDF → POST to the gateway → (optionally auto-print)"**.
The gateway API already supports the receiving half. So each plugin is a small sender;
feasibility differs only in how hostile the host application is.

| Host | Mechanism | Feasibility | Effort | Verdict |
|---|---|---|---|---|
| **Microsoft Word** | Office Add-in (Office JS task pane). `Office.context.document.getFileAsync(Office.FileType.Pdf)` returns the doc as PDF slices — supported on Word for Windows, Mac, and web. POST to gateway; task pane can even embed the live preview UI in an iframe. | **High** | **M** (~1–2 wk incl. manifest, sideload docs) | **Build** (Phase 4). Requirements: add-in assets hosted over HTTPS (§4.4 solves), CORS on the gateway API. Distribution: sideload/central deploy; AppSource optional later. |
| **LibreOffice Writer** | `.oxt` extension in Python-UNO: `storeToURL` with the `writer_pdf_Export` filter to a temp file, `urllib` POST, toolbar button + menu item. No signing, no store, no HTTPS requirement. | **High** | **S** (~2–4 days) | **Build first** — cheapest, and doubles as the reference implementation of the sender pattern. |
| **Adobe Acrobat / Reader** | (a) Folder-level JavaScript + trusted functions: menu item calling `Net.HTTP` — privileged, requires per-machine trust configuration, brittle across Acrobat versions, effectively blocked in Reader. (b) Native C++ plugin SDK: per-platform builds, and Reader plugins require Adobe's RIKLA approval program. | **Low** | L–XL, ongoing maintenance | **Don't build.** The outcome is already achievable two better ways: **1)** the existing LabelDrop watched folder (Acrobat: File → Save As into `LabelDrop/In`); **2)** macOS Print-dialog PDF menu → Automator/Shortcuts workflow that POSTs to the gateway (elegant, ~1 day, works from *every* Mac app, not just Acrobat). On Windows, a "print to gateway" virtual printer (e.g., a PDF port writing into LabelDrop) achieves the same universality. Revisit a native Acrobat plugin only on explicit customer demand. |

The Acrobat row is the important strategic call: **universal OS-level capture (watched
folder + print-dialog workflows) beats per-app plugins** — it covers Adobe, browsers,
and every other input source at once, and it's mostly already built.

---

## 6. Roadmap

Ordering per the confirmed priority: UI refactor first — every other target inherits it.

| Phase | Scope | Exit criteria | Effort |
|---|---|---|---|
| **1. Design-system refactor** | Tokens (§2.2–2.5), Svelte+Vite migration, full component inventory with states, `<dialog>` replaces `prompt()`, empty/skeleton/error states, StatusPanel with guidance, keyboard map, SettingsPanel + `/api/settings`, light/dark, multi-stage Docker build. Write `DESIGN.md` as the tokens land. | Screenshot-verified on desktop + narrow viewport; all existing API flows + 76 tests green; container rebuilt; `impeccable audit` pass on the new UI | **L** (the big one) |
| **2. iOS / PWA** | Manifest + SW (app-shell cache), safe areas, touch/Pencil ergonomics, camera capture, sticky Print bar, TLS sidecar (Caddy internal CA) + trust-install docs, **Shortcuts recipe** shipped and documented | Installed to Home Screen on a real iPhone + iPad over HTTPS; crop-drag verified by touch; share-sheet Shortcut prints end-to-end | **M** |
| **3. Desktop installers** | pywebview + PyInstaller bundle; Inno Setup (Win) + DMG (macOS); code signing + notarization; first-run printer setup; CI release matrix. Tauri graduation as a follow-on decision | Signed installer installs on clean Win 11 + macOS VM, first-run connects to printer, prints; uninstall clean | **M–L** |
| **4. Plugins** | LibreOffice `.oxt` (reference sender) → Word Office-JS add-in (needs CORS + HTTPS from Phase 2) → macOS print-dialog workflow + Windows virtual-printer doc. No Acrobat plugin. | Each sender round-trips a real document to a physical label | **M** |

---

## 7. Risks & open questions

1. **TLS trust-install friction** (Phase 2): installing a local CA profile on iOS is a
   one-time but non-trivial user step. Mitigation: Tailscale option for zero-cert
   setups; very explicit docs with screenshots.
2. **PyInstaller × PyMuPDF freezing** (Phase 3): PyMuPDF bundles native libs; freezing
   is known-workable but needs early spike on both OSes before committing dates.
3. **Signing costs/identity**: Apple Developer Program + Windows signing require
   accounts and modest recurring cost — needed before Phase 3 release, not before dev.
4. **In-memory upload sessions**: uploads (not history) are lost on server restart —
   acceptable for a bench tool; revisit only if plugins introduce long-lived queues.
5. **Office add-in HTTPS hosting**: the add-in's own static assets must be HTTPS;
   simplest is serving them from the gateway behind the Phase-2 TLS layer.
6. **Scope discipline**: Phase 1 deliberately excludes new features (no batch
   printing, no multi-printer). The refactor is quality, not surface area.

---

*Plan grounded in the impeccable design skill (product register), PRODUCT.md, and the
current codebase (FastAPI + vanilla JS webapp, 76 passing tests, verified against a
Zebra ZD421 at 10.10.100.107).*
