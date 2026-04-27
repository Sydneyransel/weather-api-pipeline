# GitHub Actions Weather Pipeline — Design Spec

**Date:** 2026-04-27
**Project:** weather-api-pipeline

---

## Goal

Run `weather.py` on a daily schedule using GitHub Actions. Each run appends fresh forecast data to `weather_data.csv`, deduplicating so each city+date pair always reflects the most recent fetch.

---

## Architecture

Two existing files are modified; one new file is created:

```
weather.py                          ← read API key from os.environ, add append/dedup logic
weather_data.csv                    ← grows over time; one row per (zip_code, date)
.github/workflows/weather.yml       ← new: defines the scheduled workflow
```

The workflow steps on each run:
1. Check out the repo
2. Set up Python 3.x and install `requirements.txt`
3. Run `weather.py` (API key injected from GitHub Secret `WEATHERAPI_KEY`)
4. Commit and push the updated `weather_data.csv` back to `main`

---

## Schedule

`0 9 * * *` — 9 AM UTC daily.

---

## Data Flow

Each run fetches a 3-day forecast for 20 cities and merges it into the existing CSV:

1. Fetch new rows from the API, stamping each with `fetched_on` (today's date in `YYYY-MM-DD` format)
2. Load `weather_data.csv` if it exists
3. Concatenate old + new rows
4. Deduplicate on `(zip_code, date)`, keeping the last (most recent) occurrence
5. Save back to `weather_data.csv`

**Growth pattern:**
- First run: 60 rows (20 cities × 3 forecast days)
- Each subsequent day: ~20 new rows added (one new future date enters the window as the oldest exits)
- Existing rows for dates still in the forecast window are refreshed with the latest values

Once a date scrolls out of the 3-day window it stays in the CSV frozen at its last known forecast.

**Columns:** `zip_code`, `city`, `region`, `date`, `max_temp_f`, `min_temp_f`, `condition`, `fetched_on`

---

## API Key

The hardcoded key in `weather.py` line 6 is removed. The script reads it via:

```python
API_KEY = os.environ["WEATHERAPI_KEY"]
```

The key is stored as a GitHub Secret (`WEATHERAPI_KEY`) on the repo and injected into the workflow environment at runtime. This is required because the repo is public.

---

## Error Handling

- **Per-city API errors:** If a request fails for a zip code, print a warning and skip that city. The run continues; existing CSV data for that city is unchanged.
- **Workflow-level failures:** GitHub Actions sends an email notification automatically on failure. No retries — a missed daily run is acceptable for this project.

---

## Testing

The workflow includes a `workflow_dispatch` trigger so it can be run manually from the GitHub Actions tab at any time, without waiting for the scheduled time.

---

## Files Changed

| File | Change |
|---|---|
| `weather.py` | Remove hardcoded key; read from `os.environ`; switch to append+dedup mode; add `fetched_on` column |
| `.github/workflows/weather.yml` | New file — defines schedule, Python setup, script run, auto-commit |
| `weather_data.csv` | Updated by the workflow on each run |
