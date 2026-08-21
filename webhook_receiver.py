"""Receive a finished batch job instead of polling for it.

Pass `"webhook": "https://your.host/qd-batch"` when you start the job and the
finished job is POSTed here once. Verify the job id against something you
started — a public endpoint will eventually be probed by someone else.

    pip install flask && python3 webhook_receiver.py
"""
from __future__ import annotations

import json
import pathlib

from flask import Flask, jsonify, request

app = Flask(__name__)
STARTED: set[str] = set()          # job ids this process started — populate when you POST /batch
OUT = pathlib.Path("received")


@app.post("/qd-batch")
def receive():
    job = request.get_json(silent=True) or {}
    payload = job.get("payload", job)
    job_id = payload.get("id")

    if not job_id:
        return jsonify(error="no job id"), 400
    if STARTED and job_id not in STARTED:
        return jsonify(error="unknown job"), 403

    OUT.mkdir(exist_ok=True)
    (OUT / f"{job_id}.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"{job_id}: {payload.get('status')} — "
          f"{payload.get('completed')}/{payload.get('total')} items")
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(port=8080)
