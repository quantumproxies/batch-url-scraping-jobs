"""One CSS extraction schema, applied to every URL in the job.

`extract` turns each page into a row instead of a document — the shortest path
from a list of product URLs to a CSV your analysts can open.

    python3 extract_schema.py products.txt --out products.csv
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import time

from qdapi import get, post

# field -> CSS selector (or { selector, attr, all } for attributes / lists)
SCHEMA = {
    "title": "h1",
    "price": '[itemprop="price"], .price, [data-price]',
    "availability": '[itemprop="availability"], .stock, .availability',
    "sku": '[itemprop="sku"], [data-sku]',
    "image": {"selector": 'img[itemprop="image"], .product img', "attr": "src"},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=pathlib.Path)
    ap.add_argument("--render", action="store_true", help="for shops that price client-side")
    ap.add_argument("--country", default=None, help="ISO code — localized prices")
    ap.add_argument("--out", default="products.csv")
    args = ap.parse_args()

    urls = [ln.strip() for ln in args.file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    body = {"urls": urls, "extract": SCHEMA, "concurrency": 8, "render": args.render}
    if args.country:
        body["country"] = args.country

    job = post("/batch", body)
    print(f"job {job.get('id')}: {len(urls)} URLs")

    while True:
        time.sleep(3)
        status = get(f"/batch/{job['id']}")
        if status.get("status") in ("completed", "failed", "cancelled"):
            break

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["url", *SCHEMA, "error"])
        w.writeheader()
        for item in status.get("items") or []:
            row = {"url": item.get("url"), "error": item.get("error", "")}
            row.update({k: (item.get("data") or {}).get(k) for k in SCHEMA})
            w.writerow(row)

    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
