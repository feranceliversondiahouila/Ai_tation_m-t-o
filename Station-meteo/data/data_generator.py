# ============================================================
# IMPORTS
# ============================================================

# NumPy : génération de nombres aléatoires et calculs mathématiques
import numpy as np

# Pandas : création de tableaux de données (DataFrame)
import pandas as pd


# ============================================================
# FONCTION DE GÉNÉRATION DU JEU DE DONNÉES
# ============================================================

def dataset(n_samples: int = 2000) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Génère un dataset météo artificiel.

    Paramètre :
        n_samples = nombre de lignes à générer

    Retour :
        X = données d'entrée (features)
        Y = données à prédire (targets)
    """

    # Fixe la graine aléatoire.
    # Cela permet d'obtenir toujours les mêmes données
    # à chaque exécution du programme.
    np.random.seed(42)

    # ========================================================
    # 1. CRÉATION DES DONNÉES D'ENTRÉE (X)
    # ========================================================

    # Génère des températures aléatoires comprises
    # entre -5°C et +38°C
    temp = np.random.uniform(-5, 38, n_samples)

    # Humidité comprise entre 20% et 100%
    humidity = np.random.uniform(20, 100, n_samples)

    # Pression atmosphérique comprise entre 980 et 1035 hPa
    pressure = np.random.uniform(980, 1035, n_samples)

    # Vitesse du vent comprise entre 0 et 80 km/h
    wind_speed = np.random.uniform(0, 80, n_samples)

    # Taux de nuages compris entre 0% et 100%
    cloud_cover = np.random.uniform(0, 100, n_samples)

    # Heure de la journée
    # entre 0h et 23h
    hour = np.random.randint(0, 24, n_samples)

    # Mois de l'année
    # entre 1 et 12
    month = np.random.randint(1, 13, n_samples)

    # Latitude géographique
    latitude = np.random.uniform(-90, 90, n_samples)

    # Longitude géographique
    longitude = np.random.uniform(-180, 180, n_samples)

    # ========================================================
    # 2. CRÉATION DES DONNÉES À PRÉDIRE (Y)
    # ========================================================

    # La température dans 1 heure.
    #
    # Si on est entre 6h et 14h :
    # +1.2°C
    #
    # Sinon :
    # -0.8°C
    target_temp_1h = temp + np.where(
        (hour >= 6) & (hour <= 14),
        1.2,
        -0.8
    )

    # Variation légère de l'humidité
    #
    # np.clip évite que les valeurs
    # dépassent la plage autorisée.
    target_humidity_1h = np.clip(
        humidity + np.random.uniform(-5, 5, n_samples),
        0,
        100
    )

    # Variation légère du vent
    target_wind_1h = np.clip(
        wind_speed + np.random.uniform(-3, 3, n_samples),
        0,
        120
    )

    # ========================================================
    # CALCUL DE LA PROBABILITÉ DE PLUIE
    # ========================================================

    # Règle simplifiée :
    #
    # Pression basse
    # +
    # Humidité élevée
    # +
    # Beaucoup de nuages
    #
    # => Forte probabilité de pluie
    rain_prob = np.where(

        # Condition météo pluvieuse
        (pressure < 1005)
        & (humidity > 75)
        & (cloud_cover > 60),

        # Cas pluie probable
        np.random.uniform(65, 95, n_samples),

        # Cas pluie peu probable
        np.random.uniform(0, 30, n_samples)
    )

    # ========================================================
    # CRÉATION DU DATAFRAME X
    # ========================================================

    # Toutes les variables d'entrée
    X = pd.DataFrame({

        'temperature': temp,

        'humidite': humidity,

        'pression': pressure,

        'vitesse_vent': wind_speed,

        'couverture_nuageuse': cloud_cover,

        'heure': hour,

        'mois': month,

        'latitude': latitude,

        'longitude': longitude
    })

    # ========================================================
    # CRÉATION DU DATAFRAME Y
    # ========================================================

    # Toutes les valeurs que l'IA devra apprendre
    Y = pd.DataFrame({

        'temperature_predite_1h': target_temp_1h,

        'humidite_predite_1h': target_humidity_1h,

        'vitesse_vent_predite_1h': target_wind_1h,

        'probabilite_de_pluie': rain_prob
    })

    # Retour des deux datasets
    return X, Y


# ============================================================
# TEST DU FICHIER
# ============================================================

# Ce bloc s'exécute uniquement si on lance directement :
#
# python data_generator.py
#
# Il ne s'exécutera pas si le fichier est importé
# depuis un autre script.
if __name__ == "__main__":

    # Génération de seulement 5 lignes
    X_test, Y_test = dataset(5)

    # Affichage des entrées
    print("Aperçu des entrées (X) :")
    print(X_test)

    # Affichage des sorties attendues
    print("\nAperçu des cibles à prédire (Y) :")
    print(Y_test)

# ============================================================
# JEU DE DONNÉES RÉEL (capteurs IoT) — utilisé par l'IA "Edge"
# ============================================================
#
# Source : dataset Kaggle "Environmental Sensor Telemetry Data"
# 3 capteurs, ~405 000 relevés bruts sur 8 jours (juillet 2020).
#
# Contrairement à dataset() ci-dessus (données 100% simulées),
# cette fonction entraîne sur de VRAIES mesures de capteurs.
#
# Limite honnête : ce sont des capteurs d'intérieur. Il n'y a
# pas de vent, de pression ou de position GPS dans ces données.
# On prédit donc uniquement température et humidité à court terme.

import os

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
