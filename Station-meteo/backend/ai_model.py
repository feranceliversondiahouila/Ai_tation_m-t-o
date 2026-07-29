# ============================================================
# 1. IMPORTS & GESTION PROPRE DES CHEMINS
# ============================================================

# os :
# permet de manipuler les fichiers et dossiers
import os

# sys :
# permet de modifier les chemins utilisés par Python
# pour rechercher les modules à importer
import sys


# ============================================================
# IDENTIFICATION DES DOSSIERS DU PROJET
# ============================================================

# __file__
# contient le chemin du fichier actuel
#
# Exemple :
# C:/Station-meteo/backend/ai_model.py
#
# dirname() récupère uniquement le dossier

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# Remonte d'un niveau :
#
# backend
#   ↑
# Station-meteo
#
# ROOT_DIR correspond à la racine du projet

ROOT_DIR = os.path.dirname(
    CURRENT_DIR
)


# ============================================================
# AJOUT DES DOSSIERS AU PYTHONPATH
# ============================================================

# Cela permet à Python de retrouver
# correctement les modules du projet.

if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# Ajout préventif du dossier data

sys.path.append(
    os.path.join(CURRENT_DIR, "data")
)

sys.path.append(
    os.path.join(ROOT_DIR, "data")
)


# ============================================================
# IMPORTS DES LIBRAIRIES EXTERNES
# ============================================================

# Sauvegarde et chargement du modèle IA
import joblib

# Manipulation de tableaux de données
import pandas as pd

# Algorithme Machine Learning
from sklearn.ensemble import RandomForestRegressor


# ============================================================
# IMPORT DU DATASET
# ============================================================

# Le try/except permet de gérer plusieurs
# organisations possibles du projet.

try:

    from data.data_generator import dataset

except ModuleNotFoundError:

    from data_generator import dataset


# ============================================================
# 2. EMPLACEMENT DU MODÈLE IA
# ============================================================

# Localisation du modèle entraîné
#
# Exemple :
# backend/local_model.pkl

MODEL_PATH = os.path.join(
    CURRENT_DIR,
    "local_model.pkl"
)


# ============================================================
# 3. ENTRAÎNEMENT DU MODÈLE
# ============================================================

def train_and_save_model():
    """
    Cette fonction :

    1. Génère les données d'entraînement
    2. Crée un modèle RandomForest
    3. Entraîne le modèle
    4. Sauvegarde le modèle sur le disque
    """

    print(
        "Génération des données d'entraînement..."
    )

    # Création du dataset
    #
    # X = variables d'entrée
    # Y = valeurs à prédire
    X, Y = dataset(
        n_samples=2000
    )

    print(
        "Entraînement du modèle RandomForestRegressor..."
    )

    # Création du modèle IA
    #
    # n_estimators = nombre d'arbres
    # random_state = résultat reproductible
    model = RandomForestRegressor(
        n_estimators=60,
        random_state=42
    )

    # Apprentissage
    model.fit(X, Y)

    # Sauvegarde du modèle
    joblib.dump(
        model,
        MODEL_PATH
    )

    print(
        f"Modèle IA entraîné et sauvegardé avec succès sous : {MODEL_PATH}"
    )


# ============================================================
# 4. CALCUL DES INDICATEURS MÉTÉO
# ============================================================

