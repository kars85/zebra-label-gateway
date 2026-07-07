# iOS Share-Sheet Shortcut (print from Mail / Files)

iOS Safari does not support the Web Share **Target** API, so a PWA can't appear
in the share sheet. The native equivalent is an **Apple Shortcut** that POSTs a
file to the gateway's API. It works from Mail, Files, Safari — anywhere the iOS
share sheet appears — and needs nothing installed on the gateway beyond what's
already there.

## Build it (Shortcuts app, ~2 minutes)

1. **Shortcuts → +** (new shortcut). Rename it e.g. *Print Label*.
2. Tap the info (ⓘ) button → enable **Show in Share Sheet**. Set *Accepted Types*
   to **Files** (and Images if you photograph labels).
3. Add action **Get Contents of URL**:
   - URL: `https://gateway.local/api/upload` (your TLS hostname from
     `docs/tls-setup.md`)
   - Method: **POST**
   - Request Body: **Form**
   - Add field → type **File**, name **`file`**, value **Shortcut Input**.
4. Add action **Get Dictionary Value** → key **`id`** from the previous result.
5. *(optional, auto-print)* Add another **Get Contents of URL**:
   - URL: `https://gateway.local/api/print`
   - Method: **POST**, Request Body: **JSON**
   - JSON: `{ "id": <the id from step 4>, "profile": "generic_4x6" }`
6. Add **Show Result** (or a notification) to confirm.

Now: in Mail, tap a label PDF → Share → **Print Label**. It uploads (and prints,
if you added step 5). To review before printing, skip step 5 and instead open the
PWA — the upload is already in your session/history.

## API contract (for reference)

| Endpoint | Method | Body | Returns |
|---|---|---|---|
| `/api/upload` | POST | multipart form, field `file` | `{ id, name, width, height, pages, suggested_profile }` |
| `/api/render` | POST | JSON `{ id, profile, page?, rotate?, threshold?, crop_mode?, crop? }` | PNG preview (`X-Zpl-Bytes` header) |
| `/api/print` | POST | JSON `{ id, profile, ... }` | `{ ok, detail, zpl_bytes }` |

`crop_mode` is one of `profile` / `auto` / `manual` / `none`; for `manual`,
`crop` is `[left, top, right, bottom]` fractions in 0..1.
