# PyInstaller spec for the Zebra Label Gateway desktop app (onedir).
# Build:  pyinstaller packaging/desktop.spec --noconfirm \
#           --distpath packaging/dist --workpath packaging/build
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

PROJ = os.path.abspath(os.getcwd())

datas, binaries, hiddenimports = [], [], []

# Collect packages that need their data/native libs/submodules bundled.
for pkg in ("uvicorn", "fitz", "pymupdf", "webview"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

hiddenimports += collect_submodules("uvicorn")
hiddenimports += ["zebra_label_gateway.webapp.server"]

# Bundle app resources: read-only config + the built frontend static assets.
datas += [
    (os.path.join(PROJ, "config"), "config"),
    (os.path.join(PROJ, "src", "zebra_label_gateway", "webapp", "static"),
     "zebra_label_gateway/webapp/static"),
]

a = Analysis(
    [os.path.join(PROJ, "src", "zebra_label_gateway", "desktop.py")],
    pathex=[os.path.join(PROJ, "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    excludes=["tkinter", "pytest", "PyInstaller"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ZebraLabelGateway",
    console=False,
    icon=os.path.join(PROJ, "packaging", "app.ico") if os.path.exists(
        os.path.join(PROJ, "packaging", "app.ico")) else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="ZebraLabelGateway",
)
