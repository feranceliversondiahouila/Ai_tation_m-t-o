# ============================================================
# IMPORTS
# ============================================================

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime
from typing import Optional
from collections import defaultdict

from network_checker import is_network_available
from ai_model import predict_edge, calculate_smart_indexes


# ============================================================
# CRÉATION DE L'APPLICATION FASTAPI
# ============================================================

app = FastAPI(
    title="Station Météo IA - Backend API",
    version="4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# BASE DE DONNÉES LOCALE DES VILLES (accès rapide, sans réseau)
# ============================================================

CITIES_COORDS = {
    "bethune": {"name": "Béthune", "lat": 50.53, "lon": 2.64},
    "lille": {"name": "Lille", "lat": 50.63, "lon": 3.06},
    "paris": {"name": "Paris", "lat": 48.85, "lon": 2.35},
    "lyon": {"name": "Lyon", "lat": 45.76, "lon": 4.84},
    "marseille": {"name": "Marseille", "lat": 43.30, "lon": 5.37},
    "toulouse": {"name": "Toulouse", "lat": 43.60, "lon": 1.44},
    "nantes": {"name": "Nantes", "lat": 47.22, "lon": -1.55},
    "pointe-noire": {"name": "Pointe-Noire", "lat": -4.78, "lon": 11.86},
}


@app.get("/cities")
def get_cities():
    """Liste des villes de sélection rapide, pour les boutons du frontend."""
    return [
        {"key": key, "name": v["name"], "lat": v["lat"], "lon": v["lon"]}
        for key, v in CITIES_COORDS.items()
    ]


# ============================================================
# CONVERSION D'UNE VILLE EN COORDONNÉES GPS
# ============================================================

def get_coordinates_from_city(city_name: str):
    city_clean = city_name.strip().lower()

    if city_clean in CITIES_COORDS:
        return (
            CITIES_COORDS[city_clean]["lat"],
            CITIES_COORDS[city_clean]["lon"],
            CITIES_COORDS[city_clean]["name"]
        )

    try:
        geo_url = (
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city_name}&count=1&language=fr&format=json"
        )
        res = requests.get(geo_url, timeout=2.0).json()

        if "results" in res and len(res["results"]) > 0:
            item = res["results"][0]
            return (item["latitude"], item["longitude"], item["name"])

    except Exception:
        pass

    return (50.53, 2.64, city_name.capitalize())


# ============================================================
# TRADUCTION DES CODES MÉTÉO OPEN-METEO (WMO)
# ============================================================
# On renvoie un code simplifié utilisé par le frontend
# pour choisir une icône. Cela évite de dupliquer
# la logique d'icônes côté serveur ET côté client.

def weathercode_to_label(code: int) -> str:
    mapping = {
        0: "clear", 1: "mostly_clear", 2: "partly_cloudy", 3: "cloudy",
        45: "fog", 48: "fog",
        51: "drizzle", 53: "drizzle", 55: "drizzle",
        61: "rain", 63: "rain", 65: "rain",
        66: "freezing_rain", 67: "freezing_rain",
        71: "snow", 73: "snow", 75: "snow", 77: "snow",
        80: "showers", 81: "showers", 82: "showers",
        85: "snow_showers", 86: "snow_showers",
        95: "storm", 96: "storm", 99: "storm",
    }
    return mapping.get(code, "cloudy")


# ============================================================
# ROUTE PRINCIPALE
# ============================================================

