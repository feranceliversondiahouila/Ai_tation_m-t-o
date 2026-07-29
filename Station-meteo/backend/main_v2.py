# ============================================================
# IMPORTS
# ============================================================

# Framework permettant de créer une API Web REST
from fastapi import FastAPI, Query

# Permet d'envoyer des requêtes HTTP vers une API externe
import requests

# Permet de créer des paramètres facultatifs
from typing import Optional

# Vérifie si Internet est disponible
from network_checker import is_network_available

# Fonction IA utilisée lorsque la connexion Internet est absente
from ai_model import predict_temperature_local


# ============================================================
# CRÉATION DE L'APPLICATION FASTAPI
# ============================================================

# Création de l'objet principal de l'API
app = FastAPI(
    title="Station Météo IA - Backend API",
    version="2.0"
)


# ============================================================
# BASE DE DONNÉES LOCALE DES VILLES
# ============================================================

# Dictionnaire contenant quelques villes connues
# avec leurs coordonnées GPS.
#
# Cela permet de trouver immédiatement les coordonnées
# sans utiliser Internet.
CITIES_COORDS = {
    "bethune": {"name": "Béthune", "lat": 50.53, "lon": 2.64},
    "lille": {"name": "Lille", "lat": 50.63, "lon": 3.06},
    "paris": {"name": "Paris", "lat": 48.85, "lon": 2.35},
    "lyon": {"name": "Lyon", "lat": 45.76, "lon": 4.83},
    "marseille": {"name": "Marseille", "lat": 43.30, "lon": 5.37},
    "toulouse": {"name": "Toulouse", "lat": 43.60, "lon": 1.44}
}


# ============================================================
# CONVERTIR UNE VILLE EN COORDONNÉES GPS
# ============================================================

def get_coordinates_from_city(city_name: str):

    """
    Transforme un nom de ville en :

    - latitude
    - longitude
    - nom formaté

    Exemple :

    Entrée :
        "Paris"

    Sortie :
        48.85, 2.35, "Paris"
    """

    # Supprime les espaces inutiles et transforme en minuscules
    city_clean = city_name.strip().lower()

    # Vérifie si la ville existe dans la base locale
    if city_clean in CITIES_COORDS:

        return (
            CITIES_COORDS[city_clean]["lat"],
            CITIES_COORDS[city_clean]["lon"],
            CITIES_COORDS[city_clean]["name"]
        )

    # ========================================================
    # SI LA VILLE N'EST PAS ENREGISTRÉE LOCALEMENT
    # ========================================================

    try:

        # URL du service de géocodage Open-Meteo
        #
        # Cette API permet de trouver les coordonnées GPS
        # à partir d'un nom de ville.
        geo_url = (
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city_name}"
            f"&count=1"
            f"&language=fr"
            f"&format=json"
        )

        # Envoi de la requête
        res = requests.get(
            geo_url,
            timeout=2.0
        ).json()

        # Vérifie qu'un résultat a été trouvé
        if "results" in res and len(res["results"]) > 0:

            item = res["results"][0]

            return (
                item["latitude"],
                item["longitude"],
                item["name"]
            )

    except Exception:

        # Ignore discrètement les erreurs
        pass

    # ========================================================
    # VALEUR PAR DÉFAUT SI RIEN N'EST TROUVÉ
    # ========================================================

    return (
        50.53,
        2.64,
        city_name.capitalize()
    )


# ============================================================
# ROUTE D'ACCUEIL
# ============================================================

@app.get("/")
def read_root():

    """
    Route accessible avec :

    GET /
    """

    return {
        "message": "API Station Météo IA"
    }


# ============================================================
# ROUTE MÉTÉO
# ============================================================

@app.get("/weather")

def get_weather(

    # Ville demandée par l'utilisateur
    city: str = Query(
        "Béthune",
        description="Nom de la ville recherchée"
    ),

    # Coordonnées facultatives
    lat: Optional[float] = None,
    lon: Optional[float] = None
):

    """
    Route principale.

    Fonctionnement :

    1. Obtient les coordonnées.
    2. Vérifie Internet.
    3. Utilise Open-Meteo si possible.
    4. Sinon utilise l'IA locale.
    """

    # ========================================================
    # RECHERCHE DES COORDONNÉES
    # ========================================================

    # Si l'utilisateur n'a pas fourni de coordonnées GPS
    if lat is None or lon is None:

        # Recherche automatique à partir du nom de ville
        lat, lon, formatted_city_name = (
            get_coordinates_from_city(city)
        )

    else:

        formatted_city_name = city

    # ========================================================
    # VÉRIFICATION DE L'ÉTAT RÉSEAU
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
                f"?latitude={lat}"
                f"&longitude={lon}"
                f"&past_days=2"
                f"&forecast_days=2"
                f"&current=temperature_2m,"
                f"relative_humidity_2m,"
                f"wind_speed_10m"
                f"&hourly=temperature_2m"
            )

            # Appel de l'API météo
            data = requests.get(
                url,
                timeout=3.0
            ).json()

            # ====================================================
            # EXTRACTION DES DONNÉES ACTUELLES
            # ====================================================

            current_temp = data["current"]["temperature_2m"]

            humidity = data["current"]["relative_humidity_2m"]

            wind_speed = data["current"]["wind_speed_10m"]

            # ====================================================
            # TEMPÉRATURES HORAIRES
            # ====================================================

            hourly_temps = data["hourly"]["temperature_2m"]

            # Moyenne de température du jour J-2
            temp_j_minus_2 = round(
                sum(hourly_temps[0:24]) / 24,
                1
            )

            # Moyenne de température du jour J-1
            temp_j_minus_1 = round(
                sum(hourly_temps[24:48]) / 24,
                1
            )

            # Moyenne de température du jour J+1
            temp_j_plus_1 = round(
                sum(hourly_temps[72:96]) / 24,
                1
            )

            # ====================================================
            # RÉPONSE JSON
            # ====================================================

            return {

                "source": "Online (Open-Meteo API)",

                "city": formatted_city_name,

                "current": {

                    "temperature": current_temp,

                    "humidity": humidity,

                    "wind_speed": wind_speed
                },

                "timeline": {

                    "J-2": temp_j_minus_2,

                    "J-1": temp_j_minus_1,

                    "Aujourd'hui": current_temp,

                    "J+1 (Prédiction)": temp_j_plus_1
                }
            }

        except Exception:

            # Si Open-Meteo ne répond pas,
            # passage automatique en mode Offline
            online = False

    # ========================================================
    # MODE HORS LIGNE (EDGE AI)
    # ========================================================

    # Utilisation du modèle IA local
    current_temp = round(
        predict_temperature_local(lat, lon),
        1
    )

    return {

        "source": "Offline (Edge AI Local)",

        "city": formatted_city_name,

        "current": {

            "temperature": current_temp,

            # Valeurs estimées
            "humidity": 60,

            "wind_speed": 12.0
        },

        "timeline": {

            "J-2": round(
                current_temp - 1.5,
                1
            ),

            "J-1": round(
                current_temp - 0.8,
                1
            ),

            "Aujourd'hui": current_temp,

            "J+1 (Prédiction IA)": round(
                current_temp + 1.2,
                1
            )
        }
    }