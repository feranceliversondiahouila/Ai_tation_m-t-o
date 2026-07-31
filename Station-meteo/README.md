# 🌤️ Station Météo Connectée & Edge AI

Tableau de bord météo avec bascule automatique **En ligne / Hors-ligne** :
- **En ligne** : données en temps réel via l'API [Open-Meteo](https://open-meteo.com/) (gratuite, sans clé).
- **Hors-ligne** : un modèle d'IA embarqué (*Edge AI*), entraîné sur de vraies données de capteurs IoT, prend le relais pour estimer température et humidité.

## Structure du projet

```
Station-meteo/
├── backend/                # API FastAPI
│   ├── main.py              # Routes (/weather, /cities) + bascule online/offline
│   ├── ai_model.py           # Entraînement et inférence du modèle Edge AI
│   ├── network_checker.py    # Détection de la connexion Internet
│   └── requirements.txt
├── data/
│   ├── data_generator.py     # Préparation du dataset IoT réel pour l'entraînement
│   └── iot_telemetry_data.csv.xls   # Dataset Kaggle "Environmental Sensor Telemetry Data"
├── frontend/                # Dashboard HTML / CSS / JS (Chart.js, carte Windy)
├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```

## Prérequis

- Python 3.11+
- (Optionnel) Docker & Docker Compose

## Lancement en local (sans Docker)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Puis ouvre `frontend/index.html` dans ton navigateur (ou sers le dossier `frontend/`
avec un petit serveur statique, par exemple `python -m http.server 1200` depuis
ce dossier).

Au tout premier lancement, si `backend/edge_model.pkl` n'existe pas encore,
le modèle Edge AI est automatiquement entraîné à partir de
`data/iot_telemetry_data.csv.xls` (quelques secondes) et sauvegardé pour les
lancements suivants.

## Lancement avec Docker

```bash
docker compose up --build
```

- Backend (FastAPI) → http://localhost:8000
- Frontend (nginx) → http://localhost:1200

## Endpoints de l'API

| Méthode | Route      | Description                                    |
|---------|-----------|-------------------------------------------------|
| GET     | `/cities` | Liste des villes de sélection rapide            |
| GET     | `/weather?city=...` (ou `?lat=...&lon=...`) | Météo actuelle, prévisions et indices intelligents |

Documentation interactive générée par FastAPI : http://localhost:8000/docs

## Notes

- Le bulletin vocal du bouton **🔊 Écouter** utilise la synthèse vocale native
  du navigateur (Web Speech API), entièrement côté client — aucune clé API
  n'est nécessaire.
- Le dataset IoT réel (`iot_telemetry_data.csv.xls`) ne contient pas de mesure
  de vent, de pression ou de position GPS (capteurs d'intérieur) : ces valeurs
  restent donc estimées par défaut en mode hors-ligne, ce qui est indiqué
  clairement dans le code (`ai_model.py`, `main.py`).
