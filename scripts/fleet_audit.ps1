# fleet_audit.ps1 — Windows counterpart to fleet_audit.sh
# Run on Windows fleet nodes (laptop, l3e7).  Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File fleet_audit.ps1 > node.txt
$ErrorActionPreference = 'SilentlyContinue'
$os  = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor
"====================================================="
" FLEET NODE AUDIT  host=$env:COMPUTERNAME"
"====================================================="
"--- OS ---";   $os.Caption + " build " + $os.BuildNumber
"--- CPU ---";  $cpu.Name.Trim()
"cores=$($cpu.NumberOfCores) logical=$($cpu.NumberOfLogicalProcessors)"
"--- MEMORY ---"; "{0} GB total" -f [math]::Round($os.TotalVisibleMemorySize/1MB,1)
"--- GPU ---"
Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name + " (driver " + $_.DriverVersion + ")" }
if (Get-Command nvidia-smi -EA SilentlyContinue) {
  nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader
}
"--- LOCAL-AI TOOLING ---"
foreach ($t in 'ollama','python','pip','tesseract','ffmpeg','docker') {
  $c = Get-Command $t -EA SilentlyContinue
  if ($c) { "{0,-10} {1}" -f $t, ((& $t --version 2>&1 | Select-Object -First 1)) }
  else    { "{0,-10} MISSING" -f $t }
}
if (Get-Command ollama -EA SilentlyContinue) { "ollama models:"; ollama list }
"--- DISK ---"
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
  "{0} {1} GB free / {2} GB" -f $_.DeviceID, [math]::Round($_.FreeSpace/1GB), [math]::Round($_.Size/1GB) }
"--- NETWORK ---"
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' } |
  ForEach-Object { "{0}  {1}" -f $_.InterfaceAlias, $_.IPAddress }
"===================================================== END"
