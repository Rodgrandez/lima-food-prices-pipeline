# Daily update on a machine in Lima (SISAP does not answer GitHub-hosted runners).
# Registered in Windows Task Scheduler; downloads the latest prices, rebuilds the site and pushes it to gh-pages.
# A failed run (for example, no internet at the scheduled time) is retried: -Attempts runs, -WaitMinutes apart.
param([string]$Stage = "daily", [int]$Attempts = 3, [int]$WaitMinutes = 30)
$repo = Split-Path -Parent $PSScriptRoot
$log = Join-Path $repo "data\update.log"
$conda = Join-Path $env:USERPROFILE "anaconda3\Scripts\conda.exe"
New-Item -ItemType Directory -Force (Join-Path $repo "data") | Out-Null
Set-Location $repo
if (-not (Test-Path $conda)) { "FAILED: conda not found at $conda" | Out-File -Append -Encoding utf8 $log; exit 2 }
$code = 1
for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
    "=== $(Get-Date -Format s) stage=$Stage attempt=$attempt/$Attempts" | Out-File -Append -Encoding utf8 $log
    # cmd.exe does the redirection so that warnings on stderr are logged instead of aborting PowerShell
    cmd /c "`"$conda`" run -n food-prices --no-capture-output python -m foodprices.pipeline $Stage >> `"$log`" 2>&1"
    $code = $LASTEXITCODE
    "=== exit code $code" | Out-File -Append -Encoding utf8 $log
    if ($code -eq 0) { break }
    if ($attempt -lt $Attempts) {
        "=== retrying in $WaitMinutes minutes" | Out-File -Append -Encoding utf8 $log
        Start-Sleep -Seconds (60 * $WaitMinutes)
    }
}
exit $code
