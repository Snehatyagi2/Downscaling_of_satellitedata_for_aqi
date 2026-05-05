"""
satellite.py - Real satellite downscaling pipeline.
Fetches coarse Open-Meteo data, generates fine-resolution auxiliary features,
and uses a trained downscaling RF model to predict sub-grid AQI variation.
"""
import os
import pickle
import random
import math
import numpy as np
from src.logic import compute_aqi
from src.api_satellite import fetch_coarse_grid

# ─── City Bounding Boxes ────────────────────────────────────────────────────

_CITY_BBOX = {
    "delhi": (28.4, 28.9, 76.8, 77.4), "new delhi": (28.4, 28.9, 76.8, 77.4),
    "mumbai": (18.9, 19.3, 72.7, 73.0), "bengaluru": (12.8, 13.2, 77.4, 77.8),
    "chennai": (12.9, 13.2, 80.1, 80.4), "kolkata": (22.4, 22.7, 88.2, 88.5),
    "hyderabad": (17.2, 17.6, 78.3, 78.7), "pune": (18.4, 18.7, 73.7, 74.0),
}

# ─── Land Use Types ─────────────────────────────────────────────────────────

LAND_TYPES = ["Industrial", "Residential", "Commercial", "Green"]
_LAND_ENCODE = {"Industrial": 0, "Residential": 1, "Commercial": 2, "Green": 3}
_NDVI = {"Industrial": 0.1, "Residential": 0.3, "Commercial": 0.2, "Green": 0.6}
_POP = {"Industrial": 0.3, "Residential": 0.9, "Commercial": 0.7, "Green": 0.1}
_SPATIAL_MUL = {"Industrial": (1.4, 1.8), "Residential": (0.9, 1.1),
                "Commercial": (1.1, 1.3), "Green": (0.5, 0.7)}

# ─── City-tier fallback ranges ──────────────────────────────────────────────

_TIER_MAP = {
    "delhi": "very_high", "new delhi": "very_high", "noida": "very_high",
    "gurgaon": "very_high", "faridabad": "very_high", "ghaziabad": "very_high",
    "kanpur": "very_high", "lucknow": "very_high", "patna": "very_high",
    "mumbai": "high", "kolkata": "high", "chennai": "high",
    "bengaluru": "high", "hyderabad": "high", "pune": "high",
    "ahmedabad": "high", "jaipur": "high",
    "sydney": "clean", "singapore": "clean", "tokyo": "clean",
    "london": "clean", "paris": "clean", "new york": "clean",
    "los angeles": "clean", "seoul": "clean",
    "beijing": "polluted", "jakarta": "polluted", "karachi": "polluted",
    "shanghai": "polluted", "dubai": "polluted",
}
_TIER_RANGES = {
    "very_high": (80, 180, 120, 280, 40, 110),
    "high": (40, 110, 80, 190, 25, 75),
    "moderate": (25, 70, 50, 130, 15, 50),
    "clean": (5, 22, 10, 38, 5, 22),
    "polluted": (50, 140, 80, 210, 30, 85),
}

_downscale_model = None


def _get_fallback_coarse(city):
    """City-tier based fallback when Open-Meteo is unavailable."""
    tier = _TIER_MAP.get(city.lower().strip(), "moderate")
    r = _TIER_RANGES[tier]
    return {
        "pm25": random.uniform(r[0], r[1]),
        "pm10": random.uniform(r[2], r[3]),
        "no2": random.uniform(r[4], r[5]),
    }


def _assign_land_use(lat, lon, center_lat, center_lon):
    """Assign land use based on quadrant + distance from center."""
    dlat = lat - center_lat
    dlon = lon - center_lon
    dist = math.sqrt(dlat**2 + dlon**2)
    quad = (1 if dlat >= 0 else 0) * 2 + (1 if dlon >= 0 else 0)
    # Simple spatial pattern: industrial in NE, green in SW
    if dist < 0.05:
        return "Commercial"
    patterns = {0: "Green", 1: "Residential", 2: "Industrial", 3: "Residential"}
    base = patterns.get(quad, "Mixed")
    # Add some randomness
    if random.random() < 0.25:
        return random.choice(LAND_TYPES)
    return base


def _dist_to_road(lat, lon, center_lat, center_lon):
    """Simulated distance to nearest major road (km)."""
    # Roads run along major axes through city center
    dlat = abs(lat - center_lat)
    dlon = abs(lon - center_lon)
    return min(dlat, dlon) * 111  # degrees to km approx


