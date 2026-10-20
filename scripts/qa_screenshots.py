"""Visual QA: full-page screenshots of the running app at laptop and tablet widths.

Drives a headless Microsoft Edge / Chrome over the DevTools protocol and waits
until Streamlit has finished rendering (no running indicator, no skeletons)
before capturing. Dev tool only; needs the app running with TUTOR_DEV=1 for the
``?unlock=1&sel=…`` hooks.

    python scripts/qa_screenshots.py OUT_DIR name=path[@width] ...
    python scripts/qa_screenshots.py shots pgA=playground?scene=divider@768
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
BASE = os.environ.get("TUTOR_URL", "http://localhost:8517/")
READY_JS = """
(() => {
  const running = document.querySelector('[data-testid="stStatusWidget"]');
  const skel = document.querySelector('[data-testid="stSkeleton"]');
  const app = document.querySelector('[data-testid="stMain"]');
  const plots = Array.from(document.querySelectorAll('.stPlotlyChart'));
  const plotsOk = plots.every(p => p.querySelector('.main-svg'));
  return !!app && !running && !skel && plotsOk && document.readyState === 'complete';
})()
"""


class Tab:
    def __init__(self, ws_url: str):
        self.ws = connect(ws_url, max_size=None)
        self.i = 0

    def call(self, method: str, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.i:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})


def shoot(tab: Tab, url: str, width: int, out: Path) -> None:
    tab.call("Emulation.setDeviceMetricsOverride", width=width, height=1000, deviceScaleFactor=1, mobile=False)
    tab.call("Page.navigate", url=url)
    time.sleep(2.0)
    stable, deadline = 0, time.time() + 45
    while time.time() < deadline:
        ok = tab.call("Runtime.evaluate", expression=READY_JS, returnByValue=True)["result"].get("value")
        stable = stable + 1 if ok else 0
        if stable >= 4:  # ready for ~2 s in a row
            break
        time.sleep(0.5)
    h = tab.call("Runtime.evaluate", expression="document.querySelector('[data-testid=\"stMain\"]').scrollHeight + 80",
                 returnByValue=True)["result"]["value"]
    tab.call("Emulation.setDeviceMetricsOverride", width=width, height=int(h), deviceScaleFactor=1, mobile=False)
    time.sleep(1.2)
    sw = tab.call("Runtime.evaluate", expression="document.documentElement.scrollWidth", returnByValue=True)["result"]["value"]
    if os.environ.get("QA_DEBUG"):
        dbg = tab.call("Runtime.evaluate", returnByValue=True, expression=(
            "JSON.stringify({app: getComputedStyle(document.querySelector('.stApp')).backgroundColor,"
            " dark: matchMedia('(prefers-color-scheme: dark)').matches, ls: localStorage.getItem('stActiveTheme-/playground-v2')})"))
        print("   debug:", dbg["result"]["value"])
    data = tab.call("Page.captureScreenshot", format="png", captureBeyondViewport=True)["data"]
    out.write_bytes(base64.b64decode(data))
    flag = "  !! horizontal overflow" if sw > width + 1 else ""
    print(f"{out.name}: {width}x{h}  scrollWidth={sw}{flag}")


def main() -> int:
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    # one fresh browser per shot: reused headless tabs carry Streamlit state between loads
    for spec in sys.argv[2:]:
        _run_one(out_dir, spec)
    return 0


def _run_one(out_dir: Path, spec: str) -> None:
    browser = next(b for b in BROWSERS if Path(b).exists())
    prof = tempfile.mkdtemp(prefix="qa_")
    port = 9333
    proc = subprocess.Popen([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                             f"--remote-debugging-port={port}", f"--user-data-dir={prof}", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                page = next(t for t in targets if t["type"] == "page")
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.2)
        tab = Tab(page["webSocketDebuggerUrl"])
        tab.call("Page.enable")
        tab.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"},
                                                         {"name": "prefers-reduced-motion", "value": "reduce"}])
        name, _, rest = spec.partition("=")
        path, _, w = rest.partition("@")
        shoot(tab, BASE + path, int(w or 1366), out_dir / f"{name}.png")
    finally:
        proc.terminate()
        time.sleep(0.8)
        shutil.rmtree(prof, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
