# ============================================================
# 1. IMPORTS & GESTION PROPRE DES CHEMINS
# ============================================================

import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)
sys.path.append(os.path.join(CURRENT_DIR, "data"))
sys.path.append(os.path.join(ROOT_DIR, "data"))

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

try:
    from data.data_generator import dataset_from_real_iot
except ModuleNotFoundError:
    from data_generator import dataset_from_real_iot


# ============================================================
# 2. EMPLACEMENT DU MODÈLE ET DU PROFIL HORAIRE
# ============================================================
#
# Le modèle Edge AI est entraîné sur les VRAIES données de
# capteurs IoT (data/iot_telemetry_data.csv.xls), et non plus
# sur des données simulées.
#
# Comme le projet ne dispose pas de capteur physique, le
# "hourly_profile" sert à simuler une lecture plausible pour
# l'heure actuelle quand on est hors-ligne.

MODEL_PATH = os.path.join(CURRENT_DIR, "edge_model.pkl")
PROFILE_PATH = os.path.join(CURRENT_DIR, "hourly_profile.json")


# ============================================================
# 3. ENTRAÎNEMENT DU MODÈLE SUR DONNÉES RÉELLES
# ============================================================

def train_and_save_model():
    """
    1. Charge et prépare les données réelles des capteurs IoT.
    2. Entraîne un RandomForestRegressor multi-sortie
       (température future + humidité future).
    3. Sauvegarde le modèle ET le profil horaire moyen,
       nécessaire pour simuler une lecture capteur hors-ligne.
    """

    print("Chargement et préparation des données réelles (IoT)...")
    X, Y, hourly_profile = dataset_from_real_iot()

    print(f"Entraînement sur {len(X)} échantillons réels...")
    model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(X, Y)

    joblib.dump(model, MODEL_PATH)

    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(hourly_profile, f, ensure_ascii=False, indent=2)

    print(f"Modèle Edge AI entraîné et sauvegardé sous : {MODEL_PATH}")
    print(f"Profil horaire sauvegardé sous : {PROFILE_PATH}")


# ============================================================
# 4. CALCUL DES INDICATEURS MÉTÉO (inchangé)
# ============================================================

def calculate_smart_indexes(
    temp: float,
    humidity: float,
    wind_speed: float,
    rain_prob: float
) -> dict:
    """Transforme des données météo en conseils lisibles par un utilisateur."""

    thermal_comfort = max(
        0,
        min(100, int(100 - abs(temp - 22) * 3 - (humidity - 50) * 0.2))
    )

    if temp < 8:
        clothing = "Manteau chaud et Bonnet"
    elif temp < 18:
        clothing = "Veste légère ou Pull"
    else:
        clothing = "T-shirt et Tenue légère"

    if rain_prob > 50:
        clothing += " + Parapluie / Imperméable"

    if rain_prob > 60 or wind_speed > 50:
        activity = "Activités d'intérieur recommandées"
    else:
        activity = "Excellente journée pour sortir !"

    if rain_prob > 40:
        watering = "Non (Pluie prévue)"
    elif humidity < 60:
        watering = "Oui (Temps sec)"
    else:
        watering = "Optionnel"

    return {
        "thermal_comfort_score": f"{thermal_comfort}%",
        "clothing_advice": clothing,
        "outdoor_activity": activity,
        "plant_watering_needed": watering,
        "wind_risk": "Fort" if wind_speed > 45 else "Faible",
    }


# ============================================================
# 5. PRÉDICTION EDGE AI (mode hors-ligne, sans capteur physique)
# ============================================================
#
# Le dataset réel ne contient ni vent, ni pression : ces deux
# valeurs restent donc estimées de façon simple en hors-ligne,
# ce qui est clairement indiqué dans la réponse de l'API.

def predict_edge(hour: int) -> dict:
    """
    Simule une lecture capteur pour l'heure donnée (à partir du
    profil horaire moyen appris sur les vraies données), puis
    utilise le modèle Edge AI pour prédire température et
    humidité 30 minutes plus tard.
    """

    if not os.path.exists(MODEL_PATH) or not os.path.exists(PROFILE_PATH):
        train_and_save_model()

    model = joblib.load(MODEL_PATH)

    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        hourly_profile = json.load(f)

    # Le JSON stocke les heures sous forme de texte ("0", "1"...)
    profile = hourly_profile.get(
        str(hour),
        # Si l'heure exacte manque, on prend la moyenne globale
        {"temp": 20.0, "humidity": 55.0, "co": 0.004, "lpg": 0.006, "smoke": 0.017}
    )

    current_temp = round(profile["temp"], 1)
    current_humidity = round(profile["humidity"], 1)

    input_df = pd.DataFrame([{
        "temp": profile["temp"],
        "humidity": profile["humidity"],
        "co": profile["co"],
        "lpg": profile["lpg"],
        "smoke": profile["smoke"],
        "hour": hour,
    }])

    pred_temp, pred_hum = model.predict(input_df)[0]

    # Le vent n'existe pas dans ce dataset (capteurs d'intérieur) :
    # valeur estimée par défaut, clairement documentée.
    estimated_wind = 10.0

    # La pluie non plus : approximation simple à partir de l'humidité prédite.
    estimated_rain_prob = min(95, max(0, round((pred_hum - 50) * 1.8, 1)))

    smart_indexes = calculate_smart_indexes(
        current_temp, current_humidity, estimated_wind, estimated_rain_prob
    )

    return {
        "now_simulated": {
            "temperature": current_temp,
            "humidity": current_humidity,
        },
        "predictions_1h": {
            "temp_1h": round(float(pred_temp), 1),
            "humidity_1h": round(float(pred_hum), 1),
            "wind_speed_1h": estimated_wind,
            "rain_probability": estimated_rain_prob,
        },
        "smart_indexes": smart_indexes,
    }


# ============================================================
# 6. POINT D'ENTRÉE DU PROGRAMME
# ============================================================

if __name__ == "__main__":
    train_and_save_model()