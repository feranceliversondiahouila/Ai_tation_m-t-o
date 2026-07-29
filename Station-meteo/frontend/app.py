# ============================================================
# IMPORTS
# ============================================================

# Streamlit permet de créer une interface Web en Python
import streamlit as st

# requests permet de communiquer avec le Backend FastAPI
import requests

# pandas permet de manipuler les données et afficher des graphiques
import pandas as pd


# ============================================================
# CONFIGURATION DE LA PAGE STREAMLIT
# ============================================================

st.set_page_config(

    # Titre affiché dans l'onglet du navigateur
    page_title="Station Météo IA",

    # Icône affichée dans l'onglet
    page_icon="🌤️",

    # Utilisation de toute la largeur disponible
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

# session_state sert à conserver des données
# même lorsque la page se recharge.

# Si aucune ville n'existe encore dans la session
if "selected_city" not in st.session_state:

    # Ville par défaut
    st.session_state["selected_city"] = "Pointe-Noire"

# Latitude mémorisée
if "lat" not in st.session_state:
    st.session_state["lat"] = None

# Longitude mémorisée
if "lon" not in st.session_state:
    st.session_state["lon"] = None


# ============================================================
# TITRE PRINCIPAL
# ============================================================

st.title("🌤️ Station Météo Connectée & Edge AI")

# Ligne horizontale
st.markdown("---")


# ============================================================
# SIDEBAR (MENU LATÉRAL)
# ============================================================

st.sidebar.header("📍 Configuration de la Ville")


# ============================================================
# CHAMP DE SAISIE DE LA VILLE
# ============================================================

city_input = st.sidebar.text_input(

    # Libellé visible
    "Entrez une ville :",

    # Valeur affichée par défaut
    value=st.session_state["selected_city"]
)


# ============================================================
# BOUTONS RACCOURCIS
# ============================================================

st.sidebar.markdown("**Favoris :**")

# Création de 3 colonnes
col_f1, col_f2, col_f3 = st.sidebar.columns(3)

# Bouton Pointe-Noire
if col_f1.button("Pointe-Noire"):
    city_input = "Pointe-Noire"

# Bouton Béthune
if col_f2.button("Béthune"):
    city_input = "Béthune"

# Bouton Paris
if col_f3.button("Paris"):
    city_input = "Paris"


# ============================================================
# SAUVEGARDE DE LA VILLE DANS LA SESSION
# ============================================================

st.session_state["selected_city"] = city_input


# ============================================================
# URL DU BACKEND FASTAPI
# ============================================================

# ATTENTION :
# Dans ton vrai code il ne faut PAS les balises HTML.
#
# Utilise simplement :
#
# BACKEND_URL = "http://127.0.0.1:8000/weather"

BACKEND_URL = "http://127.0.0.1:8000/weather"


# ============================================================
# APPEL DU BACKEND
# ============================================================

try:

    # Envoi d'une requête HTTP GET
    #
    # Exemple :
    # /weather?city=Paris
    response = requests.get(

        BACKEND_URL,

        params={
            "city": st.session_state["selected_city"]
        }
    )

    # Conversion du JSON en dictionnaire Python
    data = response.json()


    # ========================================================
    # STOCKAGE DES COORDONNÉES
    # ========================================================

    # Le backend renvoie :
    #
    # {
    #   "coordinates": {
    #      "latitude": ...
    #      "longitude": ...
    #   }
    # }

    st.session_state["lat"] = (
        data["coordinates"]["latitude"]
    )

    st.session_state["lon"] = (
        data["coordinates"]["longitude"]
    )


    # ========================================================
    # AFFICHAGE DES COORDONNÉES
    # ========================================================

    st.sidebar.markdown("---")

    st.sidebar.subheader(
        "🌐 Coordonnées Auto-détectées"
    )

    st.sidebar.text(
        f"Latitude : {st.session_state['lat']}"
    )

    st.sidebar.text(
        f"Longitude : {st.session_state['lon']}"
    )


    # ========================================================
    # MODE ONLINE OU OFFLINE
    # ========================================================

    if "Online" in data["source"]:

        st.success(
            f"🌐 Mode En Ligne — Métriques pour {data['city']}"
        )

    else:

        st.warning(
            f"⚡ Mode Hors-Ligne (Edge AI) — Prédictions pour {data['city']}"
        )


    # ========================================================
    # CARTES MÉTÉO
    # ========================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    # Informations météo actuelles
    now = data["now"]

    # Température
    col1.metric(
        "🌡️ Température",
        f"{now['temperature']} °C"
    )

    # Humidité
    col2.metric(
        "💧 Humidité",
        f"{now['humidity']} %"
    )

    # Vent
    col3.metric(
        "💨 Vent",
        f"{now['wind_speed']} km/h"
    )

    # Lever du soleil
    col4.metric(
        "🌅 Lever du Soleil",
        now.get("sunrise", "N/A")
    )

    # Coucher du soleil
    col5.metric(
        "🌇 Coucher du Soleil",
        now.get("sunset", "N/A")
    )

    st.markdown("---")


    # ========================================================
    # GRAPHIQUE TEMPOREL
    # ========================================================

    st.subheader(
        "📊 Évolution Temporelle Heure par Heure"
    )

    # Récupération des données horaires
    timeline = data.get(
        "timeline_hourly",
        {}
    )

    # Historique passé
    history = timeline.get(
        "history_past_48h",
        []
    )

    # Heure actuelle
    current = timeline.get(
        "current_hour",
        {}
    )

    # Prévisions futures
    forecast = timeline.get(
        "forecast_next_24h",
        []
    )


    # ========================================================
    # RECONSTRUCTION DE LA CHRONOLOGIE
    # ========================================================

    # On fusionne :
    #
    # historique
    # +
    # heure actuelle
    # +
    # futur
    full_series = (
        history
        + [current]
        + forecast
    )


    # ========================================================
    # CRÉATION DU GRAPHIQUE
    # ========================================================

    if full_series:

        # Transformation en DataFrame
        df = pd.DataFrame(full_series)

        # Conversion des dates
        df["time"] = pd.to_datetime(
            df["time"]
        )

        # Utilisation des dates comme index
        df = df.set_index("time")

        # Affichage du graphique
        st.line_chart(
            df["temp_c"]
        )

# ============================================================
# GESTION DES ERREURS
# ============================================================

except Exception as e:

    # Affichage d'un message si le backend
    # n'est pas lancé
    st.error(
        f"❌ Erreur de connexion au Backend API : {e}"
    )