"""Live viewer — watch the full perception stream in real time.

Starts continuous screen translation (VISION), exact text (OCR), and voice (YOU),
and prints each new line as it lands. Move around your screen, open an app or an
error, and talk into your mic. Ctrl-C to stop.

    python run_live.py
"""
import os, sys, time
from pathlib import Path

os.system("")  # enable ANSI colors on Windows consoles
sys.path.insert(0, str(Path(__file__).parent / "mcp_server"))
import perception  # noqa: E402

C = {"VISION": "\033[38;5;44m", "OCR": "\033[38;5;179m",
     "YOU": "\033[1;38;5;46m", "SYS": "\033[38;5;244m"}
RESET = "\033[0m"; BOLD = "\033[1m"

def main():
    print(f"{BOLD}╔══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║  DESKTOP LIVESTREAM — live perception stream                  ║{RESET}")
    print(f"{BOLD}╚══════════════════════════════════════════════════════════════╝{RESET}")
    print(f"  {C['VISION']}VISION{RESET}=screen described   {C['OCR']}OCR{RESET}=exact text   "
          f"{C['YOU']}YOU{RESET}=your voice   {C['SYS']}SYS{RESET}=status")
    print("  Move around, open an error, talk into your mic.  Ctrl-C to stop.\n")
    perception.start()
    seen = 0
    try:
        while True:
            lines = perception.recent(500).splitlines()
            for ln in lines[seen:]:
                src = ln[11:17].strip() if len(ln) > 17 else ""
                print(f"{C.get(src,'')}{ln}{RESET}", flush=True)
            seen = len(lines)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n{C['SYS']}stopped.{RESET}")

if __name__ == "__main__":
    main()
