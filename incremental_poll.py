"""Poll a big job with the `since` cursor — each poll returns only what is new.

Re-downloading 5,000 items on every poll is how a batch job becomes slower than
scraping serially. `since` (the previous response's `nextCursor`) fixes that;
`include_content=false` keeps the status calls tiny while a job is still running.

    python3 incremental_poll.py <jobId> --out items.jsonl
"""
from __future__ import annotations

import argparse
import json
import time

from qdapi import get


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--out", default="items.jsonl")
    args = ap.parse_args()

    cursor = None
    seen = 0
    delay = 2.0

    with open(args.out, "w", encoding="utf-8") as fh:
        while True:
            params = {"include_content": "true"}
            if cursor is not None:
                params["since"] = cursor

            status = get(f"/batch/{args.job_id}", **params)
            items = status.get("items") or []
            for item in items:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
            seen += len(items)
            cursor = status.get("nextCursor", cursor)

            print(f"{status.get('status')}: +{len(items)} new, {seen} saved, "
                  f"{status.get('completed')}/{status.get('total')} done")

            if status.get("contentTruncated"):
                print("  note: the job stopped retaining page bodies (retention budget hit)")
            if status.get("status") in ("completed", "failed", "cancelled") and not items:
                break

            time.sleep(delay)
            delay = min(delay * 1.3, 15.0)

    print(f"\n{seen} items → {args.out}")


if __name__ == "__main__":
    main()
