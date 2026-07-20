# Launch the live perception viewer. Run:  powershell -ExecutionPolicy Bypass -File launch.ps1
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
$Host.UI.RawUI.WindowTitle = "Desktop Livestream — live view"
Write-Host "Starting live perception viewer (screen + OCR + voice)..." -ForegroundColor Cyan
python "$here\run_live.py"
Write-Host "`nStopped. Press any key to close." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
