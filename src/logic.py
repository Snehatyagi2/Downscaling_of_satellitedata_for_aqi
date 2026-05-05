"""
logic.py - EPA AQI deterministic formulas, classification, and reasoning.
Implements the full US EPA breakpoint interpolation for PM2.5, PM10, NO2.
"""
import math

# ─── EPA Breakpoint Tables: (C_lo, C_hi, AQI_lo, AQI_hi) ──────────────────

_PM25_BP = [
    (0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500),
]
_PM10_BP = [
    (0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
    (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500),
]
_NO2_PPB_BP = [
    (0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
    (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 2049, 301, 500),
]


def _interp(c, bp):
    """Linear interpolation within EPA breakpoints."""
    for c_lo, c_hi, a_lo, a_hi in bp:
        if c_lo <= c <= c_hi:
            return round(((a_hi - a_lo) / (c_hi - c_lo)) * (c - c_lo) + a_lo)
    return 500 if c > bp[-1][1] else 0


def pm25_to_aqi(pm25):
    """PM2.5 µg/m³ → AQI (truncate to 1 decimal per EPA)."""
    return _interp(math.floor(max(pm25, 0) * 10) / 10, _PM25_BP)


def pm10_to_aqi(pm10):
    """PM10 µg/m³ → AQI (truncate to integer per EPA)."""
    return _interp(int(max(pm10, 0)), _PM10_BP)


def no2_to_aqi(no2_ugm3):
    """NO2 µg/m³ → AQI (convert to ppb first: divide by 1.88, truncate)."""
    ppb = int(max(no2_ugm3, 0) / 1.88)
    return _interp(ppb, _NO2_PPB_BP)


def compute_aqi(pm25, pm10, no2):
    """Composite AQI = max of per-pollutant sub-AQIs (official EPA rule)."""
    return max(pm25_to_aqi(pm25), pm10_to_aqi(pm10), no2_to_aqi(no2))


def pollution_score(pm25, pm10, no2):
    """Weighted pollution score used as a forecast input feature."""
    return pm25 * 0.5 + pm10 * 0.3 + no2 * 0.2


def locality_type(location):
    """Classify station into area type from name keywords."""
    loc = location.lower()
    if any(k in loc for k in ("industrial", "factory", "smelter", "plant")):
        return "Industrial"
    if any(k in loc for k in ("road", "traffic", "highway", "junction",
                               "chowk", "crossing", "flyover")):
        return "Traffic"
    if any(k in loc for k in ("residential", "colony", "nagar", "vihar",
                               "enclave", "housing", "apartment")):
        return "Residential"
    if any(k in loc for k in ("university", "campus", "school", "park",
                               "garden", "green", "forest")):
        return "Residential"
    return "Mixed"


def _severity(aqi):
    if aqi <= 50: return "Good"
    if aqi <= 100: return "Moderate"
    if aqi <= 150: return "Unhealthy for Sensitive Groups"
    if aqi <= 200: return "Unhealthy"
    if aqi <= 300: return "Very Unhealthy"
    return "Hazardous"


def _dominant(pm25, pm10, no2):
    scores = {"PM2.5": pm25_to_aqi(pm25), "PM10": pm10_to_aqi(pm10),
              "NO2": no2_to_aqi(no2)}
    return max(scores, key=scores.get)


def detailed_reason(aqi, area, pm25, pm10=0, no2=0):
    """Rich 1-2 sentence explanation based on dominant pollutant, area, severity."""
    sev = _severity(aqi)
    dom = _dominant(pm25, pm10, no2)

    pol_clause = {
        "PM2.5": "fine particulate matter (PM2.5) from combustion sources",
        "PM10": "coarse dust particles (PM10) from road dust and construction",
        "NO2": "nitrogen dioxide (NO2) from vehicular and industrial emissions",
    }[dom]

    area_clause = {
        "Industrial": "amplified by nearby factory and manufacturing emissions",
        "Traffic": "worsened by heavy vehicular congestion and tailpipe exhaust",
        "Residential": "likely from domestic cooking fuels and local traffic",
        "Mixed": "from a combination of urban emission sources",
    }.get(area, "from mixed urban sources")

    advice = {
        "Good": "Air quality is satisfactory with minimal health risk.",
        "Moderate": "Sensitive individuals should limit prolonged outdoor exertion.",
        "Unhealthy for Sensitive Groups": "Children and elderly should reduce outdoor activity.",
        "Unhealthy": "Everyone should reduce prolonged outdoor exertion; wear masks if needed.",
        "Very Unhealthy": "Avoid outdoor activities; use air purifiers indoors.",
        "Hazardous": "Health emergency — stay indoors with air purifiers running.",
    }[sev]

    return f"Elevated AQI driven by {pol_clause}, {area_clause}. {advice}"