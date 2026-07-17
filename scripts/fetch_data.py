"""Fetch open hyperspectral cubes used by the benchmark into ./data.

    python scripts/fetch_data.py

Indian Pines is a public AVIRIS scene (Purdue University). We mirror from a
stable public copy and validate it loads as a 3D cube. Add more scenes here
as the benchmark grows (Salinas, Pavia, target-detection sets).
"""

from __future__ import annotations

import os
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")

# name -> list of mirror URLs (tried in order)
SOURCES = {
    "indian_pines.mat": [
        "https://github.com/gokriznastic/HybridSN/raw/master/data/Indian_pines_corrected.mat",
    ],
}


def _download(url: str, dest: str) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r, open(dest, "wb") as f:
            f.write(r.read())
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  failed: {exc}")
        return False


def main() -> None:
    os.makedirs(DATA, exist_ok=True)
    for name, urls in SOURCES.items():
        dest = os.path.join(DATA, name)
        if os.path.exists(dest):
            print(f"{name}: already present, skipping")
            continue
        for url in urls:
            print(f"{name}: downloading from {url}")
            if _download(url, dest):
                try:
                    from hypermix.datasets import load_mat_cube
                    cube = load_mat_cube(dest)
                    print(f"  ok -> {cube.shape} {cube.dtype}")
                    break
                except Exception as exc:  # noqa: BLE001
                    print(f"  downloaded but not a valid cube: {exc}")
                    os.remove(dest)
        else:
            print(f"{name}: all mirrors failed. See "
                  "https://www.ehu.eus/ccwintco/index.php/Hyperspectral_Remote_Sensing_Scenes")


if __name__ == "__main__":
    main()
