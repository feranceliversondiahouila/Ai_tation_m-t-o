# Ai_station_m-t-o
Il s'agit d'un projet de fin d'année donné par l'université, qui implique la réalisation d'une station de météo intelligente. 

---

# 🌍 Station Météo Connectée & IA Globale (Local-First / Edge AI)

Ce projet propose une **station météo intelligente 100% logicielle**, conteneurisée avec **Docker**, capable de fonctionner en mode **Edge AI (Offline)** tout en exploitant les réseaux externes (**Online**) lorsque la connectivité le permet.

L'application intègre un **Globe Terrestre 3D interactif** permettant de visualiser en temps réel la température, l'humidité et la force du vent par région, ainsi qu'une analyse prédictive des risques météo générée par un modèle d'IA local.

---

## 🚀 Fonctionnalités Principales

* **🌍 Globe 3D Interactif :** Visualisation dynamique des données météo mondiales (hauteur des barres selon la température, couleurs selon l'intensité).
* **🧠 IA Locale (Edge AI) :** Analyse et prédiction à court terme des risques de météo extrême (tempête, pluie, stabilité) via un modèle `Scikit-Learn` embarqué.
* **🌐 Arbitrage Réseau Dynamique (Online / Offline) :**
* **Mode Connecté :** Synchronisation avec des API externes (*Open-Meteo*) et enrichissement des prévisions.
* **Mode Hors-Ligne :** Bascule automatique sans interruption sur le modèle de Machine Learning et la base de données SQLite locaux.


* **🐳 100% Dockerisé :** Architecture multi-conteneurs orchestrée par Docker Compose.

---

## 🛠️ Stack Technique

* **Langage principal :** Python 3.11
* **Machine Learning / IA :** `Scikit-Learn`, `Joblib`, `Pandas`, `NumPy`
* **Backend & API :** `FastAPI`, `Uvicorn`
* **Frontend / Dashboard 3D :** `Streamlit`, `PyDeck`
* **Stockage & Réseau :** `SQLite3`, `Requests`, `Urllib3`
* **Déploiement :** `Docker`, `Docker Compose`

---

## 📁 Architecture du Projet

```text
station-meteo-ia/
├── 🐳 docker-compose.yml           # Configuration globale Multi-Containers
├── 📄 requirements.txt             # Dépendances Python du projet
├── 📄 README.md                    # Documentation du projet
│
├── 🧠 backend/                     # API FastAPI et Modèle IA
│   ├── 🐳 Dockerfile               # Container du Backend
│   ├── 📜 main.py                  # API REST & points d'accès
│   ├── 📜 ai_model.py              # Logique d'apprentissage et prédictions
│   └── 📜 network_checker.py       # Détection de la connectivité réseau
│
├── 🌐 frontend/                    # Interface utilisateur & 3D
│   ├── 🐳 Dockerfile               # Container du Frontend
│   └── 📜 app.py                   # Tableau de bord Streamlit & Globe PyDeck
│
└── 🗄️ data/                       # Données & Simulation
    └── 📜 generate_data.py         # Génération et récupération des métriques

```

---

## 💻 Installation et Lancement

### Prérequis

* [Docker Desktop](https://www.docker.com/) installé et démarré sur votre machine.
* Git pour cloner le projet.

### Lancement Rapide (Recommandé avec Docker)

1. **Cloner le dépôt :**
```bash
git clone https://github.com/votre-compte/station-meteo-ia.git
cd station-meteo-ia

```


2. **Lancer l'application avec Docker Compose :**
```bash
docker compose up --build

```


3. **Accéder aux services :**
* 🌐 **Dashboard & Globe 3D :** [http://localhost:8501](http://localhost:8501)
* 🧠 **Documentation API FastAPI :** [http://localhost:8000/docs](http://localhost:8000/docs)



---

## 🧪 Tester le Mode Hors-Ligne (Offline AI)

Pour vérifier le basculement intelligent entre le réseau et l'IA locale :

1. Ouvrez l'interface Streamlit sur [http://localhost:8501](http://localhost:8501).
2. Déconnectez le Wi-Fi / réseau de votre ordinateur ou coupez l'accès réseau du container.
3. Observez l'indicateur dans le tableau de bord passer en **`Mode Offline (Edge AI)`** : l'IA continue de prédire les risques de tempête et de pluie sans aucune interruption ni erreur réseau !

---
