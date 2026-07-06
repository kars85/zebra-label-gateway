# Retailer Profiles

Profiles are normalization presets for crop, rotation, and threshold behavior,
selected with `--profile` or in the watcher/UI.

Built-in profiles:

- `generic_4x6` - full-page 4x6 label, printed as-is (no crop).
- `generic_letter_embedded` - letter page with an embedded label; auto-crop.
- `ups`, `fedex`, `usps` - carrier labels, auto-crop (handles labels embedded on
  a letter page).
- `amazon_return` - return label on a letter page; auto-crop.

## Fields

- `page_type`: `label` (full 4x6) or `letter` (embedded label).
- `crop`: `auto` (largest content region), four `0..1` fractions
  `[left, top, right, bottom]`, or omitted/`null` for no crop.
- `rotate`: `0`, `90`, `180`, or `270` (clockwise).
- `threshold`: `light` (96), `standard` (128), `dark` (160), or an explicit
  `0-255`.

Override built-in profiles or add new ones in `config/profiles.yaml`; YAML values
merge over the built-in defaults. Profiles never hide irreversible
transformations -- a preview is always produced, and manual override remains
required for questionable inputs.
