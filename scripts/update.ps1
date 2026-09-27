# Daily update on a machine in Lima (SISAP does not answer GitHub-hosted runners).
# Registered in Windows Task Scheduler; downloads the latest prices, rebuilds the site and pushes it to gh-pages.
param([string]$Stage = "daily")
$repo = Split-Path -Parent $PSScriptRoot
$log = Join-Path $repo "data\update.log"
$conda = Join-Path $env:USERPROFILE "anaconda3\Scripts\conda.exe"
New-Item -ItemType Directory -Force (Join-Path $repo "data") | Out-Null
Set-Location $repo
"=== $(Get-Date -Format s) stage=$Stage" | Out-File -Append -Encoding utf8 $log
if (-not (Test-Path $conda)) { "FAILED: conda not found at $conda" | Out-File -Append -Encoding utf8 $log; exit 2 }
# cmd.exe does the redirection so that warnings on stderr are logged instead of aborting PowerShell
cmd /c "`"$conda`" run -n food-prices --no-capture-output python -m foodprices.pipeline $Stage >> `"$log`" 2>&1"
$code = $LASTEXITCODE
"=== exit code $code" | Out-File -Append -Encoding utf8 $log
exit $code
