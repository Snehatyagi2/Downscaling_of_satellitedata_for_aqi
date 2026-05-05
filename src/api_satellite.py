"""
api_satellite.py - Open-Meteo Air Quality API integration.
Fetches real coarse-resolution (0.1deg) pollution data for satellite downscaling.
FREE, no API key required.
"""
import requests

# Session-level cache to avoid redundant API calls
_CACHE = {}


def fetch_coarse_grid(center_lat, center_lon, radius_deg=0.25):
    """
    Fetch current air quality from Open-Meteo for a 5x5 grid (0.1deg spacing).
    Returns dict keyed by (lat_rounded, lon_rounded) -> {pm25, pm10, no2}.
    Falls back to None on failure (caller handles fallback).
    """
    grid = {}
    lat_min = round(center_lat - radius_deg, 1)
    lon_min = round(center_lon - radius_deg, 1)

    # Generate 5x5 grid points at 0.1deg spacing
    lats = [round(lat_min + i * 0.1, 1) for i in range(5)]
    lons = [round(lon_min + i * 0.1, 1) for i in range(5)]

    for lat in lats:
        for lon in lons:
            key = (lat, lon)
            if key in _CACHE:
                grid[key] = _CACHE[key]
                continue
            try:
                data = _fetch_point(lat, lon)
                if data:
                    grid[key] = data
                    _CACHE[key] = data
            except Exception:
                continue

    return grid if len(grid) >= 5 else None


def _fetch_point(lat, lon):
    """Fetch latest hourly air quality for a single point."""
    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=pm2_5,pm10,nitrogen_dioxide"
        "&forecast_days=1"
    )
    resp = requests.get(url, timeout=8)
    if resp.status_code != 200:
        return None

    data = resp.json()
    hourly = data.get("hourly", {})
    pm25_vals = hourly.get("pm2_5", [])
    pm10_vals = hourly.get("pm10", [])
    no2_vals = hourly.get("nitrogen_dioxide", [])

    # Take last non-null value
    pm25 = _last_valid(pm25_vals, 30.0)
    pm10 = _last_valid(pm10_vals, 50.0)
    no2 = _last_valid(no2_vals, 20.0)

    return {"pm25": pm25, "pm10": pm10, "no2": no2}


def _last_valid(vals, default):
    """Return last non-null value from a list, or default."""
    for v in reversed(vals):
        if v is not None:
            return float(v)
    return default
