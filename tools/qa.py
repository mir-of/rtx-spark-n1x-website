# -*- coding: utf-8 -*-
"""Viewport / asset QA for the generated site."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "qa"
OUT.mkdir(exist_ok=True)
TMP = ROOT / "tools" / "tmp"
TMP.mkdir(exist_ok=True)
os.environ["TEMP"] = str(TMP)
os.environ["TMP"] = str(TMP)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PAGES = ["index.html", "spec.html", "nvidia-app.html", "benchmark.html",
         "memory.html", "memory-story.html", "qwen.html", "h3.html", "wukong.html",
         "evidence.html", "verdict.html"]

def scroll_all(page):
    page.evaluate("""async () => {
      const step = Math.max(600, window.innerHeight * 0.9);
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 40));
      }
      window.scrollTo(0, document.body.scrollHeight);
      await new Promise(r => setTimeout(r, 250));
      window.scrollTo(0, 0);
      await new Promise(r => setTimeout(r, 150));
    }""")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=EDGE, args=["--no-sandbox"])
        for width, height, tag in [(1440, 900, "desktop"), (768, 1024, "tablet"), (390, 844, "mobile")]:
            ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
            page = ctx.new_page()
            bad = []
            page.on("response", lambda r: bad.append((r.status, r.url)) if r.status >= 400 else None)
            page.on("requestfailed", lambda r: bad.append(("FAIL", r.url)))
            for name in PAGES:
                page.goto(f"http://127.0.0.1:8765/{name}", wait_until="load")
                page.wait_for_timeout(250)
                # Lazy images can report naturalWidth 0 if we only scroll fast; force eager first.
                page.evaluate("document.querySelectorAll('img').forEach(i => i.loading = 'eager')")
                scroll_all(page)
                page.wait_for_timeout(500)
                metrics = page.evaluate("""() => {
                  const imgs = [...document.images];
                  return {
                    scrollWidth: document.documentElement.scrollWidth,
                    innerWidth: window.innerWidth,
                    broken: imgs.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'))
                  };
                }""")
                overflow = metrics["scrollWidth"] > metrics["innerWidth"] + 2
                if overflow or metrics["broken"]:
                    print(f"[{tag}] {name}: overflow={overflow} sw={metrics['scrollWidth']} iw={metrics['innerWidth']} broken={metrics['broken']}")
                else:
                    print(f"[{tag}] {name}: ok")
                if name in ("index.html", "memory.html", "qwen.html", "h3.html", "wukong.html", "spec.html", "memory-story.html", "verdict.html", "evidence.html"):
                    page.evaluate("window.scrollTo(0,0)")
                    page.wait_for_timeout(150)
                    page.screenshot(path=str(OUT / f"{tag}-{name.replace('.html','')}-top.png"), full_page=False)
            if bad:
                print(f"[{tag}] http errors:", bad[:20])
            ctx.close()
        browser.close()

if __name__ == "__main__":
    run()
