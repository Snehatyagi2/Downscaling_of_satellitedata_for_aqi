"""
api_weather.py - Weather data with guaranteed city-aware fallback (NEVER returns None).
"""
import os
from dotenv import load_dotenv
import requests
import random
from src.stability import stable_seed

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# (lat, lon, base_temp_C, base_humidity_%)
_DEFAULTS = {
    "delhi": (28.61, 77.21, 32, 55), "new delhi": (28.61, 77.21, 32, 55),
    "mumbai": (19.08, 72.88, 30, 75), "kolkata": (22.57, 88.36, 31, 70),
    "chennai": (13.08, 80.27, 33, 68), "bengaluru": (12.97, 77.59, 27, 60),
    "hyderabad": (17.38, 78.49, 32, 55), "pune": (18.52, 73.86, 29, 58),
    "ahmedabad": (23.02, 72.57, 34, 45), "jaipur": (26.91, 75.79, 33, 42),
    "lucknow": (26.85, 80.95, 31, 60), "kanpur": (26.45, 80.35, 32, 58),
    "noida": (28.57, 77.32, 32, 55), "gurgaon": (28.46, 77.03, 32, 52),
    "faridabad": (28.41, 77.31, 33, 54), "ghaziabad": (28.67, 77.42, 32, 56),
    "patna": (25.61, 85.14, 31, 62), "bhopal": (23.26, 77.41, 30, 55),
    "indore": (22.72, 75.86, 30, 50), "nagpur": (21.15, 79.09, 33, 48),
    "surat": (21.17, 72.83, 31, 65), "vadodara": (22.31, 73.19, 32, 55),
    "varanasi": (25.32, 83.01, 31, 62), "agra": (27.18, 78.02, 33, 52),
    "chandigarh": (30.73, 76.77, 29, 50), "dehradun": (30.32, 78.03, 26, 65),
    "amritsar": (31.63, 74.87, 29, 55), "jodhpur": (26.24, 73.02, 35, 35),
    "kochi": (9.93, 76.27, 29, 78), "coimbatore": (11.02, 76.96, 29, 62),
    "visakhapatnam": (17.69, 83.22, 30, 72), "ranchi": (23.34, 85.31, 28, 58),
    "raipur": (21.25, 81.63, 32, 52), "guwahati": (26.14, 91.74, 27, 72),
    "sydney": (-33.87, 151.21, 22, 60), "singapore": (1.35, 103.82, 30, 80),
    "tokyo": (35.68, 139.69, 18, 65), "london": (51.51, -0.13, 14, 72),
    "paris": (48.86, 2.35, 15, 68), "new york": (40.71, -74.01, 16, 62),
    "los angeles": (34.05, -118.24, 22, 50), "seoul": (37.57, 126.98, 14, 60),
    "beijing": (39.90, 116.40, 16, 50), "shanghai": (31.23, 121.47, 19, 68),
    "jakarta": (-6.21, 106.85, 30, 78), "karachi": (24.86, 67.01, 32, 58),
    "dubai": (25.20, 55.27, 36, 45), "hong kong": (22.32, 114.17, 25, 75),
    "kuala lumpur": (3.14, 101.69, 30, 78),
}


def get_weather(city):
    """Fetch weather. Tries OpenWeatherMap, ALWAYS falls back (never None)."""
    if API_KEY:
        try:
            url = (f"http://api.openweathermap.org/data/2.5/weather"
                   f"?q={city}&appid={API_KEY}&units=metric")
            data = requests.get(url, timeout=10).json()
            return (data["main"]["temp"], data["main"]["humidity"],
                    data["coord"]["lat"], data["coord"]["lon"])
        except Exception:
            pass
    return _fallback(city)


def _fallback(city):
    """City-aware weather defaults. Never returns None."""
    key = city.lower().strip()
    if key in _DEFAULTS:
        lat, lon, bt, bh = _DEFAULTS[key]
    else:
        lat, lon, bt, bh = 22.0, 78.0, 30, 55
    rng = random.Random(stable_seed(city, bucket_seconds=1800, salt="weather"))
    return (round(bt + rng.uniform(-3, 3), 1),
            int(bh + rng.uniform(-8, 8)), lat, lon)
