<#
.SYNOPSIS
  Install the expeditions-specialist skill for Claude Code, Codex, or both.

.DESCRIPTION
  Copies this folder to the agent's skills directory and checks that the Python
  dependencies are present. Nothing is written outside the skills directory.

.EXAMPLE
  .\install.ps1                 # Claude Code
  .\install.ps1 -Agent codex    # Codex
  .\install.ps1 -Agent both
#>
[CmdletBinding()]
param(
    [ValidateSet('claude', 'codex', 'both')]
    [string]$Agent = 'claude',
    [string]$Destination
)

$ErrorActionPreference = 'Stop'
$src = $PSScriptRoot
$name = Split-Path $src -Leaf

function Install-To($root) {
    $dest = Join-Path $root $name
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item -Path (Join-Path $src '*') -Destination $dest -Recurse -Force `
              -Exclude 'install.ps1', 'install.sh'
    "  installed -> $dest"
}

if ($Destination) {
    Install-To $Destination
} else {
    if ($Agent -in 'claude', 'both') { Install-To (Join-Path $HOME '.claude\skills') }
    if ($Agent -in 'codex', 'both')  { Install-To (Join-Path $HOME '.codex\skills') }
}

# Dependencies. rembg is optional and large, so it is reported, not demanded.
$required = @{ 'PIL' = 'pillow'; 'numpy' = 'numpy'; 'cv2' = 'opencv-python' }
$missing = @()
foreach ($mod in $required.Keys) {
    & python -c "import $mod" 2>$null
    if ($LASTEXITCODE -ne 0) { $missing += $required[$mod] }
}
& python -c "import rembg" 2>$null
$rembg = ($LASTEXITCODE -eq 0)

""
if ($missing.Count) {
    "  missing packages: $($missing -join ', ')"
    "  install with:     python -m pip install $($missing -join ' ')"
} else {
    "  python dependencies present"
}
if (-not $rembg) {
    "  rembg not installed. Only needed to cut an opaque portrait;"
    "  a portrait that already has alpha works without it."
}

""
"  Optional environment overrides, only if your paths are unusual:"
"    EXPEDITIONS_GAME    the game install"
"    EXPEDITIONS_MODS    Documents\My Games\Expeditions\Media\Mods"
"    EXPEDITIONS_SCHEMA  Sources\BinEditor\meta_desc_ssl.ps (editor only)"
""
"  Verify with:  python scripts\specialist_doctor.py"
