"""Live viewer — watch the full perception stream in real time.

Starts continuous screen translation (VISION), OCR, and voice (YOU), and prints
each new line as it lands. Use it to SEE the system working: move around your
screen, open an error, talk into your mic. Ctrl-C to stop.

    python run_live.py
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))
import perception

TAG = {"VISION": "\033[36m", "OCR": "\033[33m", "YOU": "\033[1;32m", "SYS": "\033[90m"}
RESET = "\033[0m"

def main():
    print("Starting perception (screen + OCR + voice). Ctrl-C to stop.\n")
    perception.start()
    seen = 0
    try:
        while True:
            lines = perception.recent(500).splitlines()
            for ln in lines[seen:]:
                src = next((k for k in TAG if f" {k} " in ln or ln.split("]")[-1].strip().startswith(k)), "")
                color = TAG.get(src, "")
                print(f"{color}{ln}{RESET}", flush=True)
            seen = len(lines)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nstopped.")

if __name__ == "__main__":
    main()
