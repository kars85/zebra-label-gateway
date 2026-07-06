[CmdletBinding(SupportsShouldProcess)]
param(
    [string] $BasePath = "C:\Dev",
    [string] $RepoName = "zebra-label-gateway",
    [string] $RepoDescription = "Local middleware for normalizing inconsistent shipping labels into reliable 4x6 ZPL output for a Zebra ZD421 203dpi printer.",
    [string] $PrinterIP = "192.168.x.x",
    [switch] $ForceScaffold,
    [switch] $SkipGitHub,
    [switch] $SkipInstall,
    [switch] $SkipPush
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string] $Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Warn {
    param([string] $Message)
    Write-Warning $Message
}

function Invoke-External {
    param(
        [Parameter(Mandatory)] [string] $Command,
        [Parameter(ValueFromRemainingArguments)] [string[]] $Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
}

function Invoke-ExternalText {
    param(
        [Parameter(Mandatory)] [string] $Command,
        [Parameter(ValueFromRemainingArguments)] [string[]] $Arguments
    )

    $output = & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
    return $output
}

function Test-CommandExists {
    param([string] $Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-GitRepo {
    param([string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $result = & git -C $Path rev-parse --is-inside-work-tree 2>$null
    return ($LASTEXITCODE -eq 0 -and ($result -join '').Trim() -eq 'true')
}

function Ensure-OriginRemote {
    param(
        [string] $RepoPath,
        [string] $RemoteUrl
    )

    $existing = & git -C $RepoPath remote get-url origin 2>$null
    if ($LASTEXITCODE -eq 0 -and $existing) {
        if (($existing -join '').Trim() -ne $RemoteUrl) {
            Write-Warn "Existing origin is '$existing'. Leaving it unchanged. Expected '$RemoteUrl'."
        }
        return
    }

    Invoke-External git -C $RepoPath remote add origin $RemoteUrl
}

function Ensure-GitHubRepo {
    param(
        [string] $Owner,
        [string] $RepoName,
        [string] $Description
    )

    if ($SkipGitHub) { return }

    Write-Step "Ensuring GitHub repository $Owner/$RepoName exists"
    & gh repo view "$Owner/$RepoName" --json name *> $null
    if ($LASTEXITCODE -eq 0) { return }

    Invoke-External gh repo create "$Owner/$RepoName" --public --description $Description
}

function New-ScaffoldFile {
    param(
        [string] $RelativePath,
        [string] $Content
    )

    $target = Join-Path $script:RepoPath $RelativePath
    $parent = Split-Path -Parent $target
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }

    if ((Test-Path -LiteralPath $target) -and -not $ForceScaffold) {
        return
    }

    Set-Content -Path $target -Value $Content -Encoding UTF8
}

function New-ScaffoldTree {
    Write-Step "Creating project scaffold"
    $dirs = @(
        'docs',
        'src/zebra_label_gateway/profiles',
        'src/zebra_label_gateway/ui',
        'tests/fixtures',
        'samples',
        'config',
        'scripts',
        '.github/ISSUE_TEMPLATE',
        '.github/workflows'
    )
    foreach ($dir in $dirs) {
        New-Item -ItemType Directory -Force -Path (Join-Path $script:RepoPath $dir) | Out-Null
    }

    New-ScaffoldFile '.gitignore' @"
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
.venv/
venv/
env/
pip-wheel-metadata/
dist/
build/
*.egg-info/

# Test/cache
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Local app data
LabelDrop/
logs/
*.log

# Generated samples/output
samples/*.zpl
samples/*.png
samples/*.pdf
!samples/README.md
!samples/.gitkeep

# Secrets/local config
config/local.yaml
.env
"@

    New-ScaffoldFile 'README.md' @"
# Zebra Label Gateway

Local middleware for normalizing inconsistent shipping labels into reliable 4x6 ZPL output for a Zebra ZD421 203dpi printer.

## Purpose

Shipping labels arrive in inconsistent formats: 4x6 PDFs, letter-size PDFs with embedded labels, screenshots, browser dialogs, Adobe output, and Word documents. Zebra Label Gateway owns normalization so these inputs become one predictable 4x6 Zebra print job.

This project is not starting as an Adobe, Word, or browser plugin. Those tools are treated as inconsistent input sources.

## Target Printer

- Printer: Zebra / ZDesigner ZD421
- DPI: 203
- Language: ZPL
- Label size: 4x6 inches
- Dot canvas: 812x1218 dots

## MVP Goal

Generate one known-good ZPL test label, send it to the ZD421, and confirm printer connection, orientation, label size, and output.

## Quick Start

````powershell
cd C:\Dev\zebra-label-gateway
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest
python .\src\zebra_label_gateway\print_tcp.py --host 192.168.x.x --save-only
python .\src\zebra_label_gateway\print_tcp.py --host <actual-printer-ip>
````

Optional port test:

````powershell
Test-NetConnection <actual-printer-ip> -Port 9100
````

## Safety Note

Do not commit real labels or private shipping data, including names, addresses, tracking numbers, barcodes, QR codes, order numbers, or screenshots of real shipments.
"@

    New-ScaffoldFile 'docs/project-charter.md' @"
# Project Charter

Zebra Label Gateway standardizes inconsistent shipping-label inputs into predictable 4x6 ZPL output for a Zebra ZD421 203dpi printer.

The app owns normalization and output. Adobe, Word, browsers, carrier sites, and retailer portals are input sources only.

The MVP is a native ZPL test label that can be saved and sent over raw TCP to the printer.
"@
    New-ScaffoldFile 'docs/architecture.md' @"
# Architecture

````text
input source -> detection -> normalization -> preview -> ZPL output -> printer transport
````

Initial scope is native ZPL generation and raw TCP transport.
"@
    New-ScaffoldFile 'docs/printer-setup.md' @"
# Printer Setup

- Model: Zebra / ZDesigner ZD421
- DPI: 203
- Language: ZPL
- Label: 4x6 inches
- Canvas: 812x1218 dots

Generate a test file without printing:

````powershell
python .\src\zebra_label_gateway\print_tcp.py --host 192.168.x.x --save-only
````

Check network reachability:

````powershell
Test-NetConnection <actual-printer-ip> -Port 9100
````

Print the test label:

````powershell
python .\src\zebra_label_gateway\print_tcp.py --host <actual-printer-ip>
````
"@
    New-ScaffoldFile 'docs/label-normalization.md' @"
# Label Normalization

Normalization converts inconsistent label-like inputs into a single 812x1218 dot canvas.

Future behavior includes detection, preservation of original files, rendering, profile defaults, manual crop and rotation overrides, and preview before printing.
"@
    New-ScaffoldFile 'docs/zpl-output.md' @"
# ZPL Output

The first supported output is a native ZPL test label using `^PW812` and `^LL1218`.

Future raster output will encode normalized 1-bit images as ZPL graphics payloads.
"@
    New-ScaffoldFile 'docs/retailer-profiles.md' @"
# Retailer Profiles

Retailer and carrier profiles are future configuration presets for crop, rotation, threshold, and scaling behavior.
"@

    New-ScaffoldFile 'config/default.yaml' @"
printer:
  name: "ZDesigner ZD421-203dpi ZPL"
  dpi: 203
  label_width_in: 4
  label_height_in: 6
  output_width_dots: 812
  output_height_dots: 1218

  connection_type: "tcp"

  tcp_host: "$PrinterIP"
  tcp_port: 9100

  windows_queue_name: "Zebra ZD421 - 4x6 Shipping"

folders:
  input: "C:/Users/Karson/LabelDrop/In"
  printed: "C:/Users/Karson/LabelDrop/Printed"
  failed: "C:/Users/Karson/LabelDrop/Failed"

printing:
  preview_before_print: true
  auto_print: false
"@
    New-ScaffoldFile 'config/profiles.yaml' @"
profiles:
  generic_4x6:
    description: "Full-page 4x6 label"
    page_type: "label"
    rotate: 0
    threshold: "standard"

  generic_letter_embedded:
    description: "Letter-size page with embedded shipping label"
    page_type: "letter"
    rotate: 0
    threshold: "standard"
"@

    New-ScaffoldFile 'pyproject.toml' @"
[project]
name = "zebra-label-gateway"
version = "0.1.0"
description = "Local middleware for normalizing inconsistent shipping labels into reliable 4x6 ZPL output for Zebra printers."
requires-python = ">=3.11"
dependencies = [
    "pymupdf",
    "pillow",
    "pyyaml",
    "watchdog"
]

[project.optional-dependencies]
dev = [
    "pytest"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
"@
    New-ScaffoldFile 'requirements.txt' @"
pymupdf
pillow
pyyaml
watchdog
"@
    New-ScaffoldFile 'LICENSE' @"
MIT License

Copyright (c) 2026 Karson

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.
"@

    New-ScaffoldFile 'src/zebra_label_gateway/__init__.py' @"
"""Zebra Label Gateway package."""

__version__ = "0.1.0"
"@
    New-ScaffoldFile 'src/zebra_label_gateway/input_detection.py' @"
"""Input type detection for label-like files."""

from __future__ import annotations

from pathlib import Path

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
ZPL_EXTENSIONS = {".zpl", ".txt"}


def detect_input_type(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in PDF_EXTENSIONS:
        return "pdf"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in ZPL_EXTENSIONS:
        return "zpl"
    return "unknown"
"@
    New-ScaffoldFile 'src/zebra_label_gateway/zpl_encoder.py' @"
"""ZPL generation helpers."""

from __future__ import annotations

LABEL_WIDTH_DOTS = 812
LABEL_HEIGHT_DOTS = 1218


def build_test_label_zpl() -> str:
    """Return a deterministic native ZPL 4x6-ish test label."""
    return "\n".join([
        "^XA",
        "^PW812",
        "^LL1218",
        "^FO40,40^GB730,1130,4^FS",
        "^FO80,100^A0N,55,55^FDZebra Label Gateway^FS",
        "^FO80,180^A0N,35,35^FDZD421 203dpi ZPL Test^FS",
        "^FO80,260^BY3",
        "^BCN,120,Y,N,N",
        "^FD123456789012^FS",
        "^FO80,450^A0N,35,35^FDIf this printed correctly:^FS",
        "^FO100,510^A0N,32,32^FD- Printer connection works^FS",
        "^FO100,560^A0N,32,32^FD- ZPL is being accepted^FS",
        "^FO100,610^A0N,32,32^FD- Label size is close to 4x6^FS",
        "^XZ",
        "",
    ])
"@
    New-ScaffoldFile 'src/zebra_label_gateway/printer_tcp.py' @"
"""Raw TCP printer transport."""

from __future__ import annotations

import socket

DEFAULT_ZPL_PORT = 9100


def send_zpl_tcp(zpl: str, host: str, port: int = DEFAULT_ZPL_PORT, timeout: float = 10.0) -> None:
    """Send a ZPL payload to a networked Zebra printer."""
    payload = zpl.encode("ascii")
    with socket.create_connection((host, port), timeout=timeout) as connection:
        connection.sendall(payload)
"@
    New-ScaffoldFile 'src/zebra_label_gateway/print_tcp.py' @"
"""Generate and optionally send a native ZPL test label over raw TCP."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zebra_label_gateway.printer_tcp import DEFAULT_ZPL_PORT, send_zpl_tcp
from zebra_label_gateway.zpl_encoder import build_test_label_zpl

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = REPO_ROOT / "samples" / "test-label.zpl"


def save_zpl(zpl: str, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(zpl, encoding="ascii", newline="\n")
    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and optionally print a Zebra ZPL test label.")
    parser.add_argument("--host", required=True, help="Printer hostname or IP address.")
    parser.add_argument("--port", type=int, default=DEFAULT_ZPL_PORT, help="Raw TCP printer port. Defaults to 9100.")
    parser.add_argument("--save-only", action="store_true", help="Save samples/test-label.zpl without printing.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    zpl = build_test_label_zpl()
    output_path = save_zpl(zpl)
    print(f"Saved test label to {output_path}")
    if args.save_only:
        print("Save-only mode selected; not sending to printer.")
        return 0
    send_zpl_tcp(zpl, args.host, args.port)
    print(f"Sent test label to {args.host}:{args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"@

    foreach ($module in @('app','watcher','pdf_renderer','image_processor','crop_detector','printer_windows')) {
        $func = 'placeholder'
        New-ScaffoldFile "src/zebra_label_gateway/$module.py" "`"`"`Future $module support.`"`"`n`n`ndef $func() -> None:`n    raise NotImplementedError(`"$module is planned for a later phase.`")"
    }

    New-ScaffoldFile 'src/zebra_label_gateway/profiles/__init__.py' @"
"""Profile placeholders."""
"@
    foreach ($profile in @('generic_4x6','generic_letter_embedded','amazon_return','ups','fedex','usps')) {
        New-ScaffoldFile "src/zebra_label_gateway/profiles/$profile.py" "`"`"`$profile profile placeholder.`"`"`n`nPROFILE = {`"name`": `"$profile`"}"
    }
    New-ScaffoldFile 'src/zebra_label_gateway/ui/__init__.py' @"
"""UI package."""
"@
    New-ScaffoldFile 'src/zebra_label_gateway/ui/web.py' @"
"""Future local web UI."""


def run_web_ui() -> None:
    raise NotImplementedError("The preview UI is planned for a later phase.")
"@

    New-ScaffoldFile 'tests/test_input_detection.py' @"
from zebra_label_gateway.input_detection import detect_input_type


def test_detects_pdf() -> None:
    assert detect_input_type("label.PDF") == "pdf"


def test_detects_images() -> None:
    assert detect_input_type("label.png") == "image"
    assert detect_input_type("label.jpeg") == "image"


def test_detects_zpl() -> None:
    assert detect_input_type("label.zpl") == "zpl"


def test_unknown_extension() -> None:
    assert detect_input_type("label.docx") == "unknown"
"@
    New-ScaffoldFile 'tests/test_zpl_encoder.py' @"
from zebra_label_gateway.print_tcp import save_zpl
from zebra_label_gateway.zpl_encoder import build_test_label_zpl


def test_test_label_zpl_contains_expected_canvas() -> None:
    zpl = build_test_label_zpl()
    assert "^XA" in zpl
    assert "^PW812" in zpl
    assert "^LL1218" in zpl
    assert "^XZ" in zpl


def test_test_label_zpl_contains_barcode() -> None:
    zpl = build_test_label_zpl()
    assert "^BCN,120,Y,N,N" in zpl
    assert "^FD123456789012^FS" in zpl


def test_save_zpl_writes_ascii_file(tmp_path) -> None:
    output_path = tmp_path / "test-label.zpl"
    saved_path = save_zpl(build_test_label_zpl(), output_path)
    assert saved_path == output_path
    assert output_path.read_text(encoding="ascii").startswith("^XA")
"@
    New-ScaffoldFile 'tests/test_pdf_renderer.py' @"
import pytest

from zebra_label_gateway.pdf_renderer import placeholder


def test_pdf_renderer_is_future_work() -> None:
    with pytest.raises(NotImplementedError):
        placeholder()
"@
    New-ScaffoldFile 'tests/test_crop_detector.py' @"
import pytest

from zebra_label_gateway.crop_detector import placeholder


def test_crop_detector_is_future_work() -> None:
    with pytest.raises(NotImplementedError):
        placeholder()
"@
    New-ScaffoldFile 'tests/fixtures/README.md' @"
# Test Fixtures

Do not store real shipping labels, addresses, tracking numbers, barcodes, or QR codes in this directory.
"@
    New-ScaffoldFile 'tests/fixtures/sample-placeholder.txt' @"
Placeholder fixture. Do not replace with private label data.
"@
    New-ScaffoldFile 'samples/README.md' @"
# Samples

Generated output files can be written here during local testing.

Do not commit real labels or private shipping data.
"@
    New-ScaffoldFile 'samples/.gitkeep' ""

    New-ScaffoldFile 'scripts/install-dev.ps1' @"
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
`$ErrorActionPreference = "Stop"

`$RepoRoot = Split-Path -Parent `$PSScriptRoot
Set-Location `$RepoRoot

py -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -e ".[dev]"
"@
    New-ScaffoldFile 'scripts/run-dev.ps1' @"
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
`$ErrorActionPreference = "Stop"

`$RepoRoot = Split-Path -Parent `$PSScriptRoot
Set-Location `$RepoRoot

& .\.venv\Scripts\python.exe -m zebra_label_gateway.app
"@
    New-ScaffoldFile 'scripts/print-test-label.ps1' @"
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] `$HostName,
    [int] `$Port = 9100,
    [switch] `$SaveOnly
)

Set-StrictMode -Version Latest
`$ErrorActionPreference = "Stop"

`$RepoRoot = Split-Path -Parent `$PSScriptRoot
Set-Location `$RepoRoot

`$ArgsList = @(".\src\zebra_label_gateway\print_tcp.py", "--host", `$HostName, "--port", `$Port)
if (`$SaveOnly) { `$ArgsList += "--save-only" }
& .\.venv\Scripts\python.exe @ArgsList
"@
    New-ScaffoldFile 'scripts/calibrate-notes.md' @"
# Calibration Notes

Record printer baseline observations here.
"@

    New-ScaffoldFile '.github/workflows/tests.yml' @"
name: Tests

on:
  push:
  pull_request:

jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install package
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Run tests
        run: pytest
"@
    New-ScaffoldFile '.github/ISSUE_TEMPLATE/bug_report.md' "---`nname: Bug report`nabout: Report incorrect label processing or printing behavior`ntitle: `"`"`nlabels: `"type:bug`"`nassignees: `"`"`n---`n`n## Problem`n`n## Steps To Reproduce`n`n## Expected Result`n`n## Actual Result`n"
    New-ScaffoldFile '.github/ISSUE_TEMPLATE/feature_request.md' "---`nname: Feature request`nabout: Request a new workflow or capability`ntitle: `"`"`nlabels: `"type:feature`"`nassignees: `"`"`n---`n`n## Goal`n`n## Proposed Behavior`n`n## Acceptance Criteria`n"
    New-ScaffoldFile '.github/ISSUE_TEMPLATE/retailer_profile_request.md' "---`nname: Retailer profile request`nabout: Request support for a retailer or carrier label layout`ntitle: `"`"`nlabels: `"area:profiles,type:feature`"`nassignees: `"`"`n---`n`n## Retailer Or Carrier`n`n## Input Format`n`nDo not attach real labels with personal data.`n"
}

function Install-And-Test {
    if ($SkipInstall) { return }
    Write-Step "Creating virtual environment and installing dependencies"
    Set-Location $script:RepoPath
    Invoke-External py -m venv .venv
    Invoke-External (Join-Path $script:RepoPath '.venv/Scripts/python.exe') -m pip install --upgrade pip
    Invoke-External (Join-Path $script:RepoPath '.venv/Scripts/pip.exe') install -e ".[dev]"
    Invoke-External (Join-Path $script:RepoPath '.venv/Scripts/python.exe') -m pytest
    Invoke-External (Join-Path $script:RepoPath '.venv/Scripts/python.exe') (Join-Path $script:RepoPath 'src/zebra_label_gateway/print_tcp.py') --host $PrinterIP --save-only
}

function Commit-And-Push {
    if ($SkipPush) { return }
    Write-Step "Committing and pushing scaffold changes"
    Set-Location $script:RepoPath
    Invoke-External git add -- .
    $status = Invoke-ExternalText git status --porcelain
    if ($status) {
        Invoke-External git commit -m "chore: bootstrap project skeleton"
    }
    Invoke-External git push -u origin main
}

function Ensure-GitHubLabels {
    param([string] $Owner, [string] $RepoName)
    if ($SkipGitHub) { return }
    Write-Step "Ensuring GitHub labels"
    $labels = @(
        @{Name='type:bug'; Color='d73a4a'; Description='Bug or defect'},
        @{Name='type:feature'; Color='0e8a16'; Description='Feature work'},
        @{Name='type:docs'; Color='0075ca'; Description='Documentation'},
        @{Name='type:research'; Color='5319e7'; Description='Research'},
        @{Name='type:test'; Color='fbca04'; Description='Testing'},
        @{Name='area:printer'; Color='1d76db'; Description='Printer connection and setup'},
        @{Name='area:zpl'; Color='1d76db'; Description='ZPL output'},
        @{Name='area:pdf'; Color='1d76db'; Description='PDF handling'},
        @{Name='area:image'; Color='1d76db'; Description='Image handling'},
        @{Name='area:ui'; Color='1d76db'; Description='User interface'},
        @{Name='area:profiles'; Color='1d76db'; Description='Retailer and carrier profiles'},
        @{Name='area:windows'; Color='1d76db'; Description='Windows workflow'},
        @{Name='priority:high'; Color='b60205'; Description='High priority'},
        @{Name='priority:medium'; Color='fbca04'; Description='Medium priority'},
        @{Name='priority:low'; Color='0e8a16'; Description='Low priority'},
        @{Name='status:blocked'; Color='000000'; Description='Blocked'},
        @{Name='status:needs-testing'; Color='c5def5'; Description='Needs testing'}
    )
    foreach ($label in $labels) {
        & gh label create $label.Name --repo "$Owner/$RepoName" --color $label.Color --description $label.Description *> $null
        if ($LASTEXITCODE -ne 0) {
            & gh label edit $label.Name --repo "$Owner/$RepoName" --color $label.Color --description $label.Description *> $null
        }
    }
}

function Ensure-GitHubMilestones {
    param([string] $Owner, [string] $RepoName)
    if ($SkipGitHub) { return }
    Write-Step "Ensuring GitHub milestones"
    $existing = @(gh api "repos/$Owner/$RepoName/milestones?state=all" --paginate --jq '.[].title' 2>$null)
    $milestones = @(
        'M0 - Project Skeleton',
        'M1 - Printer Baseline',
        'M2 - PDF/Image Normalization',
        'M3 - ZPL Raster Output',
        'M4 - Preview and Manual Crop',
        'M5 - Watched Folder Workflow',
        'M6 - Retailer Profiles',
        'M7 - Packaging'
    )
    foreach ($milestone in $milestones) {
        if ($existing -notcontains $milestone) {
            Invoke-External gh api "repos/$Owner/$RepoName/milestones" -f title=$milestone | Out-Null
        }
    }
}

function Ensure-GitHubIssues {
    param([string] $Owner, [string] $RepoName)
    if ($SkipGitHub) { return }
    Write-Step "Ensuring starter issues"
    $existingTitles = @(gh issue list --repo "$Owner/$RepoName" --state all --limit 200 --json title --jq '.[].title' 2>$null)
    $issues = @(
        @{Title='Confirm printer connection'; Milestone='M1 - Printer Baseline'; Labels=@('area:printer','priority:high'); Body=@"
## Goal

Confirm how the ZD421 is connected and whether raw ZPL can be sent directly.

## Tasks

- [ ] Determine whether printer is networked or USB-only
- [ ] Find printer IP if networked
- [ ] Confirm port 9100 is reachable
- [ ] Send basic ZPL test label
- [ ] Document result in docs/printer-setup.md

## Acceptance Criteria

A known-good ZPL test label prints from this repo.
"@},
        @{Title='Add test ZPL generator'; Milestone='M1 - Printer Baseline'; Labels=@('area:zpl','type:feature','priority:high'); Body=@"
## Goal

Create a simple script that generates a 4x6 ZPL test label.

## Tasks

- [ ] Generate test label ZPL
- [ ] Save output to samples/test-label.zpl
- [ ] Include text, border, and barcode
- [ ] Confirm label is close to 4x6

## Acceptance Criteria

Running the script produces a reusable ZPL test file.
"@},
        @{Title='Document printer baseline'; Milestone='M1 - Printer Baseline'; Labels=@('type:docs','area:printer'); Body=@"
## Goal

Document the known-good printer settings.

## Tasks

- [ ] Printer model
- [ ] DPI
- [ ] Label size
- [ ] Connection method
- [ ] IP address or queue name
- [ ] Media type
- [ ] Calibration notes
- [ ] Darkness/speed notes

## Acceptance Criteria

A future user can reproduce the working printer setup.
"@},
        @{Title='Add PDF renderer'; Milestone='M2 - PDF/Image Normalization'; Labels=@('area:pdf','type:feature'); Body=@"
## Goal

Render PDF pages into images at the correct resolution for 4x6 normalization.

## Tasks

- [ ] Load PDF input
- [ ] Detect page count
- [ ] Render first page to image
- [ ] Save preview PNG
- [ ] Preserve barcode clarity

## Acceptance Criteria

A PDF label can be rendered to a preview image.
"@},
        @{Title='Add image normalization pipeline'; Milestone='M2 - PDF/Image Normalization'; Labels=@('area:image','type:feature'); Body=@"
## Goal

Normalize image input to a 4x6 203dpi canvas.

## Tasks

- [ ] Crop input
- [ ] Rotate input
- [ ] Resize to 812x1218
- [ ] Convert to grayscale
- [ ] Convert to black-and-white
- [ ] Save normalized PNG

## Acceptance Criteria

An image can be normalized to 812x1218.
"@},
        @{Title='Add image-to-ZPL encoder'; Milestone='M3 - ZPL Raster Output'; Labels=@('area:zpl','area:image','type:feature'); Body=@"
## Goal

Convert a normalized black-and-white image into printable ZPL graphics.

## Tasks

- [ ] Accept normalized 1-bit image
- [ ] Encode image data for ZPL
- [ ] Wrap output with ^XA and ^XZ
- [ ] Save generated ZPL
- [ ] Print generated ZPL

## Acceptance Criteria

A normalized image can be printed on the Zebra as a ZPL graphics payload.
"@},
        @{Title='Add watched folder workflow'; Milestone='M5 - Watched Folder Workflow'; Labels=@('type:feature','area:windows'); Body=@"
## Goal

Create the LabelDrop watched-folder workflow.

## Tasks

- [ ] Create input folder
- [ ] Create printed folder
- [ ] Create failed folder
- [ ] Detect new files
- [ ] Process supported files
- [ ] Move successful files to Printed
- [ ] Move failed files to Failed

## Acceptance Criteria

Dropping a supported file into the input folder triggers processing.
"@},
        @{Title='Add retailer profile system'; Milestone='M6 - Retailer Profiles'; Labels=@('area:profiles','type:feature'); Body=@"
## Goal

Create a YAML-based profile system for common retailer and carrier label layouts.

## Tasks

- [ ] Define profile schema
- [ ] Add generic 4x6 profile
- [ ] Add generic letter embedded profile
- [ ] Add placeholder UPS profile
- [ ] Add placeholder FedEx profile
- [ ] Add placeholder USPS profile
- [ ] Add placeholder Amazon return profile

## Acceptance Criteria

A user can select a profile and apply its crop/rotation/threshold settings.
"@}
    )

    foreach ($issue in $issues) {
        if ($existingTitles -contains $issue.Title) { continue }
        $bodyFile = New-TemporaryFile
        try {
            Set-Content -Path $bodyFile -Value $issue.Body -Encoding UTF8
            $labelCsv = $issue.Labels -join ','
            Invoke-External gh issue create --repo "$Owner/$RepoName" --title $issue.Title --body-file $bodyFile --milestone $issue.Milestone --label $labelCsv | Out-Null
        }
        finally {
            Remove-Item -LiteralPath $bodyFile -Force -ErrorAction SilentlyContinue
        }
    }
}

if (-not (Test-CommandExists git)) { throw "git is required." }
if (-not $SkipGitHub -and -not (Test-CommandExists gh)) { throw "gh is required unless -SkipGitHub is used." }
if (-not (Test-CommandExists py)) { throw "Python launcher 'py' is required." }

New-Item -ItemType Directory -Force -Path $BasePath | Out-Null

$Owner = if ($SkipGitHub) { 'kars85' } else { (Invoke-ExternalText gh api user --jq '.login' | Select-Object -First 1).Trim() }
if (-not $Owner) { $Owner = 'kars85' }
$script:RepoPath = Join-Path $BasePath $RepoName
$remoteUrl = "https://github.com/$Owner/$RepoName.git"

Ensure-GitHubRepo -Owner $Owner -RepoName $RepoName -Description $RepoDescription

if (-not (Test-Path -LiteralPath $script:RepoPath)) {
    Write-Step "Local folder missing; cloning $remoteUrl"
    Invoke-External git clone $remoteUrl $script:RepoPath
}
elseif (Test-GitRepo -Path $script:RepoPath) {
    Write-Step "Existing Git repository found at $script:RepoPath"
}
else {
    Write-Step "Existing folder is not a Git repository; initializing it"
    Invoke-External git -C $script:RepoPath init -b main
    Ensure-OriginRemote -RepoPath $script:RepoPath -RemoteUrl $remoteUrl
}

if (Test-GitRepo -Path $script:RepoPath) {
    Ensure-OriginRemote -RepoPath $script:RepoPath -RemoteUrl $remoteUrl
}

New-ScaffoldTree
Install-And-Test
Commit-And-Push
Ensure-GitHubLabels -Owner $Owner -RepoName $RepoName
Ensure-GitHubMilestones -Owner $Owner -RepoName $RepoName
Ensure-GitHubIssues -Owner $Owner -RepoName $RepoName

Write-Step "Bootstrap complete"
[pscustomobject]@{
    RepositoryPath = $script:RepoPath
    Owner = $Owner
    RemoteUrl = $remoteUrl
    PrinterIP = $PrinterIP
}