def _train_downscale_model():
    """Train a downscaling RF model on synthetic fine-resolution data."""
    rng = np.random.RandomState(99)
    n = 2000
    rows = []

    for _ in range(n):
        coarse_pm25 = rng.uniform(5, 200)
        coarse_pm10 = rng.uniform(10, 300)
        coarse_no2 = rng.uniform(3, 120)
        land = rng.choice(LAND_TYPES)
        dist_road = rng.uniform(0.1, 8.0)
        elev_delta = rng.uniform(-20, 20)
        ndvi = _NDVI[land] + rng.normal(0, 0.05)
        pop = _POP[land] + rng.normal(0, 0.05)
        lat_off = rng.uniform(-0.25, 0.25)
        lon_off = rng.uniform(-0.25, 0.25)

        # Spatial multiplier based on land use and road proximity
        mul_lo, mul_hi = _SPATIAL_MUL[land]
        road_boost = max(0, (3 - dist_road) / 3) * 0.2  # closer to road = higher
        mul = rng.uniform(mul_lo, mul_hi) + road_boost

        fine_pm25 = coarse_pm25 * mul
        fine_pm10 = coarse_pm10 * mul * rng.uniform(0.95, 1.05)
        fine_no2 = coarse_no2 * mul * rng.uniform(0.9, 1.1)
        fine_aqi = compute_aqi(fine_pm25, fine_pm10, fine_no2)

        rows.append([
            coarse_no2, coarse_pm25, coarse_pm10, dist_road,
            _LAND_ENCODE[land], elev_delta, ndvi, pop, lat_off, lon_off,
            fine_aqi
        ])

    data = np.array(rows)
    X = data[:, :10]
    y = data[:, 10]

    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X, y)

    os.makedirs("model", exist_ok=True)
    with open("model/downscale_model.pkl", "wb") as f:
        pickle.dump(model, f)
    return model


def _load_downscale_model():
    """Load or train the downscaling model."""
    global _downscale_model
    if _downscale_model is not None:
        return _downscale_model

    model_path = "model/downscale_model.pkl"
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            _downscale_model = pickle.load(f)
    else:
        _downscale_model = _train_downscale_model()
    return _downscale_model


def generate_satellite_grid(center_lat, center_lon, city="Delhi", n_points=50):
    """
    Full downscaling pipeline:
    1. Fetch coarse data from Open-Meteo (or fallback)
    2. Generate fine-resolution points with auxiliary features
    3. Predict fine AQI using downscaling model
    Returns list of {lat, lon, aqi, land_use, coarse_aqi, delta}
    """
    model = _load_downscale_model()

    # Determine bounding box
    key = city.lower().strip()
    if key in _CITY_BBOX:
        lat_min, lat_max, lon_min, lon_max = _CITY_BBOX[key]
    else:
        lat_min, lat_max = center_lat - 0.25, center_lat + 0.25
        lon_min, lon_max = center_lon - 0.25, center_lon + 0.25

    # Fetch coarse grid from Open-Meteo
    coarse_grid = fetch_coarse_grid(center_lat, center_lon)
    use_fallback = coarse_grid is None

    # Build coarse lookup
    def get_coarse(lat, lon):
        if use_fallback:
            return _get_fallback_coarse(city)
        # Snap to nearest 0.1 degree
        snapped = (round(lat, 1), round(lon, 1))
        if snapped in coarse_grid:
            return coarse_grid[snapped]
        # Find nearest available
        best = min(coarse_grid.keys(),
                   key=lambda k: (k[0]-lat)**2 + (k[1]-lon)**2)
        return coarse_grid[best]

    results = []
    for _ in range(n_points):
        lat = random.uniform(lat_min, lat_max)
        lon = random.uniform(lon_min, lon_max)

        coarse = get_coarse(lat, lon)
        land_use = _assign_land_use(lat, lon, center_lat, center_lon)
        dist_road = _dist_to_road(lat, lon, center_lat, center_lon)
        elev_delta = random.uniform(-20, 20)
        ndvi = _NDVI[land_use] + random.gauss(0, 0.03)
        pop = _POP[land_use] + random.gauss(0, 0.03)

        features = np.array([[
            coarse["no2"], coarse["pm25"], coarse["pm10"], dist_road,
            _LAND_ENCODE[land_use], elev_delta, ndvi, pop,
            lat - center_lat, lon - center_lon,
        ]])

        fine_aqi = float(np.clip(model.predict(features)[0], 0, 500))
        coarse_aqi = float(compute_aqi(coarse["pm25"], coarse["pm10"], coarse["no2"]))

        results.append({
            "lat": lat,
            "lon": lon,
            "aqi": round(fine_aqi, 1),
            "land_use": land_use,
            "coarse_aqi": round(coarse_aqi, 1),
            "delta": round(fine_aqi - coarse_aqi, 1),
        })

    return results