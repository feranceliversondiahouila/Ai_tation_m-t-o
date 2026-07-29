# ============================================================
# IMPORTS
# ============================================================

# FastAPI permet de créer une API REST en Python
from fastapi import FastAPI, Query

# Middleware permettant d'autoriser des applications externes
# (HTML, JavaScript, React, Streamlit...) à appeler l'API
from fastapi.middleware.cors import CORSMiddleware

# Permet d'effectuer des requêtes HTTP vers Open-Meteo
import requests

# Permet de manipuler les dates et heures
from datetime import datetime

# Permet de rendre certains paramètres facultatifs
from typing import Optional

# Fonction qui vérifie si Internet est disponible
from network_checker import is_network_available

# Fonction IA locale utilisée lorsque le réseau est coupé
from ai_model import predict_temperature_local


# ============================================================
# CRÉATION DE L'APPLICATION FASTAPI
# ============================================================

app = FastAPI(
    title="Station Météo IA - Backend API",
    version="2.5"
)


# ============================================================
# CONFIGURATION CORS
# ============================================================

# Sans cette configuration :
# Un navigateur peut bloquer les appels venant
# d'une autre application (HTML, JS, React, etc.)

app.add_middleware(
    CORSMiddleware,

    # Autorise tous les domaines
    # (pratique pour le développement)
    allow_origins=["*"],

    # Autorise l'envoi d'informations d'authentification
    allow_credentials=True,

    # Autorise toutes les méthodes HTTP
    # GET, POST, PUT, DELETE...
    allow_methods=["*"],

    # Autorise tous les en-têtes HTTP
    allow_headers=["*"],
)


# ============================================================
# BASE DE DONNÉES LOCALE
# ============================================================

# Petit dictionnaire contenant des villes connues.
# Cela évite d'appeler une API externe à chaque fois.

CITIES_COORDS = {

    "bethune": {
        "name": "Béthune",
        "lat": 50.53,
        "lon": 2.64
    },

    "lille": {
        "name": "Lille",
        "lat": 50.63,
        "lon": 3.06
    },

    "paris": {
        "name": "Paris",
        "lat": 48.85,
        "lon": 2.35
    },

    "pointe-noire": {
        "name": "Pointe-Noire",
        "lat": -4.78,
        "lon": 11.86
    }
}


# ============================================================
# CONVERSION D'UNE VILLE EN COORDONNÉES GPS
# ============================================================

def get_coordinates_from_city(city_name: str):

    """
    Reçoit un nom de ville.

    Exemple :
        Paris

    Retour :
        latitude
        longitude
        nom officiel
    """

    # Nettoyage :
    # " PARIS " devient "paris"
    city_clean = city_name.strip().lower()

    # Recherche dans la base locale
    if city_clean in CITIES_COORDS:

        return (
            CITIES_COORDS[city_clean]["lat"],
            CITIES_COORDS[city_clean]["lon"],
            CITIES_COORDS[city_clean]["name"]
        )

    # Si la ville n'existe pas,
    # on tente une recherche Open-Meteo
    try:

        # ATTENTION :
        # Dans ton code original, cette URL contient
        # des balises HTML <a>.
        # Il faut uniquement conserver l'URL.

        geo_url = (
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city_name}"
            f"&count=1"
            f"&language=fr"
            f"&format=json"
        )

        # Appel de l'API
        res = requests.get(
            geo_url,
            timeout=2.0
        ).json()

        # Vérifie qu'un résultat existe
        if "results" in res and len(res["results"]) > 0:

            item = res["results"][0]

            return (
                item["latitude"],
                item["longitude"],
                item["name"]
            )

    except Exception:

        # On ignore les erreurs réseau
        pass

    # Si rien n'est trouvé :
    # coordonnées par défaut = Béthune
    return (
        50.53,
        2.64,
        city_name.capitalize()
    )


# ============================================================
# ROUTE PRINCIPALE
# ============================================================

@app.get("/weather")

