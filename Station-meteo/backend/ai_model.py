# ============================================================
# 1. IMPORTS & GESTION DES CHEMINS
# ============================================================

# Bibliothèques Python intégrées
import os
import sys

# ------------------------------------------------------------
# __file__
# -> chemin du fichier actuel
#
# Exemple :
# C:/Projet/backend/ai_model.py
#
# os.path.abspath(__file__)
# -> transforme en chemin absolu
#
# os.path.dirname(...)
# -> récupère uniquement le dossier parent
# ------------------------------------------------------------

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# ------------------------------------------------------------
# Ajout de dossiers au PYTHONPATH
#
# Pourquoi ?
#
# Python recherche les modules dans plusieurs dossiers.
# Si data_generator.py est dans un dossier "data",
# Python risque de ne pas le trouver.
#
# sys.path.append(...) ajoute donc de nouveaux dossiers
# où Python pourra chercher les modules.
# ------------------------------------------------------------

sys.path.append(
    os.path.join(CURRENT_DIR, "data")
)

sys.path.append(
    os.path.join(CURRENT_DIR, "..", "data")
)

# ============================================================
# IMPORTS DES LIBRAIRIES EXTERNES
# ============================================================

# Sauvegarde et chargement des modèles IA
import joblib

# Manipulation des tableaux de données
import pandas as pd

# Algorithme Machine Learning
from sklearn.ensemble import RandomForestRegressor

# ============================================================
# IMPORT DU DATASET
# ============================================================

# ------------------------------------------------------------
# On essaye plusieurs chemins d'import.
#
# Cas 1 :
# data_generator.py est dans le même dossier
#
# Cas 2 :
# data_generator.py est dans /data
#
# Cela évite les erreurs :
# ModuleNotFoundError
# ------------------------------------------------------------

try:

    from data_generator import dataset

except ModuleNotFoundError:

    from data.data_generator import dataset


# ============================================================
# 2. EMPLACEMENT DU MODÈLE
# ============================================================

# ------------------------------------------------------------
# Fichier dans lequel sera sauvegardé
# le modèle entraîné.
#
# Exemple :
# backend/local_model.pkl
# ------------------------------------------------------------

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

    1. Crée les données
    2. Crée l'IA
    3. Entraîne l'IA
    4. Sauvegarde l'IA
    """

    print(
        "Génération des données d'entraînement..."
    )

    # Dataset généré automatiquement
    #
    # X = entrées
    # Y = résultats attendus
    X, Y = dataset(n_samples=2000)

    print(
        "Entraînement du modèle RandomForestRegressor..."
    )

    # Création du modèle IA
    #
    # n_estimators=60
    # -> 60 arbres de décision
    #
    # random_state=42
    # -> rend l'entraînement reproductible
    model = RandomForestRegressor(
        n_estimators=60,
        random_state=42
    )

    # Phase d'apprentissage
    #
    # Le modèle observe :
    # X -> Y
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
    en conseils compréhensibles
    pour un utilisateur.
    """

    # --------------------------------------------------------
    # CONFORT THERMIQUE
    # --------------------------------------------------------
    #
    # Température idéale :
    # 22°C
    #
    # Plus la température s'éloigne de 22°C,
    # plus le score diminue.
    #
    # max(0, ...)
    # empêche une valeur négative.
    #
    # min(100, ...)
    # empêche une valeur supérieure à 100.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CONSEIL VESTIMENTAIRE
    # --------------------------------------------------------

    if temp < 8:

        clothing = "Manteau chaud et Bonnet"

    elif temp < 18:

        clothing = "Veste légère ou Pull"

    else:

        clothing = "T-shirt et Tenue légère"

    # Risque de pluie
    if rain_prob > 50:

        clothing += " + Parapluie / Imperméable"

    # --------------------------------------------------------
    # ACTIVITÉS EXTÉRIEURES
    # --------------------------------------------------------

    if rain_prob > 60 or wind_speed > 50:

        activity = (
            "Activités d'intérieur recommandées"
        )

    else:

        activity = (
            "Excellente journée pour sortir !"
        )

    # --------------------------------------------------------
    # CONSEIL D'ARROSAGE
    # --------------------------------------------------------

    if rain_prob > 40:

        watering = "Non (Pluie prévue)"

    elif humidity < 60:

        watering = "Oui (Temps sec)"

    else:

        watering = "Optionnel"

    # --------------------------------------------------------
    # RETOUR DES CONSEILS
    # --------------------------------------------------------

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
            "Fort" if wind_speed > 45 else "Faible"
    }


# ============================================================
# 5. PRÉDICTION MÉTÉO
# ============================================================

def predict_weather_advanced(
    features: dict
) -> dict:

    """
    Fonction principale du modèle IA.

    Elle :
    - charge le modèle
    - effectue une prédiction
    - calcule les conseils
    """

    # --------------------------------------------------------
    # Si le modèle n'existe pas encore,
    # on l'entraîne automatiquement.
    # --------------------------------------------------------

    if not os.path.exists(MODEL_PATH):

        train_and_save_model()

    # Chargement du modèle sauvegardé
    model = joblib.load(MODEL_PATH)

    # --------------------------------------------------------
    # Transformation du dictionnaire
    # en DataFrame Pandas.
    #
    # Scikit-Learn préfère travailler
    # avec des tableaux.
    # --------------------------------------------------------

    input_df = pd.DataFrame([features])

    # L'IA effectue une prédiction
    preds = model.predict(input_df)[0]

    # Extraction des résultats
    pred_temp = preds[0]
    pred_hum = preds[1]
    pred_wind = preds[2]
    rain_prob = preds[3]

    # Calcul des conseils intelligents
    smart_indexes = calculate_smart_indexes(
        features["temp"],
        features["humidity"],
        features["wind_speed"],
        rain_prob
    )

    # Structure finale renvoyée
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
    Fonction simplifiée appelée
    lorsque l'application n'a plus Internet.
    """

    # --------------------------------------------------------
    # Création de données météo fictives.
    #
    # ATTENTION :
    # lat et lon ne sont actuellement
    # pas utilisées.
    # --------------------------------------------------------

    sample_features = {

        "temp": 18.0,

        "humidity": 55.0,

        "wind_speed": 10.0
    }

    # Appel de l'IA
    res = predict_weather_advanced(
        sample_features
    )

    # Retourne seulement
    # la température prévue.
    return res["predictions_1h"]["temp_1h"]


# ============================================================
# 7. POINT D'ENTRÉE
# ============================================================

# Ce bloc s'exécute uniquement si :
#
# python ai_model.py
#
# est lancé directement.

if __name__ == "__main__":

    train_and_save_model()