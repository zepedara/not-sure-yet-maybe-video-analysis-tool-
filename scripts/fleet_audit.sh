#!/usr/bin/env bash
# fleet_audit.sh — portable hardware audit for the desktop-livestream fleet.
# Run on each node (l3, echo7, ricksanchez, laptop). Linux + macOS.
# Usage:  bash fleet_audit.sh            # prints report
#         bash fleet_audit.sh > l3.txt   # save to feed back to Claude
set -u

line() { printf '%s\n' "----------------------------------------"; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "======================================================"
echo " FLEET NODE AUDIT   host=$(hostname 2>/dev/null)   date=$(date 2>/dev/null)"
echo "======================================================"

line; echo "OS / KERNEL"
uname -a 2>/dev/null
if [ -f /etc/os-release ]; then . /etc/os-release; echo "$PRETTY_NAME"; fi
have sw_vers && sw_vers   # macOS

line; echo "CPU"
if have lscpu; then
  lscpu | grep -E "Model name|^CPU\(s\)|Thread|Core|Socket|MHz"
elif have sysctl; then
  sysctl -n machdep.cpu.brand_string 2>/dev/null
fi
echo "logical CPUs: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null)"

line; echo "MEMORY"
if have free; then free -h
elif have sysctl; then echo "$(( $(sysctl -n hw.memsize 2>/dev/null)/1024/1024/1024 )) GB total"; fi

line; echo "GPU / ACCELERATOR"
if have nvidia-smi; then
  echo "[NVIDIA]"
  nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader
elif have rocm-smi; then
  echo "[AMD ROCm]"; rocm-smi --showproductname --showmeminfo vram 2>/dev/null
elif sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -qi "Apple"; then
  echo "[Apple Silicon] unified memory GPU"
  system_profiler SPDisplaysDataType 2>/dev/null | grep -E "Chipset|Total Number of Cores|Metal"
else
  have lspci && lspci | grep -iE "vga|3d|display" || echo "no discrete GPU detected"
fi

line; echo "LOCAL-AI TOOLING PRESENT"
for t in ollama python3 pip tesseract ffmpeg docker; do
  if have "$t"; then printf "  %-10s %s\n" "$t" "$("$t" --version 2>&1 | head -1)"; else printf "  %-10s MISSING\n" "$t"; fi
done
if have ollama; then echo "  ollama models:"; ollama list 2>/dev/null | sed 's/^/    /'; fi

line; echo "DISK (root / cwd)"
df -h / . 2>/dev/null | sort -u

line; echo "NETWORK (for fleet reachability)"
have ip && ip -brief addr 2>/dev/null | grep -v "DOWN"
have ifconfig && ifconfig 2>/dev/null | grep -E "inet " | grep -v 127.0.0.1

echo "======================================================"
echo " END AUDIT — $(hostname 2>/dev/null)"
echo "======================================================"
