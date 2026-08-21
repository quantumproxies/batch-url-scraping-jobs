"""mode="summary" — status, title, canonical and length for thousands of URLs.

No page bodies come back, which makes this the mode for link audits, redirect
checks and "is anything 404-ing after the migration" sweeps.

    python3 summary_mode.py urls.txt --out summary.csv
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import time
from collections import Counter

from qdapi import get, post


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=pathlib.Path)
    ap.add_argument("--out", default="summary.csv")
    args = ap.parse_args()

    urls = [ln.strip() for ln in args.file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    job = post("/batch", {"urls": urls, "mode": "summary", "concurrency": 15})

    while True:
        time.sleep(3)
        status = get(f"/batch/{job['id']}")
        if status.get("status") in ("completed", "failed", "cancelled"):
            break

    items = status.get("items") or []
    codes = Counter(item.get("status") for item in items)
    print("status codes:", dict(sorted(codes.items(), key=lambda kv: -kv[1])))

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["url", "status", "title", "description",
                                           "canonical", "contentLength", "bytes", "error"])
        w.writeheader()
        for item in items:
            w.writerow({k: item.get(k) for k in w.fieldnames})

    thin = [i for i in items if (i.get("contentLength") or 0) < 500 and i.get("status") == 200]
    print(f"\n{len(thin)} pages under 500 characters of content:")
    for item in thin[:15]:
        print(f"  {item.get('contentLength'):>6}  {item.get('url')}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
