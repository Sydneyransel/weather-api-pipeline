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

    if not results:
        print("WARNING: no data fetched; CSV unchanged.")
    else:
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
