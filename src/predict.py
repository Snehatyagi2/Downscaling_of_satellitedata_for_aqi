"""
predict.py - AQI prediction (EPA formula), 7-day forecast (ML), report generation.
"""
import pickle
import numpy as np
import pandas as pd
import datetime
from src.api_pollution import get_pollution, get_pollution_history
from src.api_weather import get_weather
from src.logic import compute_aqi, pollution_score, locality_type, detailed_reason

_forecast_model = None


def _load_forecast_model():
    global _forecast_model
    if _forecast_model is None:
        with open("model/forecast_model.pkl", "rb") as f:
            _forecast_model = pickle.load(f)
    return _forecast_model


def predict_aqi(pm25, pm10, no2, temp=None, humidity=None):
    """Current AQI via deterministic EPA formula. No ML needed."""
    return float(compute_aqi(pm25, pm10, no2))


def smart_forecast(current_aqi, temp, humidity, history):
    """
    7-day recursive (autoregressive) AQI forecast using GBR model.
    history: list of recent AQI values (minimum 7; padded if shorter).
    Returns: list of 7 predicted AQI values.
    """
    model = _load_forecast_model()

    # Pad history if too short
    window = list(history) if history else []
    while len(window) < 7:
        window.insert(0, current_aqi)
    window.append(current_aqi)

    now = datetime.datetime.now()
    today_dow = now.weekday()
    month = now.month

    preds = []
    for day_offset in range(1, 8):
        lag1 = window[-1]
        lag7 = window[-7] if len(window) >= 7 else window[0]
        rolling3 = float(np.mean(window[-3:]))
        dow = (today_dow + day_offset) % 7
        is_weekend = 1 if dow >= 5 else 0

        feat_cols = ["aqi_lag1", "aqi_lag7", "aqi_rolling3", "temp",
                     "humidity", "day_of_week", "month", "is_weekend"]
        features = pd.DataFrame([[lag1, lag7, rolling3, temp, humidity,
                                   dow, month, is_weekend]], columns=feat_cols)
        predicted = float(np.clip(model.predict(features)[0], 0, 500))
        preds.append(round(predicted, 2))
        window.append(predicted)

    return preds


def satellite_downscaling(temp, humidity, lat, lon, city="Delhi"):
    """Run satellite downscaling pipeline. Returns list of {lat, lon, aqi}."""
    from src.satellite import generate_satellite_grid
    return generate_satellite_grid(lat, lon, city=city, n_points=50)


def generate_report(city="Delhi"):
    """Generate full AQI report for all stations in a city."""
    pollution = get_pollution(city)
    history = get_pollution_history(city)
    weather = get_weather(city)

    if not pollution or weather is None:
        return None

    temp, humidity, lat, lon = weather
    report = []

    for p in pollution:
        pm25, pm10, no2 = p["pm25"], p["pm10"], p["no2"]

        aqi = predict_aqi(pm25, pm10, no2)
        score = pollution_score(pm25, pm10, no2)
        area = locality_type(p["location"])
        reason = detailed_reason(aqi, area, pm25, pm10, no2)
        forecast = smart_forecast(aqi, temp, humidity, history)

        report.append({
            "location": p["location"],
            "aqi": round(aqi, 2),
            "score": round(score, 2),
            "area": area,
            "forecast": forecast,
            "reason": reason,
        })

    return report