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

        'temp': temp,

        'humidity': humidity,

        'pressure': pressure,

        'wind_speed': wind_speed,

        'cloud_cover': cloud_cover,

        'hour': hour,

        'month': month,

        'latitude': latitude,

        'longitude': longitude
    })

    # ========================================================
    # CRÉATION DU DATAFRAME Y
    # ========================================================

    # Toutes les valeurs que l'IA devra apprendre
    Y = pd.DataFrame({

        'pred_temp_1h': target_temp_1h,

        'pred_humidity_1h': target_humidity_1h,

        'pred_wind_1h': target_wind_1h,

        'rain_probability': rain_prob
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