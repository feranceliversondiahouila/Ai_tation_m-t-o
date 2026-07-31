# ============================================================
# IMPORTS
# ============================================================

import os

# Pandas : création de tableaux de données (DataFrame)
import pandas as pd


# ============================================================
# JEU DE DONNÉES RÉEL (capteurs IoT) — utilisé par l'IA "Edge"
# ============================================================
#
# Source : dataset Kaggle "Environmental Sensor Telemetry Data"
# 3 capteurs, ~405 000 relevés bruts sur 8 jours (juillet 2020).
#
# Ce module entraîne le modèle sur de VRAIES mesures de capteurs
# (et non des données simulées), ce qui rend les prédictions du
# mode hors-ligne plus crédibles.
#
# Limite honnête : ce sont des capteurs d'intérieur. Il n'y a
# pas de vent, de pression ou de position GPS dans ces données.
# On prédit donc uniquement température et humidité à court terme.

REAL_CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "iot_telemetry_data.csv.xls"
)


def dataset_from_real_iot(
    csv_path: str = REAL_CSV_PATH,
    horizon_steps: int = 6,
    resample_freq: str = "5min",
):
    """
    Construit un jeu d'entraînement supervisé à partir des
    relevés réels des capteurs IoT.

    Étapes :
    1. Lecture du CSV et conversion du timestamp Unix en date.
    2. Rééchantillonnage à `resample_freq` (5 min par défaut)
       par capteur, pour lisser le bruit des mesures très
       fréquentes et travailler sur un pas de temps réaliste.
    3. Construction de la cible : température et humidité
       `horizon_steps` pas de temps plus tard
       (6 x 5 min = 30 minutes dans le futur par défaut).

    Retour :
        X = variables d'entrée (temp, humidity, co, lpg, smoke, hour)
        Y = valeurs à prédire (temp_future, humidity_future)
        hourly_profile = moyenne des mesures par heure de la
            journée, utilisée pour simuler une "lecture capteur
            actuelle" en mode hors-ligne (pas de capteur physique
            disponible dans ce projet).
    """

    raw = pd.read_csv(csv_path)
    raw["ts"] = pd.to_datetime(raw["ts"], unit="s")

    frames = []
    for _device, g in raw.groupby("device"):
        g = g.set_index("ts").sort_index()

        r = (
            g[["temp", "humidity", "co", "lpg", "smoke"]]
            .resample(resample_freq)
            .mean()
            .dropna()
        )

        r["hour"] = r.index.hour
        r["temp_future"] = r["temp"].shift(-horizon_steps)
        r["humidity_future"] = r["humidity"].shift(-horizon_steps)

        frames.append(r.dropna())

    data = pd.concat(frames)

    features = ["temp", "humidity", "co", "lpg", "smoke", "hour"]
    X = data[features]
    Y = data[["temp_future", "humidity_future"]]

    # Profil horaire moyen : sert à simuler une lecture capteur
    # "actuelle" plausible quand on est hors-ligne et qu'on n'a
    # pas de vrai capteur branché.
    hourly_profile = (
        data.groupby("hour")[["temp", "humidity", "co", "lpg", "smoke"]]
        .mean()
        .round(4)
        .to_dict(orient="index")
    )

    return X, Y, hourly_profile
