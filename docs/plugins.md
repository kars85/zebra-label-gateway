# Application Plugins

Plugins send the current document to the gateway from inside an authoring app.
Each is a thin sender: **render to PDF → POST `/api/upload` (optionally
`/api/print`)**. The gateway does the normalization and printing.

## LibreOffice Writer / Calc / Impress (`.oxt`)

Adds *Send to Label Gateway*, *Send & Print label*, and *Set Gateway address…*
under **Tools → Add-Ons**, plus a toolbar **Print label** button.

### Build & install

```bash
python plugins/libreoffice/build.py           # -> plugins/zebra-label-gateway.oxt
```

Install by double-clicking the `.oxt` (opens the Extension Manager), or:

```bash
"C:\Program Files\LibreOffice\program\unopkg.exe" add --force plugins\zebra-label-gateway.oxt
```

### Use

1. Open a document. If the gateway isn't at `http://localhost:8000`, set it via
   **Tools → Add-Ons → Set Gateway address…** (stored in
   `%APPDATA%\ZebraLabelGateway\gateway.txt`; also overridable with the
   `ZLG_GATEWAY_URL` env var).
2. **Send to Label Gateway** uploads the document as a PDF and leaves it in the
   gateway for review; **Send & Print label** uploads and prints immediately.

The macro picks the right PDF export filter by document type (Writer/Calc/
Impress/Draw). The gateway-communication code is unit-tested
(`tests/test_libreoffice_plugin.py`); the extension's install and macro
resolution are verified against a real LibreOffice via `unopkg` + UNO.

## Microsoft Word (Office add-in)

An Office-JS task-pane add-in adds a **Label Gateway** button to the Word ribbon.
It exports the document as PDF (`getFileAsync`) and posts it to `/api/upload`
(and `/api/print`). The task pane is served **by the gateway**, so its API calls
are same-origin — no CORS needed.

### Requirements

- The gateway reachable over **HTTPS** (`docs/tls-setup.md`) — Office add-ins
  are HTTPS-only. Replace `https://gateway.local` in `plugins/word/manifest.xml`
  with your TLS host.
- If you host the task pane on a *different* origin than the API, enable CORS on
  the gateway with `ZLG_CORS_ORIGINS=https://your-addin-host` (comma-separated).

### Sideload

1. Edit `plugins/word/manifest.xml` — set your gateway host in the URLs.
2. Word → **Home → Add-ins → More Add-ins → My Add-ins → Upload My Add-in** →
   pick `manifest.xml`. (Or use a shared-folder catalog / central deployment.)
3. Click **Label Gateway** on the ribbon → **Send** or **Send & Print**.

The manifest validates against Microsoft's Office add-in schema
(`npx office-addin-manifest validate plugins/word/manifest.xml`). The task pane
assets live in the gateway at `/static/addin/`.

## Adobe Acrobat

Intentionally **not** a plugin. Use the universal capture paths instead: the
LabelDrop watched folder (Acrobat: *Save As* into the input folder), or a
print-to-gateway workflow. These cover Adobe and every other app at once.
