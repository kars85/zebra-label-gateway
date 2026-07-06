"""Amazon return label profile: letter page with an embedded label; auto-crop."""

PROFILE = {
    "name": "amazon_return",
    "description": "Amazon return label embedded on a letter-size page; auto-crop to content",
    "page_type": "letter",
    "rotate": 0,
    "threshold": "standard",
    "crop": "auto",
}
