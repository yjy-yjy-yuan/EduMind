$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Host "python not found; please install Python 3.10+ and add it to PATH."
  exit 1
}

python .\dev_start.py --open

