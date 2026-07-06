"""UPS label profile: often a 4x6 label placed on a letter page; auto-crop."""

PROFILE = {
    "name": "ups",
    "description": "UPS shipping label (4x6, sometimes embedded on a letter page)",
    "page_type": "letter",
    "rotate": 0,
    "threshold": "standard",
    "crop": "auto",
}
