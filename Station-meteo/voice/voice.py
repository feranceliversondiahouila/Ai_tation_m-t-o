# ============================================================
# 1. IMPORTS
# ============================================================

# os permet de récupérer les variables d'environnement
# stockées sur le système.
#
# Exemple :
# OPENAI_API_KEY
#
import os

# SDK officiel OpenAI
#
# Sert à :
# - générer du texte
# - générer de la voix
# - utiliser GPT
#
import random
from openai import OpenAI


# ============================================================
# 2. CONNEXION À OPENAI (créée à la demande)
# ============================================================
#
# Important : on NE crée PAS le client ici, au chargement du
# module. Si on le faisait, le moindre souci (SDK, dépendances,
# clé absente) ferait planter TOUT le serveur FastAPI au
# démarrage — y compris les routes météo qui n'ont rien à voir
# avec la voix. Le client n'est donc créé qu'au moment réel de
# l'appel, dans text_to_speech().

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


# ============================================================
# 3. AVIS "PERSONNEL" SUR LA TEMPÉRATURE ET LA PLUIE
# ============================================================
#
# C'est ici que la station donne son avis, comme le ferait une
# personne, plutôt que de réciter un chiffre brut.

def _temperature_opinion(temp: float) -> str:
    if temp >= 35:
        return (
            "Attention, il fait vraiment très chaud : je te conseille de "
            "te mettre à l'abri, de rester au frais et de bien t'hydrater."
        )
    if temp >= 28:
        return "Il fait chaud aujourd'hui, pense à bien boire et à te protéger du soleil."
    if temp >= 18:
        return "Les températures sont agréables, plutôt une belle journée en perspective."
    if temp >= 8:
        return "Il fait un peu frais, une petite veste ne sera pas de trop."
    if temp >= 0:
        return "Il fait froid, je te conseille de bien te couvrir avant de sortir."
    return "Attention, les températures sont négatives : couvre-toi bien et prends garde au verglas."


def _rain_opinion(rain_prob) -> str:
    try:
        rain_prob = float(rain_prob)
    except (TypeError, ValueError):
        return ""
    if rain_prob >= 50:
        return " Et n'oublie pas ton parapluie, la pluie est bien présente."
    if rain_prob >= 20:
        return " Garde aussi un œil sur le ciel, un petit risque de pluie n'est pas exclu."
    return ""


# ============================================================
# 4. CONSTRUCTION DU TEXTE À LIRE
# ============================================================

INTROS = [
    "Voici le point météo pour {city}.",
    "Météo à {city}.",
    "Bulletin météo pour {city}.",
]

OUTROS = [
    "Bonne journée !",
    "Passe une excellente journée !",
    "À bientôt pour un nouveau point météo.",
]


def build_speech_text(data: dict) -> str:
    """
    Transforme les données météo JSON en une phrase naturelle,
    comme si quelqu'un te faisait le point météo à l'oral —
    avec son avis sur la température, pas juste des chiffres.
    """

    city = data["city"]
    now = data["now"]
    idx = data.get("smart_indexes", {})
    pred = data.get("predictions_1h", {})

    intro = random.choice(INTROS).format(city=city)
    outro = random.choice(OUTROS)

    temp = now.get("temperature")
    humidity = now.get("humidity")
    wind = now.get("wind_speed")
    rain_prob = now.get("rain_probability")

    conditions = (
        f"Il fait actuellement {temp} degrés, avec {humidity}% d'humidité "
        f"et un vent à {wind} kilomètres heure."
    )

    opinion = _temperature_opinion(temp) if temp is not None else ""
    rain_note = _rain_opinion(rain_prob)

    trend = ""
    temp_1h = pred.get("temp_1h")
    if temp_1h is not None and temp is not None and abs(temp_1h - temp) >= 1:
        direction = "monter" if temp_1h > temp else "descendre"
        trend = f" D'ici une heure, la température devrait {direction} autour de {temp_1h} degrés."

    activity = idx.get("outdoor_activity")
    activity_note = f" {activity.rstrip('.!')}." if activity else ""

    return " ".join(part for part in [
        intro, conditions, opinion + rain_note, trend.strip(), activity_note.strip(), outro
    ] if part)


# ============================================================
# 5. CONVERSION TEXTE -> VOIX
# ============================================================

def text_to_speech(text: str) -> bytes:
    """
    Reçoit un texte.

    Retourne un fichier audio MP3
    sous forme de données binaires (bytes).
    """

    # ========================================================
    # APPEL DU MOTEUR TTS OPENAI
    # ========================================================

    response = _get_client().audio.speech.create(

        # Modèle de synthèse vocale
        model="tts-1",

        # Voix utilisée
        #
        # Possibilités :
        # alloy
        # echo
        # fable
        # onyx
        # nova
        # shimmer
        #
        voice="nova",

        # Texte à lire
        input=text,

        # Format de sortie
        response_format="mp3",
    )

    # ========================================================
    # RETOUR DU MP3
    # ========================================================

    # response.content contient
    # les données audio du fichier MP3.
    return response.content


# ============================================================
# 6. FONCTION PRINCIPALE
# ============================================================

def speak_weather(data: dict) -> bytes:
    """
    Fonction la plus simple à utiliser.

    Elle :

    1. Reçoit les données météo
    2. Génère le texte
    3. Génère l'audio
    4. Retourne le MP3
    """

    # Création du texte météo
    text = build_speech_text(data)

    # Génération de la voix
    return text_to_speech(text)