def calculate_smart_indexes(
    temp: float,
    humidity: float,
    wind_speed: float,
    rain_prob: float
) -> dict:
    """
    Transforme des données météo
    en conseils lisibles par un utilisateur.
    """

    # ========================================================
    # SCORE DE CONFORT THERMIQUE
    # ========================================================
    #
    # Température idéale : 22°C
    #
    # Plus on s'en éloigne,
    # plus le score diminue.
    #
    # Le score est toujours maintenu
    # entre 0 et 100.

    thermal_comfort = max(
        0,
        min(
            100,
            int(
                100
                - abs(temp - 22) * 3
                - (humidity - 50) * 0.2
            )
        )
    )

    # ========================================================
    # CONSEIL VESTIMENTAIRE
    # ========================================================

    if temp < 8:

        clothing = (
            "Manteau chaud et Bonnet"
        )

    elif temp < 18:

        clothing = (
            "Veste légère ou Pull"
        )

    else:

        clothing = (
            "T-shirt et Tenue légère"
        )

    # Ajouter un parapluie si risque important
    if rain_prob > 50:

        clothing += (
            " + Parapluie / Imperméable"
        )

    # ========================================================
    # ACTIVITÉS EXTÉRIEURES
    # ========================================================

    if rain_prob > 60 or wind_speed > 50:

        activity = (
            "Activités d'intérieur recommandées"
        )

    else:

        activity = (
            "Excellente journée pour sortir !"
        )

    # ========================================================
    # CONSEIL D'ARROSAGE
    # ========================================================

    if rain_prob > 40:

        watering = (
            "Non (Pluie prévue)"
        )

    elif humidity < 60:

        watering = (
            "Oui (Temps sec)"
        )

    else:

        watering = (
            "Optionnel"
        )

    # ========================================================
    # RETOUR DES CONSEILS
    # ========================================================

    return {

        "thermal_comfort_score":
            f"{thermal_comfort}%",

        "clothing_advice":
            clothing,

        "outdoor_activity":
            activity,

        "plant_watering_needed":
            watering,

        "wind_risk":
            "Fort"
            if wind_speed > 45
            else "Faible"
    }


# ============================================================
# 5. PRÉDICTION MÉTÉO
# ============================================================

def predict_weather_advanced(
    features: dict
) -> dict:
    """
    Fonction principale de prédiction.

    Elle :

    1. Vérifie si le modèle existe
    2. Charge le modèle
    3. Effectue une prédiction
    4. Génère des conseils météo
    """

    # Si le modèle n'existe pas
    # l'entraîner automatiquement
    if not os.path.exists(
        MODEL_PATH
    ):
        train_and_save_model()

    # Chargement du modèle
    model = joblib.load(
        MODEL_PATH
    )

    # Conversion du dictionnaire
    # en DataFrame Pandas
    input_df = pd.DataFrame(
        [features]
    )

    # Prédiction
    preds = model.predict(
        input_df
    )[0]

    # Extraction des résultats
    pred_temp = preds[0]
    pred_hum = preds[1]
    pred_wind = preds[2]
    rain_prob = preds[3]

    # Calcul des conseils logiciels
    smart_indexes = calculate_smart_indexes(
        features["temp"],
        features["humidity"],
        features["wind_speed"],
        rain_prob
    )

    # Réponse structurée
    return {

        "predictions_1h": {

            "temp_1h":
                round(float(pred_temp), 1),

            "humidity_1h":
                round(float(pred_hum), 1),

            "wind_speed_1h":
                round(float(pred_wind), 1),

            "rain_probability":
                round(float(rain_prob), 1)
        },

        "smart_indexes":
            smart_indexes
    }


# ============================================================
# 6. MODE HORS LIGNE
# ============================================================

def predict_temperature_local(
    lat: float,
    lon: float
) -> float:
    """
    Fonction de secours appelée
    lorsque l'application n'a plus Internet.
    """

    # Données simulées
    #
    # Ces valeurs servent d'entrée
    # au modèle IA local.
    sample_features = {

        "temp": 18.0,

        "humidity": 55.0,

        "wind_speed": 10.0
    }

    # Appel du moteur IA principal
    res = predict_weather_advanced(
        sample_features
    )

    # Retourne uniquement
    # la température prévue dans 1 heure
    return res["predictions_1h"][
        "temp_1h"
    ]


# ============================================================
# 7. POINT D'ENTRÉE DU PROGRAMME
# ============================================================

# Ce bloc s'exécute uniquement si
# le fichier est lancé directement.
#
# Exemple :
#
# python ai_model.py

if __name__ == "__main__":

    # Lance l'entraînement du modèle
    train_and_save_model()