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
