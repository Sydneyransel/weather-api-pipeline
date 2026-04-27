# GitHub Actions Weather Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Schedule `weather.py` to run daily via GitHub Actions, appending deduplicated forecast data to `weather_data.csv` on each run.

**Architecture:** `weather.py` is restructured to extract a `merge_and_dedup` function (testable in isolation) and wrap all I/O in `if __name__ == "__main__"`. A new `.github/workflows/weather.yml` triggers the script on a cron schedule and auto-commits the updated CSV back to `main`.

**Tech Stack:** Python 3.11, pandas, requests, pytest, GitHub Actions

---

### Task 1: Restructure `weather.py` and write failing tests for `merge_and_dedup`

The script currently runs all code at module level, which means `import weather` in tests would trigger API calls. This task extracts the dedup logic into a standalone function and wraps everything else in `if __name__ == "__main__":`.

**Files:**
- Modify: `weather.py`
- Create: `tests/test_weather.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_weather.py` with this exact content:

```python
import pandas as pd
import pytest
from weather import merge_and_dedup


def _row(zip_code, date, max_temp, fetched_on):
    return {
        "zip_code": zip_code,
        "city": "Test City",
        "region": "Test Region",
        "date": date,
        "max_temp_f": max_temp,
        "min_temp_f": 50.0,
        "condition": "Sunny",
        "fetched_on": fetched_on,
    }


def test_dedup_keeps_newest_row_for_same_city_date():
    existing = pd.DataFrame([_row("90045", "2026-04-27", 65.3, "2026-04-26")])
    new = pd.DataFrame([_row("90045", "2026-04-27", 66.0, "2026-04-27")])
    result = merge_and_dedup(existing, new)
    assert len(result) == 1
    assert result.iloc[0]["max_temp_f"] == 66.0
    assert result.iloc[0]["fetched_on"] == "2026-04-27"


def test_dedup_adds_new_date_for_same_city():
    existing = pd.DataFrame([_row("90045", "2026-04-27", 65.3, "2026-04-26")])
    new = pd.DataFrame([_row("90045", "2026-04-28", 64.9, "2026-04-27")])
    result = merge_and_dedup(existing, new)
    assert len(result) == 2


def test_dedup_preserves_expired_dates_not_in_new_fetch():
    existing = pd.DataFrame([_row("90045", "2026-04-24", 64.0, "2026-04-24")])
    new = pd.DataFrame([_row("90045", "2026-04-27", 65.3, "2026-04-27")])
    result = merge_and_dedup(existing, new)
    assert len(result) == 2
    assert set(result["date"]) == {"2026-04-24", "2026-04-27"}


def test_dedup_handles_multiple_cities():
    existing = pd.DataFrame([
        _row("90045", "2026-04-27", 65.3, "2026-04-26"),
        _row("10001", "2026-04-27", 71.1, "2026-04-26"),
    ])
    new = pd.DataFrame([
        _row("90045", "2026-04-27", 66.0, "2026-04-27"),
        _row("10001", "2026-04-27", 72.0, "2026-04-27"),
    ])
    result = merge_and_dedup(existing, new)
    assert len(result) == 2
    la = result[result["zip_code"] == "90045"].iloc[0]
    ny = result[result["zip_code"] == "10001"].iloc[0]
    assert la["max_temp_f"] == 66.0
    assert ny["max_temp_f"] == 72.0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_weather.py -v
```

Expected: `ImportError` or `cannot import name 'merge_and_dedup'` — the function doesn't exist yet.

- [ ] **Step 3: Restructure `weather.py`**

Replace the entire contents of `weather.py` with:

