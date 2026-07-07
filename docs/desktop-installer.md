# Windows Desktop Installer

The desktop app runs the gateway locally in a native window (pywebview /
WebView2), with no Python or Docker needed on the target machine. It bundles the
FastAPI backend, PyMuPDF/Pillow, and the built frontend into one folder, wrapped
in an NSIS installer.

Scope: **Windows / NSIS only.** No Microsoft Store, no macOS/iOS build.

## What the user gets

- `ZebraLabelGateway-Setup.exe` → installs to `Program Files`, Start-menu and
  desktop shortcuts, and a proper entry in *Apps & features* (uninstaller).
- On launch it starts the server on a private localhost port and opens the app
  window. Printer host/port is set in-app via **Settings** (no env vars needed).
- History and trained profiles persist in
  `%LOCALAPPDATA%\ZebraLabelGateway\data` and survive reinstalls.

## Build it

Prereqs: Node/npm, a Python env with the extras, and NSIS (`makensis`).

```powershell
pip install -e ".[web,desktop]"
winget install NSIS.NSIS      # or download from nsis.sourceforge.io
pwsh packaging\build.ps1      # -Makensis "C:\path\to\makensis.exe" if not on PATH
```

The script runs the three stages and drops `packaging\ZebraLabelGateway-Setup.exe`:

1. **Frontend** — `npm run build` (Vite → `webapp/static/dist`).
2. **Freeze** — `pyinstaller packaging/desktop.spec` (onedir in `packaging/dist`).
3. **Installer** — `makensis packaging/installer.nsi`.

`src/zebra_label_gateway/desktop.py` is the entry point; run it with
`--server-only` to smoke-test the backend headlessly.

## Requirements on the target machine

- **WebView2 runtime** — preinstalled on Windows 11 and current Windows 10. If
  absent, install the Evergreen runtime from Microsoft (the installer can be
  extended to bundle the bootstrapper if needed).

## Not signed

The build is unsigned, so SmartScreen shows a "unknown publisher" warning on
first run (users click *More info → Run anyway*). Add Authenticode signing of
`ZebraLabelGateway.exe` and the setup EXE before wider distribution.
