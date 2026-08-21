"""Scrape a file of URLs in chunked batch jobs, streaming results to JSONL.

    python3 run_batch.py urls.txt --chunk 1000 --concurrency 10 --out pages.jsonl

One URL per line; blank lines and lines starting with # are ignored.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

from qdapi import get, post


def read_urls(path: pathlib.Path) -> list[str]:
    lines = (ln.strip() for ln in path.read_text(encoding="utf-8").splitlines())
    return [ln for ln in lines if ln and not ln.startswith("#")]


def wait_for(job_id: str) -> dict:
    delay = 2.0
    while True:
        time.sleep(delay)
        delay = min(delay * 1.4, 20.0)
        status = get(f"/batch/{job_id}")
        print(f"    {status.get('status')}: {status.get('completed')}/{status.get('total')}"
              f"  ({status.get('failed')} failed)")
        if status.get("status") in ("completed", "failed", "cancelled"):
            return status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=pathlib.Path)
    ap.add_argument("--chunk", type=int, default=1000, help="URLs per job (cap 5000)")
    ap.add_argument("--concurrency", type=int, default=10, help="1-20")
    ap.add_argument("--format", default="markdown", choices=["markdown", "html", "text"])
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--country", default=None)
    ap.add_argument("--out", default="pages.jsonl")
    args = ap.parse_args()

    urls = read_urls(args.file)
    chunks = [urls[i:i + args.chunk] for i in range(0, len(urls), args.chunk)]
    print(f"{len(urls)} URLs in {len(chunks)} job(s) — estimated ${len(urls) * 0.0002:.4f}")

    written = failed = 0
    with open(args.out, "w", encoding="utf-8") as fh:
        for n, chunk in enumerate(chunks, 1):
            body = {
                "urls": chunk,
                "format": args.format,
                "contentMode": "article",
                "concurrency": args.concurrency,
                "render": args.render,
            }
            if args.country:
                body["country"] = args.country

            job = post("/batch", body)
            print(f"  job {n}/{len(chunks)}: {job.get('id')}")
            status = wait_for(job["id"])

            for item in status.get("items") or []:
                if item.get("error"):
                    failed += 1
                    continue
                fh.write(json.dumps({
                    "url": item.get("url"),
                    "status": item.get("status"),
                    "title": item.get("title"),
                    "engine": item.get("engine"),
                    "content": item.get("content"),
                }, ensure_ascii=False) + "\n")
                written += 1

    print(f"\n{written} pages → {args.out}, {failed} failed (not billed)")


if __name__ == "__main__":
    main()
