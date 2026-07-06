[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $HostName,

    [int] $Port = 9100,

    [switch] $SaveOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$ArgsList = @(".\src\zebra_label_gateway\print_tcp.py", "--host", $HostName, "--port", $Port)
if ($SaveOnly) {
    $ArgsList += "--save-only"
}

& .\.venv\Scripts\python.exe @ArgsList
