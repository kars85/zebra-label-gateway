# Project Charter

## Mission

Zebra Label Gateway standardizes inconsistent shipping-label inputs into predictable 4x6 ZPL output for a Zebra ZD421 203dpi printer.

## Primary Principle

The app owns normalization and output. Adobe, Word, browsers, carrier sites, and retailer portals are input sources only.

## MVP

The first working milestone is a native ZPL test label that can be saved and sent over raw TCP to the printer.

## Non-goals For MVP

- Adobe or Word plugin integration
- Full UI
- Watched folders
- Retailer-specific crop profiles
- Automatic printing by default

## Development Principles

- Prove raw ZPL printing first.
- Prefer deterministic output over hidden magic.
- Preserve original files for troubleshooting.
- Make transformations visible before printing.
- Keep the workflow local-first.
