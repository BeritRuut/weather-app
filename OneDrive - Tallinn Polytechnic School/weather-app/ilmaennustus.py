import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"  
LAT, LON = 59.437, 24.754  # Tallinn
USER_AGENT = "ilmaharjutusberit.ruut@techno.ee"
DAYS = 3
STEP_HOURS = 4

WEEKDAYS = ["Esmaspäev", "Teisipäev", "Kolmapäev", "Neljapäev",
            "Reede", "Laupäev", "Pühapäev"]


def fetch_forecast():
    """Küsib Yr.no käest ennustuse ja tagastab tundide listi."""
    response = requests.get(
        URL,
        params={"lat": LAT, "lon": LON},
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["properties"]["timeseries"]


def to_local(text):
    """Muudab '2026-10-28T10:00:00Z' Eesti ajaks."""
    utc_time = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return utc_time.astimezone(ZoneInfo("Europe/Tallinn"))


def get_rain_probability(entry):
    """Tagastab vihma tõenäosuse (%) või None, kui seda ei ole."""
    data = entry["data"]
    for period in ("next_1_hours", "next_6_hours", "next_12_hours"):
        if period in data:
            probability = data[period]["details"].get("probability_of_precipitation")
            if probability is not None:
                return probability
    return None


def main():
    timeseries = fetch_forecast()

    start = to_local(timeseries[0]["time"])
    end = start + timedelta(days=DAYS)

    print(f"Tallinna ilmaennustus ({DAYS} päeva, iga {STEP_HOURS} tunni tagant)")
    current_day = None

    for entry in timeseries:
        time = to_local(entry["time"])
        if time >= end:
            break

        if time.hour % STEP_HOURS != 0:
            continue

        temperature = entry["data"]["instant"]["details"]["air_temperature"]

        rain = get_rain_probability(entry)
        rain_text = f"{rain:3.0f} %" if rain is not None else "  –"

        if time.date() != current_day:
            current_day = time.date()
            print(f"\n{WEEKDAYS[time.weekday()]} {time:%d.%m}")
            print("-" * 30)

        print(f"  {time:%H:%M}   {temperature:5.1f} °C   vihm {rain_text}")


main()