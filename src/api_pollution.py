"""
api_pollution.py - City-tier-aware pollution data fetching with OpenAQ fallback.
"""
import os
from dotenv import load_dotenv
import requests
import random
from src.stability import stable_seed

load_dotenv()
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY", "")

# ─── City Tier System ───────────────────────────────────────────────────────

# (pm25_lo, pm25_hi, pm10_lo, pm10_hi, no2_lo, no2_hi)
CITY_TIERS = {
    "very_high": (80, 200, 120, 300, 40, 120),
    "high":      (40, 120, 80, 200, 25, 80),
    "moderate":  (30, 90, 60, 150, 15, 60),
    "clean":     (5, 25, 10, 40, 5, 25),
    "polluted":  (50, 150, 80, 220, 30, 90),
}

_CITY_TIER_MAP = {
    # Delhi NCR
    "delhi": "very_high", "new delhi": "very_high", "noida": "very_high",
    "gurgaon": "very_high", "gurugram": "very_high", "faridabad": "very_high",
    "ghaziabad": "very_high", "kanpur": "very_high", "lucknow": "very_high",
    "patna": "very_high", "varanasi": "very_high", "agra": "very_high",
    # Major Indian metros
    "mumbai": "high", "kolkata": "high", "chennai": "high",
    "bengaluru": "high", "bangalore": "high", "hyderabad": "high",
    "pune": "high", "ahmedabad": "high", "jaipur": "high",
    "surat": "high", "nagpur": "high", "indore": "high",
    # International clean
    "sydney": "clean", "singapore": "clean", "tokyo": "clean",
    "london": "clean", "paris": "clean", "seoul": "clean",
    "new york": "clean", "los angeles": "clean",
    # International polluted
    "beijing": "polluted", "jakarta": "polluted", "karachi": "polluted",
    "shanghai": "polluted", "dubai": "polluted", "dhaka": "polluted",
    "hong kong": "polluted", "kuala lumpur": "polluted",
}


def get_city_tier(city):
    return _CITY_TIER_MAP.get(city.lower().strip(), "moderate")


def get_city_pollution_ranges(city):
    """Return (pm25_lo, pm25_hi, pm10_lo, pm10_hi, no2_lo, no2_hi)."""
    return CITY_TIERS[get_city_tier(city)]


def get_city_no2_range(city):
    """Helper for satellite module."""
    r = get_city_pollution_ranges(city)
    return r[4], r[5]


# ─── Pollution API ──────────────────────────────────────────────────────────

def get_pollution(city):
    """Fetch pollution data. Tries OpenAQ, falls back to city-aware simulation."""
    if OPENAQ_API_KEY:
        try:
            data = _fetch_openaq_v3(city)
            if data and any(d["pm25"] > 0 or d["pm10"] > 0 or d["no2"] > 0
                           for d in data):
                return data
        except Exception:
            pass
    return _generate_simulated_pollution(city)


def _fetch_openaq_v3(city):
    """Fetch data from OpenAQ v3 API."""
    headers = {"X-API-Key": OPENAQ_API_KEY}
    url = f"https://api.openaq.org/v3/locations?city={city}&limit=10"
    resp = requests.get(url, headers=headers, timeout=10)
    locations_data = resp.json()
    results = []
    for loc in locations_data.get("results", []):
        location_id = loc.get("id")
        location_name = loc.get("name", "Unknown")
        latest_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
        latest_resp = requests.get(latest_url, headers=headers, timeout=10)
        latest_data = latest_resp.json()
        pollutants = {}
        for sensor in latest_data.get("results", []):
            param = sensor.get("parameter", {})
            param_name = param.get("name", "")
            value = sensor.get("value", 0)
            pollutants[param_name.lower()] = value
        results.append({
            "location": location_name,
            "pm25": pollutants.get("pm25", pollutants.get("pm2.5", 0)),
            "pm10": pollutants.get("pm10", 0),
            "no2": pollutants.get("no2", 0),
        })
    return results


def _generate_simulated_pollution(city):
    """City-tier-aware simulated pollution with station-type modifiers."""
    pm25_lo, pm25_hi, pm10_lo, pm10_hi, no2_lo, no2_hi = get_city_pollution_ranges(city)
    rng = random.Random(stable_seed(city, bucket_seconds=1800, salt="pollution"))

    stations = [
        ("{city} - Central Station", 1.0),
        ("{city} - Industrial Area", 1.4),
        ("{city} - Traffic Junction", 1.2),
        ("{city} - Residential Colony", 0.6),
        ("{city} - University Campus", 0.5),
    ]

    results = []
    for template, mod in stations:
        location = template.format(city=city)
        results.append({
            "location": location,
            "pm25": round(max(1, rng.uniform(pm25_lo * mod, pm25_hi * mod)), 2),
            "pm10": round(max(2, rng.uniform(pm10_lo * mod, pm10_hi * mod)), 2),
            "no2": round(max(1, rng.uniform(no2_lo * mod, no2_hi * mod)), 2),
        })
    return results


def get_pollution_history(city):
    """Historical AQI values. Tries OpenAQ, falls back to city-aware simulation."""
    if OPENAQ_API_KEY:
        try:
            return _fetch_history_v3(city)
        except Exception:
            pass
    # Simulated: generate realistic AQI history for city tier
    from src.logic import compute_aqi
    ranges = get_city_pollution_ranges(city)
    rng = random.Random(stable_seed(city, bucket_seconds=1800, salt="history"))
    history = []
    for _ in range(10):
        pm25 = rng.uniform(ranges[0], ranges[1])
        pm10 = rng.uniform(ranges[2], ranges[3])
        no2 = rng.uniform(ranges[4], ranges[5])
        history.append(round(compute_aqi(pm25, pm10, no2), 2))
    return history


def _fetch_history_v3(city):
    """Fetch historical from OpenAQ v3."""
    headers = {"X-API-Key": OPENAQ_API_KEY}
    url = f"https://api.openaq.org/v3/locations?city={city}&limit=1"
    resp = requests.get(url, headers=headers, timeout=10)
    locations_data = resp.json()
    results = locations_data.get("results", [])
    if not results:
        return None
    location_id = results[0].get("id")
    meas_url = (f"https://api.openaq.org/v3/locations/{location_id}"
                f"/measurements?parameter_id=2&limit=100")
    meas_resp = requests.get(meas_url, headers=headers, timeout=10)
    meas_data = meas_resp.json()
    history = [item.get("value", 0) for item in meas_data.get("results", [])
               if item.get("value") is not None]
    return history[:10] if history else None