<#
.SYNOPSIS
  Publish this skill to its own GitHub repo without duplicating the source.

.DESCRIPTION
  The canonical copy lives inside the Expeditions Toolkit repo, is indexed by
  wiki.py, and is where the engine is maintained. Copying it to a second folder
  would create two copies that drift, which is the exact thing this skill's own
  documentation warns about.

  `git subtree` pushes a subdirectory to a separate repo as its own history,
  from the one source. Run this from the TOOLKIT root, not from here.

.EXAMPLE
  gh repo create expeditions-specialist --public --description "Build custom specialists for Expeditions: A MudRunner Game"
  git subtree push --prefix=skill/expeditions-specialist expeditions-specialist main
#>
param([string]$Remote = 'expeditions-specialist', [string]$Branch = 'main')
$prefix = 'skill/expeditions-specialist'
if (-not (Test-Path (Join-Path $PWD $prefix))) {
    throw "Run this from the Toolkit root. Expected $prefix below $PWD."
}
git remote get-url $Remote 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    "No remote named '$Remote'. Create the repo and add it first:"
    "  gh repo create expeditions-specialist --public"
    "  git remote add $Remote https://github.com/<you>/expeditions-specialist.git"
    exit 1
}
git subtree push --prefix=$prefix $Remote $Branch
