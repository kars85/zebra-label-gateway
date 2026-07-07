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

*Planned next* — an Office-JS task-pane add-in that exports the document as PDF
and posts it to the gateway. Requires the gateway to be reachable over HTTPS
(see `docs/tls-setup.md`) and a CORS allowance on the API.

## Adobe Acrobat

Intentionally **not** a plugin. Use the universal capture paths instead: the
LabelDrop watched folder (Acrobat: *Save As* into the input folder), or a
print-to-gateway workflow. These cover Adobe and every other app at once.
