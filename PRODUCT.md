# Product

## Register

product

## Users

A single operator (or small team) running a shipping/label station — a packing bench, home office, or small warehouse. They arrive with a label-like file (carrier PDF, retailer return page, screenshot) and one job: get a correct 4x6 label out of the Zebra ZD421, fast. They use the tool in short bursts between physical tasks (taping boxes, pulling stock), on whatever device is at hand: the bench PC, a MacBook, an iPad mounted at the station, or a phone.

## Product Purpose

Zebra Label Gateway normalizes inconsistent shipping-label inputs (PDFs, images, embedded letter-page labels) into reliable 4x6 ZPL output for a Zebra thermal printer. It owns the normalization step so Adobe, Word, browsers, and carrier portals can stay dumb input sources. Success: every label prints correctly the first time, and the operator trusts the preview enough to hit Print without squinting.

## Brand Personality

Industrial utility. Calm, precise, equipment-grade — the software equivalent of a well-built label printer: dense where density helps, instant feedback, zero decoration that doesn't serve the task. Three words: **precise, sturdy, quiet**.

## Anti-references

- "Vibe-coded" AI-generated dashboard aesthetics: gradient text, glassmorphism, hero metrics, identical card grids, cream/beige body backgrounds.
- Consumer shipping apps (Pirate Ship-style cheerfulness) — no mascots, no confetti, no marketing tone inside the tool.
- Enterprise-portal blandness — this is bench equipment, not an IT admin console.

## Design Principles

1. **The preview is the contract.** What the operator sees is bit-for-bit what the printer burns. Never decorate or soften the 1-bit preview; fidelity is the feature.
2. **One glance, one action.** Every screen state answers "can I print right now?" — printer status, render state, and the Print action must be readable from arm's length.
3. **Equipment, not app.** Controls behave like hardware: immediate, deterministic, stateful. No orchestrated loading choreography; no motion that doesn't convey state.
4. **Manual override is always visible.** Auto-crop and profiles do the work, but the operator can always see and correct what automation decided — trust is built by showing the machine's reasoning.
5. **Same tool everywhere.** Bench PC, Docker LAN page, iPad at the station, desktop installer — one interface vocabulary; capability, not layout, is what adapts.

## Accessibility & Inclusion

Best-effort, not gated: keep the cheap structural wins (visible focus, ≥4.5:1 body contrast, reduced-motion alternatives, 44px touch targets on coarse pointers) as defaults in the design system, but don't block shipping on formal WCAG audits.
