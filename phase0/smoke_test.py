"""Non-interactive Phase 0 smoke test: capture -> change-detect -> local narrate."""
import io, time
from datetime import datetime, timezone
import mss, imagehash
from PIL import Image
import config
from narrator import narrate, OLLAMA_URL, MODEL

print(f"target: {OLLAMA_URL}  model: {MODEL}")
def png(img, w):
    if img.width > w: img = img.resize((w, int(img.height*w/img.width)))
    b = io.BytesIO(); img.save(b, format="PNG"); return b.getvalue()

with mss.mss() as sct:
    mon = sct.monitors[config.MONITOR_INDEX]
    print(f"monitor: {mon['width']}x{mon['height']}")
    shot = sct.grab(mon)
    img = Image.frombytes("RGB", shot.size, shot.rgb)
    h = imagehash.phash(img)
    print(f"captured full screen, phash={h}")
    data = png(img, config.DOWNSCALE_WIDTH)
    print(f"downscaled PNG: {len(data)//1024} KB")
    t0 = time.time()
    text = narrate(data)
    dt = time.time()-t0
    print(f"\n=== VISION (narrated by rick in {dt:.1f}s) ===\n{text}")