```python
import os
import requests
import time
from datetime import date
import pandas as pd

CSV_PATH = "weather_data.csv"

zip_codes = [
    "90045",  # Los Angeles, CA
    "10001",  # New York, NY
    "60601",  # Chicago, IL
    "98101",  # Seattle, WA
    "33101",  # Miami, FL
    "77001",  # Houston, TX
    "85001",  # Phoenix, AZ
    "19101",  # Philadelphia, PA
    "78201",  # San Antonio, TX
    "75201",  # Dallas, TX
    "95101",  # San Jose, CA
    "78701",  # Austin, TX
    "32099",  # Jacksonville, FL
    "28201",  # Charlotte, NC
    "43085",  # Columbus, OH
    "76101",  # Fort Worth, TX
    "46201",  # Indianapolis, IN
    "94102",  # San Francisco, CA
    "28601",  # Hickory, NC
    "37201",  # Nashville, TN
]


def merge_and_dedup(existing_df, new_df):
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["zip_code", "date"], keep="last")
    return combined.reset_index(drop=True)


if __name__ == "__main__":
    API_KEY = os.environ["WEATHERAPI_KEY"]
    api_url = "https://api.weatherapi.com/v1/forecast.json"
    fetched_on = date.today().strftime("%Y-%m-%d")
    results = []

    for zip_code in zip_codes:
        params = {"key": API_KEY, "q": zip_code, "days": 7}
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"WARNING: skipping {zip_code} — {e}")
            continue

        city = data["location"]["name"]
        region = data["location"]["region"]
        print(f"\n{city}, {region} ({zip_code})")

        for day in data["forecast"]["forecastday"]:
            result = {
                "zip_code": zip_code,
                "city": city,
                "region": region,
                "date": day["date"],
                "max_temp_f": day["day"]["maxtemp_f"],
                "min_temp_f": day["day"]["mintemp_f"],
                "condition": day["day"]["condition"]["text"],
                "fetched_on": fetched_on,
            }
            results.append(result)
            print(f"  {result['date']}: High {result['max_temp_f']}°F, Low {result['min_temp_f']}°F, {result['condition']}")

        time.sleep(1)

    new_df = pd.DataFrame(results)

    if os.path.exists(CSV_PATH):
        existing_df = pd.read_csv(CSV_PATH)
        df = merge_and_dedup(existing_df, new_df)
    else:
        df = new_df

    print(df.to_string())
    print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")
    df.to_csv(CSV_PATH, index=False)
    print(f"Saved to {CSV_PATH}")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_weather.py -v
```

Expected output:
```
tests/test_weather.py::test_dedup_keeps_newest_row_for_same_city_date PASSED
tests/test_weather.py::test_dedup_adds_new_date_for_same_city PASSED
tests/test_weather.py::test_dedup_preserves_expired_dates_not_in_new_fetch PASSED
tests/test_weather.py::test_dedup_handles_multiple_cities PASSED
4 passed
```

- [ ] **Step 5: Verify the script still runs locally**

```bash
WEATHERAPI_KEY=e32648ad4a3f40f9bbe175111261304 python weather.py
```

Expected: same output as before, ending with `Saved to weather_data.csv`. The existing `weather_data.csv` will be merged and deduped; it will now have a `fetched_on` column.

- [ ] **Step 6: Commit**

```bash
git add weather.py tests/test_weather.py weather_data.csv
git commit -m "refactor: extract merge_and_dedup, add fetched_on column, add tests"
```

---

### Task 2: Create the GitHub Actions workflow

**Files:**
- Create: `.github/workflows/weather.yml`

- [ ] **Step 1: Create the workflow directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create `.github/workflows/weather.yml`**

> Note: The workflow installs `requests pandas` directly rather than using `requirements.txt`. The existing `requirements.txt` was generated on Windows (`pip freeze`) and contains Windows-only packages (e.g. `pywin32-ctypes`) that fail on the Ubuntu runner.


```yaml
name: Weather Pipeline

on:
  schedule:
    - cron: "0 9 * * *"
  workflow_dispatch:

jobs:
  fetch-weather:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repo
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests pandas

      - name: Run weather pipeline
        env:
          WEATHERAPI_KEY: ${{ secrets.WEATHERAPI_KEY }}
        run: python weather.py

      - name: Commit updated CSV
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add weather_data.csv
          git diff --staged --quiet || git commit -m "chore: update weather_data.csv [$(date -u +%Y-%m-%d)]"
          git push
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/weather.yml
git commit -m "feat: add daily GitHub Actions workflow for weather pipeline"
```

---

### Task 3: Add GitHub Secret and push

**Files:** none — this is configuration in the GitHub UI.

- [ ] **Step 1: Add `WEATHERAPI_KEY` as a GitHub Secret**

1. Go to your repo on GitHub: `https://github.com/Sydneyransel/weather-api-pipeline`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `WEATHERAPI_KEY`
5. Value: `e32648ad4a3f40f9bbe175111261304`
6. Click **Add secret**

- [ ] **Step 2: Remove the hardcoded key from git history awareness**

The key was committed in an earlier commit. Since the repo is public, rotate the key on weatherapi.com (generate a new one) after adding it as a secret, then update the secret value. The old key in git history will be dead.

- [ ] **Step 3: Push everything to GitHub**

```bash
git push origin main
```

- [ ] **Step 4: Trigger a manual test run**

1. Go to `https://github.com/Sydneyransel/weather-api-pipeline/actions`
2. Click **Weather Pipeline** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Watch the run complete — all steps should show green checkmarks
5. After it finishes, check the repo — a new commit from `github-actions[bot]` should appear updating `weather_data.csv`
