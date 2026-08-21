# Batch URL scraping jobs — 1,000 URLs, one job id, incremental polling

`POST /v1/batch` takes a list of URLs you already have and scrapes them asynchronously through
the [QuanticData Web Scraping API](https://quanticdata.io/web-scraping-api/). You get a job id
straight away and poll `GET /v1/batch/{jobId}` for progress — or hand it a `webhook` and get the
finished job pushed to you.

$0.0002 per URL. Failures are not billed, and the unfetched share of an aborted job is refunded.

```bash
pip install requests
export QUANTICDATA_API_KEY=qd_live_your_key_here
python3 run_batch.py urls.txt --format markdown --out pages.jsonl
```

## Files

| File | What it does |
|---|---|
| [`run_batch.py`](run_batch.py) | read a URL file, chunk it, run the jobs, stream results to JSONL |
| [`incremental_poll.py`](incremental_poll.py) | poll with the `since` cursor — only new items each time, no re-downloading |
| [`summary_mode.py`](summary_mode.py) | `mode: "summary"` — status/title/canonical/length for thousands of URLs without paying for content transfer |
| [`webhook_receiver.py`](webhook_receiver.py) | a 40-line Flask endpoint that receives the finished job |
| [`extract_schema.py`](extract_schema.py) | one CSS `extract` schema applied to every URL → tabular output |

## Request

```jsonc
{
  "urls": ["https://…", "https://…"],       // required, up to 5000 per job
  "format": "markdown",                      // markdown | html | text
  "engine": "auto",                          // auto | tls | fetch | render
  "render": false,                           // force the browser for every URL
  "extract": { "price": ".price", "title": "h1" },
  "contentMode": "article",                  // smart | article | full
  "mode": "summary",                         // metadata only — the cheap audit mode
  "concurrency": 10,                         // 1–20, default 5
  "webhook": "https://your.app/hook",
  "country": "us"
}
```

## Job status

```jsonc
{
  "id": "…", "status": "running",            // running | completed | failed | cancelled
  "total": 500, "completed": 143, "failed": 2,
  "items": [
    { "url": "…", "status": 200, "title": "…", "content": "# …", "engine": "tls" },
    { "url": "…", "status": 403, "title": null, "error": "blocked after retries" }
  ]
}
```

In `mode: "summary"` each item carries `description`, `canonical`, `contentLength` and `bytes`
instead of `content`. Long jobs stop retaining page bodies once the retention budget is hit and
set `contentTruncated: true` — poll incrementally (see `incremental_poll.py`) if you are
scraping tens of thousands of pages.

## Sizing a job

| URLs | Concurrency | Notes |
|---|---|---|
| < 100 | 5 (default) | finishes in a minute or two |
| 100–1,000 | 10 | the sweet spot for most sites |
| 1,000–5,000 | 15–20 | poll incrementally; consider `mode: "summary"` |
| > 5,000 | chunk into several jobs | `run_batch.py --chunk 2000` does it for you |

Don't have the URL list? [Map the site first](https://quanticdata.io/crawl-map/) — one call,
$0.0005, every URL its sitemaps know about.

## Related

- [What is a web scraper API?](https://quanticdata.io/blog/what-is-a-web-scraper-api/)
- [Web scraping with Python](https://quanticdata.io/blog/how-to-web-scraping-using-python/)
- [How data pipelines work](https://quanticdata.io/blog/how-do-data-pipelines-work/)
- [Web Data API for AI](https://quanticdata.io/web-data-api-for-ai/) — same fetches, RAG-shaped output

MIT licensed.
