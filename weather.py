import requests
import json
import time
import pandas as pd

API_KEY = "e32648ad4a3f40f9bbe175111261304"

api_url = "https://api.weatherapi.com/v1/forecast.json" # 7-day forecast data

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
    "28601",  # Seattle, WA (Hickory area)
    "37201",  # Nashville, TN
]

results = []

for zip_code in zip_codes:
    params = {
        "key": API_KEY,
        "q": zip_code,
        "days": 7
    }

    response = requests.get(api_url, params=params)
    data = response.json()

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
            "condition": day["day"]["condition"]["text"]
        }
        results.append(result)

        print(f"  {result['date']}: High {result['max_temp_f']}°F, Low {result['min_temp_f']}°F, {result['condition']}")

    time.sleep(1)

df = pd.DataFrame(results)
print(df.to_string())
print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")

df.to_csv("weather_data.csv", index=False)
print("Saved to weather_data.csv")