@app.get("/weather")
def get_weather(
    city: str = Query("Pointe-Noire", description="Nom de la ville"),
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    if lat is None or lon is None:
        lat, lon, formatted_city_name = get_coordinates_from_city(city)
    else:
        formatted_city_name = city

    online = is_network_available()

    # ========================================================
    # MODE CONNECTÉ — vraies données Open-Meteo
    # ========================================================
    if online:
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&past_days=2&forecast_days=7"
                f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
                f"wind_direction_10m,pressure_msl,cloud_cover,weather_code"
                f"&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,"
                f"wind_speed_10m,weather_code"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
                f"precipitation_probability_max,sunrise,sunset"
                f"&timezone=auto"
            )

            data = requests.get(url, timeout=4.0).json()

            # ---- Météo actuelle ----
            current_temp = data["current"]["temperature_2m"]
            humidity = data["current"]["relative_humidity_2m"]
            wind_speed = data["current"]["wind_speed_10m"]
            wind_direction = data["current"]["wind_direction_10m"]
            pressure = data["current"]["pressure_msl"]
            cloud_cover = data["current"]["cloud_cover"]
            current_weathercode = data["current"]["weather_code"]

            # ---- Lever / coucher du soleil (aujourd'hui = index 2, car past_days=2) ----
            sunrise_raw = data["daily"]["sunrise"][2] if len(data["daily"]["sunrise"]) > 2 else "N/A"
            sunset_raw = data["daily"]["sunset"][2] if len(data["daily"]["sunset"]) > 2 else "N/A"
            sunrise = sunrise_raw.split("T")[1] if "T" in sunrise_raw else sunrise_raw
            sunset = sunset_raw.split("T")[1] if "T" in sunset_raw else sunset_raw

            # ---- Prévisions journalières (J-2 à J+7, cliquables) ----
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily_forecast = [
                {
                    "date": data["daily"]["time"][i],
                    "temp_max": data["daily"]["temperature_2m_max"][i],
                    "temp_min": data["daily"]["temperature_2m_min"][i],
                    "rain_prob": data["daily"]["precipitation_probability_max"][i],
                    "weather_label": weathercode_to_label(data["daily"]["weather_code"][i]),
                    "is_today": data["daily"]["time"][i] == today_str,
                }
                for i in range(len(data["daily"]["time"]))
            ]

            # ---- Données horaires ----
            times = data["hourly"]["time"]
            temps = data["hourly"]["temperature_2m"]
            humi = data["hourly"]["relative_humidity_2m"]
            precip = data["hourly"].get("precipitation_probability", [0] * len(times))
            winds = data["hourly"].get("wind_speed_10m", [wind_speed] * len(times))
            codes = data["hourly"].get("weather_code", [current_weathercode] * len(times))

            now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
            current_idx = times.index(now_str) if now_str in times else 48
            current_rain_prob = precip[current_idx] if current_idx < len(precip) else 0

            # ---- Regroupement horaire PAR JOUR (clic sur un jour = navigation) ----
            # Permet au frontend d'afficher avant-hier / hier / aujourd'hui / demain
            # (et tous les autres jours disponibles) en cliquant sur une carte de jour.
            hourly_by_date = defaultdict(list)
            for i, t in enumerate(times):
                date_key = t.split("T")[0]
                hourly_by_date[date_key].append({
                    "time": t,
                    "temp_c": temps[i],
                    "humidity": humi[i],
                    "wind_speed": winds[i],
                    "rain_prob": precip[i],
                    "weather_label": weathercode_to_label(codes[i]),
                    "is_now": (i == current_idx),
                })

            # ---- Prédiction +1h : on utilise directement la vraie prévision Open-Meteo ----
            # (plus fiable qu'un modèle local, et évite tout problème de features)
            next_idx = min(current_idx + 1, len(times) - 1)
            predictions_1h = {
                "temp_1h": temps[next_idx],
                "humidity_1h": humi[next_idx],
                "wind_speed_1h": winds[next_idx],
                "rain_probability": precip[next_idx],
            }

            smart_indexes = calculate_smart_indexes(
                current_temp, humidity, wind_speed, current_rain_prob
            )

            return {
                "source": "Online (Open-Meteo API)",
                "city": formatted_city_name,
                "coordinates": {"latitude": lat, "longitude": lon},
                "today_date": today_str,

                "now": {
                    "time": times[current_idx] if current_idx < len(times) else "N/A",
                    "temperature": current_temp,
                    "humidity": humidity,
                    "wind_speed": wind_speed,
                    "wind_direction": wind_direction,
                    "pressure": pressure,
                    "cloud_cover": cloud_cover,
                    "rain_probability": current_rain_prob,
                    "weather_label": weathercode_to_label(current_weathercode),
                    "sunrise": sunrise,
                    "sunset": sunset,
                },

                "predictions_1h": predictions_1h,
                "smart_indexes": smart_indexes,

                "daily_forecast": daily_forecast,
                "hourly_by_date": hourly_by_date,
            }

        except Exception:
            online = False

    # ========================================================
    # MODE HORS LIGNE — Edge AI entraînée sur données IoT réelles
    # ========================================================
    now_dt = datetime.now()
    edge_result = predict_edge(now_dt.hour)
    simulated_now = edge_result["now_simulated"]

    return {
        "source": "Offline (Edge AI - modèle entraîné sur capteurs IoT réels)",
        "city": formatted_city_name,
        "coordinates": {"latitude": lat, "longitude": lon},
        "today_date": now_dt.strftime("%Y-%m-%d"),

        "now": {
            "temperature": simulated_now["temperature"],
            "humidity": simulated_now["humidity"],
            # Le dataset IoT réel ne contient ni vent ni pression (capteurs d'intérieur) :
            # valeurs par défaut clairement documentées, pas mesurées.
            "wind_speed": 10.0,
            "wind_direction": 180,
            "pressure": 1013,
            "cloud_cover": 40,
            "rain_probability": edge_result["predictions_1h"]["rain_probability"],
            "weather_label": "cloudy",
            "sunrise": "06:00",
            "sunset": "21:00",
        },

        "predictions_1h": edge_result["predictions_1h"],
        "smart_indexes": edge_result["smart_indexes"],
        "daily_forecast": [],
        "hourly_by_date": {},
    }
