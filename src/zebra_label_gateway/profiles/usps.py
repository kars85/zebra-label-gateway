"""USPS label profile: 4x6 label commonly embedded on a letter page; auto-crop."""

PROFILE = {
    "name": "usps",
    "description": "USPS shipping label (4x6, sometimes embedded on a letter page)",
    "page_type": "letter",
    "rotate": 0,
    "threshold": "standard",
    "crop": "auto",
}
