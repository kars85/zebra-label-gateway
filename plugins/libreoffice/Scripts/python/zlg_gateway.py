"""Zebra Label Gateway — LibreOffice macro.

Exports the current document to PDF and sends it to the gateway's /api/upload
(optionally /api/print). Registered as toolbar/menu items by Addons.xcu.

The HTTP helper (_upload_and_maybe_print) is pure stdlib so it can be tested
outside LibreOffice; the UNO-dependent bits import ``uno`` lazily.
"""

import json
import os
import uuid
from pathlib import Path

DEFAULT_URL = "http://localhost:8000"


# --------------------------------------------------------------------------- #
# Gateway communication (no UNO — unit-testable)
# --------------------------------------------------------------------------- #
def _config_path() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "ZebraLabelGateway" / "gateway.txt"


def gateway_url() -> str:
    """Resolve the gateway base URL: env var, saved config, then default."""
    env = os.environ.get("ZLG_GATEWAY_URL")
    if env:
        return env.rstrip("/")
    cfg = _config_path()
    if cfg.exists():
        text = cfg.read_text(encoding="utf-8").strip()
        if text:
            return text.rstrip("/")
    return DEFAULT_URL


def save_gateway_url(url: str) -> None:
    cfg = _config_path()
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(url.strip().rstrip("/"), encoding="utf-8")


def _upload_and_maybe_print(base_url: str, pdf_bytes: bytes, filename: str,
                            do_print: bool, profile: str = "generic_4x6") -> str:
    """POST the PDF to the gateway; return a human-readable result string."""
    import urllib.request

    boundary = "----zlg" + uuid.uuid4().hex
    body = b"".join([
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{filename}"\r\nContent-Type: application/pdf\r\n\r\n'.encode(),
        pdf_bytes,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())

    detail = f"Uploaded {filename} ({result['width']}×{result['height']}, {result['pages']} page(s))."
    if not do_print:
        return detail + "\nReview and print it in the Label Gateway."

    print_req = urllib.request.Request(
        base_url.rstrip("/") + "/api/print",
        data=json.dumps({"id": result["id"], "profile": profile}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(print_req, timeout=30) as resp:
        printed = json.loads(resp.read())
    return detail + "\n" + printed.get("detail", "Printed.")


# --------------------------------------------------------------------------- #
# UNO glue (runs inside LibreOffice)
# --------------------------------------------------------------------------- #
def _pdf_filter(doc) -> str:
    checks = [
        ("com.sun.star.text.TextDocument", "writer_pdf_Export"),
        ("com.sun.star.sheet.SpreadsheetDocument", "calc_pdf_Export"),
        ("com.sun.star.presentation.PresentationDocument", "impress_pdf_Export"),
        ("com.sun.star.drawing.DrawingDocument", "draw_pdf_Export"),
    ]
    for service, filt in checks:
        if doc.supportsService(service):
            return filt
    return "writer_pdf_Export"


def _export_current_pdf():
    import tempfile

    import uno
    from com.sun.star.beans import PropertyValue

    doc = XSCRIPTCONTEXT.getDocument()  # noqa: F821 (provided by LO)
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    prop = PropertyValue()
    prop.Name = "FilterName"
    prop.Value = _pdf_filter(doc)
    doc.storeToURL(uno.systemPathToFileUrl(tmp.name), (prop,))
    data = Path(tmp.name).read_bytes()
    try:
        os.unlink(tmp.name)
    except OSError:
        pass
    title = getattr(doc, "Title", None) or "document"
    return data, f"{title}.pdf"


def _message(text: str, title: str = "Zebra Label Gateway") -> None:
    import uno
    from com.sun.star.awt.MessageBoxButtons import BUTTONS_OK

    ctx = uno.getComponentContext()
    smgr = ctx.getServiceManager()
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    frame = XSCRIPTCONTEXT.getDesktop().getCurrentFrame()  # noqa: F821
    parent = frame.getContainerWindow() if frame else None
    box = toolkit.createMessageBox(parent, "infobox", BUTTONS_OK, title, text)
    box.execute()


def _input(prompt: str, default: str) -> str | None:
    """Minimal AWT input box; returns the entered text or None if cancelled."""
    import uno
    from com.sun.star.awt import Rectangle

    ctx = uno.getComponentContext()
    smgr = ctx.getServiceManager()
    dialog_model = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialogModel", ctx)
    dialog_model.setPropertyValue("Width", 240)
    dialog_model.setPropertyValue("Height", 70)
    dialog_model.setPropertyValue("Title", "Zebra Label Gateway")

    label = dialog_model.createInstance("com.sun.star.awt.UnoControlFixedTextModel")
    label.setPropertyValue("PositionX", 8)
    label.setPropertyValue("PositionY", 6)
    label.setPropertyValue("Width", 224)
    label.setPropertyValue("Height", 14)
    label.setPropertyValue("Label", prompt)
    dialog_model.insertByName("lbl", label)

    edit = dialog_model.createInstance("com.sun.star.awt.UnoControlEditModel")
    edit.setPropertyValue("PositionX", 8)
    edit.setPropertyValue("PositionY", 22)
    edit.setPropertyValue("Width", 224)
    edit.setPropertyValue("Height", 16)
    edit.setPropertyValue("Text", default)
    dialog_model.insertByName("edit", edit)

    for name, label_text, x, action in (("ok", "OK", 130, 1), ("cancel", "Cancel", 182, 0)):
        btn = dialog_model.createInstance("com.sun.star.awt.UnoControlButtonModel")
        btn.setPropertyValue("PositionX", x)
        btn.setPropertyValue("PositionY", 46)
        btn.setPropertyValue("Width", 50)
        btn.setPropertyValue("Height", 16)
        btn.setPropertyValue("Label", label_text)
        btn.setPropertyValue("PushButtonType", action)
        dialog_model.insertByName(name, btn)

    dialog = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialog", ctx)
    dialog.setModel(dialog_model)
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    dialog.setVisible(False)
    dialog.createPeer(toolkit, None)
    _ = Rectangle
    ok = dialog.execute()
    value = dialog.getControl("edit").getModel().Text
    dialog.dispose()
    return value if ok else None


def _run(do_print: bool) -> None:
    try:
        pdf, name = _export_current_pdf()
        result = _upload_and_maybe_print(gateway_url(), pdf, name, do_print)
        _message(result)
    except Exception as exc:  # noqa: BLE001
        _message(f"Could not reach the Label Gateway at {gateway_url()}.\n\n{exc}", "Error")


# Entry points referenced by Addons.xcu -------------------------------------- #
def send_to_gateway(*_args):
    _run(do_print=False)


def send_and_print(*_args):
    _run(do_print=True)


def set_gateway_url(*_args):
    current = gateway_url()
    value = _input("Label Gateway address:", current)
    if value:
        save_gateway_url(value)
        _message(f"Gateway set to {value.rstrip('/')}")


g_exportedScripts = (send_to_gateway, send_and_print, set_gateway_url)
