# Daily update on a machine in Lima (SISAP does not answer requests from abroad).
# Registered in Windows Task Scheduler; downloads the latest prices, rebuilds the site and pushes it to gh-pages.
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$log = Join-Path $repo "data\update.log"
New-Item -ItemType Directory -Force (Join-Path $repo "data") | Out-Null
Set-Location $repo
"=== $(Get-Date -Format s)" | Out-File -Append -Encoding utf8 $log
& "$env:USERPROFILE\anaconda3\Scripts\conda.exe" run -n food-prices python -m foodprices.pipeline daily *>> $log
if ($LASTEXITCODE -ne 0) { "FAILED with exit code $LASTEXITCODE" | Out-File -Append -Encoding utf8 $log; exit $LASTEXITCODE }
