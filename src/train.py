"""
train.py - Time-series forecast model training.
Generates 5000 synthetic "days" with autocorrelated AQI,
seasonal/weekend patterns, and weather coupling.
Trains GradientBoostingRegressor for 7-day AQI forecasting.
Saves to model/forecast_model.pkl
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle

from src.logic import compute_aqi


def _seasonal_offset(month):
    """Indian seasonal AQI offset: winter high, monsoon low."""
    offsets = {1: 60, 2: 50, 3: 30, 4: 10, 5: 0, 6: -25,
               7: -35, 8: -30, 9: -10, 10: 20, 11: 55, 12: 65}
    return offsets.get(month, 0)


def generate_time_series(n_days=5000, seed=42):
    """Generate synthetic daily AQI time-series with realistic patterns."""
    rng = np.random.RandomState(seed)

    # Base pollutant concentrations (log-normal, right-skewed)
    base_pm25 = np.clip(rng.lognormal(3.2, 0.7, n_days), 1, 500)

    aqi_series = []
    prev_aqi = 100.0  # starting point

    for i in range(n_days):
        day_of_week = i % 7
        month = (i // 30) % 12 + 1

        # EPA AQI from base pollutants
        pm25 = base_pm25[i]
        pm10 = pm25 * rng.uniform(1.6, 2.2)
        no2 = pm25 * rng.uniform(0.3, 0.9)
        raw_aqi = compute_aqi(pm25, pm10, no2)

        # Seasonal offset
        raw_aqi += _seasonal_offset(month) * rng.uniform(0.6, 1.4)

        # Weekend dip (Sat=5, Sun=6)
        if day_of_week >= 5:
            raw_aqi *= rng.uniform(0.85, 0.92)

        # Weather effects
        temp = rng.uniform(8, 42)
        humidity = rng.uniform(25, 90)
        if humidity > 70:
            raw_aqi *= rng.uniform(1.05, 1.20)
        if temp > 35:
            raw_aqi *= rng.uniform(0.90, 0.95)

        # Autocorrelation: strong persistence
        raw_aqi = 0.82 * prev_aqi + 0.18 * raw_aqi

        # Noise
        raw_aqi += rng.normal(0, 5)
        raw_aqi = np.clip(raw_aqi, 0, 500)

        aqi_series.append({
            "aqi": raw_aqi, "temp": temp, "humidity": humidity,
            "day_of_week": day_of_week, "month": month,
            "is_weekend": 1 if day_of_week >= 5 else 0,
        })
        prev_aqi = raw_aqi

    return aqi_series


def build_features(series):
    """Convert raw time-series to ML features with lag/rolling columns."""
    rows = []
    for i in range(7, len(series) - 1):
        cur = series[i]
        rows.append({
            "aqi_lag1": series[i - 1]["aqi"],
            "aqi_lag7": series[i - 7]["aqi"],
            "aqi_rolling3": np.mean([series[i - k]["aqi"] for k in range(1, 4)]),
            "temp": cur["temp"],
            "humidity": cur["humidity"],
            "day_of_week": cur["day_of_week"],
            "month": cur["month"],
            "is_weekend": cur["is_weekend"],
            "aqi_next": series[i + 1]["aqi"],  # target
        })
    return pd.DataFrame(rows)


def train_model():
    print("=" * 60)
    print("  AQI Forecast Model Training Pipeline")
    print("=" * 60)

    print("\n[1/4] Generating synthetic time-series (5000 days)...")
    series = generate_time_series(5000)
    df = build_features(series)
    print(f"      Feature rows: {len(df)}")

    feat_cols = ["aqi_lag1", "aqi_lag7", "aqi_rolling3", "temp",
                 "humidity", "day_of_week", "month", "is_weekend"]
    X = df[feat_cols]
    y = df["aqi_next"]

    print("\n[2/4] Splitting 80/20...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    print("\n[3/4] Training GradientBoostingRegressor...")
    model = GradientBoostingRegressor(
        n_estimators=500, max_depth=5, learning_rate=0.08, random_state=42)
    model.fit(X_train, y_train)

    print("\n[4/4] Evaluating...")
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    print(f"\n  RMSE : {rmse:.2f}")
    print(f"  R2   : {r2:.4f}")
    print("\n  Feature Importances (top 5):")
    imp = sorted(zip(feat_cols, model.feature_importances_), key=lambda x: -x[1])
    for f, v in imp[:5]:
        print(f"    {f:>15s}: {v:.4f}")

    os.makedirs("model", exist_ok=True)
    with open("model/forecast_model.pkl", "wb") as f:
        pickle.dump(model, f)
    print(f"\n  Model saved to model/forecast_model.pkl")
    print("=" * 60)
    return model, rmse, r2


if __name__ == "__main__":
    train_model()