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

## Post-MVP Status

The MVP is complete, and the following have since been implemented: PDF/image
normalization to raster ZPL, retailer crop profiles, the LabelDrop watched
folder, a local preview web UI, and a Windows print-queue transport. Automatic
printing remains disabled by default; a preview is always produced first. Adobe
and Word plugin integration remains out of scope -- those stay input sources
only.

## Development Principles

- Prove raw ZPL printing first.
- Prefer deterministic output over hidden magic.
- Preserve original files for troubleshooting.
- Make transformations visible before printing.
- Keep the workflow local-first.