def get_weather(

    # Exemple :
    # /weather?city=Paris
    city: str = Query(
        "Pointe-Noire",
        description="Nom de la ville"
    ),

    # Coordonnées facultatives
    lat: Optional[float] = None,
    lon: Optional[float] = None
):

    # ========================================================
    # CONVERSION VILLE -> GPS
    # ========================================================

    # Si aucune coordonnée n'est fournie
    if lat is None or lon is None:

        # Recherche automatique
        lat, lon, formatted_city_name = (
            get_coordinates_from_city(city)
        )

    else:

        formatted_city_name = city

    # ========================================================
    # TEST DE LA CONNEXION INTERNET
    # ========================================================

    online = is_network_available()

    # ========================================================
    # MODE CONNECTÉ
    # ========================================================

    if online:

        try:

            # Construction de l'URL Open-Meteo

            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&past_days=2"
                f"&forecast_days=2"
                f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
                f"&hourly=temperature_2m,relative_humidity_2m,precipitation_probability"
                f"&daily=sunrise,sunset"
                f"&timezone=auto"
            )

            # Requête HTTP
            data = requests.get(
                url,
                timeout=3.0
            ).json()

            # ====================================================
            # MÉTÉO ACTUELLE
            # ====================================================

            current_temp = data["current"]["temperature_2m"]

            humidity = data["current"]["relative_humidity_2m"]

            wind_speed = data["current"]["wind_speed_10m"]

            # ====================================================
            # LEVER ET COUCHER DU SOLEIL
            # ====================================================

            sunrise_raw = (
                data["daily"]["sunrise"][2]
                if "daily" in data
                and len(data["daily"]["sunrise"]) > 2
                else "N/A"
            )

            sunset_raw = (
                data["daily"]["sunset"][2]
                if "daily" in data
                and len(data["daily"]["sunset"]) > 2
                else "N/A"
            )

            # Extraction de l'heure uniquement
            sunrise = (
                sunrise_raw.split("T")[1]
                if "T" in sunrise_raw
                else sunrise_raw
            )

            sunset = (
                sunset_raw.split("T")[1]
                if "T" in sunset_raw
                else sunset_raw
            )

            # ====================================================
            # DONNÉES HORAIRES
            # ====================================================

            times = data["hourly"]["time"]

            temps = data["hourly"]["temperature_2m"]

            humi = data["hourly"]["relative_humidity_2m"]

            precip = data["hourly"].get(
                "precipitation_probability",
                [0] * len(times)
            )

            # ====================================================
            # RECHERCHE DE L'HEURE ACTUELLE
            # ====================================================

            now_str = datetime.now().strftime(
                "%Y-%m-%dT%H:00"
            )

            if now_str in times:
                current_idx = times.index(now_str)
            else:
                current_idx = 48

            # ====================================================
            # HISTORIQUE DES 48 DERNIÈRES HEURES
            # ====================================================

            past_48h = [

                {
                    "time": times[i],
                    "temp_c": temps[i],
                    "humidity": humi[i]
                }

                for i in range(
                    max(0, current_idx - 48),
                    current_idx
                )
            ]

            # ====================================================
            # PRÉVISIONS DES 24 PROCHAINES HEURES
            # ====================================================

            future_24h = [

                {
                    "time": times[i],
                    "temp_c": temps[i],
                    "humidity": humi[i],
                    "rain_prob": precip[i]
                }

                for i in range(
                    current_idx + 1,
                    min(len(times), current_idx + 25)
                )
            ]

            # ====================================================
            # CONSTRUCTION DE LA RÉPONSE JSON
            # ====================================================

            return {

                "source": "Online (Open-Meteo API)",

                "city": formatted_city_name,

                "coordinates": {
                    "latitude": lat,
                    "longitude": lon
                },

                "now": {

                    # Heure actuelle
                    "time": (
                        times[current_idx]
                        if current_idx < len(times)
                        else "N/A"
                    ),

                    "temperature": current_temp,

                    "humidity": humidity,

                    "wind_speed": wind_speed,

                    "sunrise": sunrise,

                    "sunset": sunset
                },

                "timeline_hourly": {

                    # Historique 48h
                    "history_past_48h": past_48h,

                    # Situation actuelle
                    "current_hour": {

                        "time": (
                            times[current_idx]
                            if current_idx < len(times)
                            else "N/A"
                        ),

                        "temp_c": current_temp
                    },

                    # Prévision 24h
                    "forecast_next_24h": future_24h
                }
            }

        except Exception:

            # Si Open-Meteo tombe en panne,
            # on bascule automatiquement
            # en mode IA locale
            online = False

    # ========================================================
    # MODE HORS LIGNE (EDGE AI)
    # ========================================================

    current_temp = round(
        predict_temperature_local(lat, lon),
        1
    )

    return {

        "source": "Offline (Edge AI Local)",

        "city": formatted_city_name,

        "coordinates": {
            "latitude": lat,
            "longitude": lon
        },

        "now": {

            "temperature": current_temp,

            # Valeurs estimées
            "humidity": 60,

            "wind_speed": 12.0,

            # Valeurs de secours
            "sunrise": "06:00",

            "sunset": "21:00"
        }
    }