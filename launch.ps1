# Launch the live perception viewer.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
$Host.UI.RawUI.WindowTitle = "Desktop Livestream - live view"
Write-Host "Starting live perception viewer (screen + OCR + voice)..." -ForegroundColor Cyan
& "C:/Users/m808b/AppData/Local/Programs/Python/Python312/python.exe" "$here\run_live.py" 2>&1 | Tee-Object -FilePath "$here\launch_error.log"
Write-Host ""
Write-Host "Stopped (see launch_error.log if it exited fast). Press any key to close." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
