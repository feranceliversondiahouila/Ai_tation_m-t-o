const BACKEND_URL = "http://127.0.0.1:8000";

let weatherChart = null;
let currentWeatherData = null;
let selectedDate = null;
let currentOverlay = "";     // couche Windy active ("" = vue d'ensemble)

// ============================================================
// ICÔNES MÉTÉO
// ============================================================
const WEATHER_ICONS = {
    clear: "☀️", mostly_clear: "🌤️", partly_cloudy: "⛅", cloudy: "☁️",
    fog: "🌫️", drizzle: "🌦️", rain: "🌧️", freezing_rain: "🌧️",
    snow: "❄️", showers: "🌧️", snow_showers: "🌨️", storm: "⛈️",
};
function iconFor(label) { return WEATHER_ICONS[label] || "⛅"; }

const WIND_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"];
function windDirLabel(deg) {
    if (deg === undefined || deg === null) return "--";
    return WIND_DIRECTIONS[Math.round(deg / 45) % 8];
}

const DAY_NAMES_FR = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];

// ============================================================
// ÉLÉMENTS DU DOM
// ============================================================
const cityInput = document.getElementById("city-input");
const searchForm = document.getElementById("search-form");
const quickCitiesEl = document.getElementById("quick-cities");
const layerSwitchEl = document.getElementById("layer-switch");
const mapFrame = document.getElementById("weather-map");
const speakBtn = document.getElementById("btn-speak");

document.addEventListener("DOMContentLoaded", () => {
    loadQuickCities();
    if (cityInput && cityInput.value) fetchWeather(cityInput.value);
});

if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const city = cityInput.value.trim();
        if (city) fetchWeather(city);
    });
}

if (layerSwitchEl) {
    layerSwitchEl.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-overlay]");
        if (!btn) return;
        currentOverlay = btn.dataset.overlay;
        [...layerSwitchEl.children].forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        updateMap();
    });
}

if (speakBtn) {
    speakBtn.addEventListener("click", speakWeather);
}

// ============================================================
// VILLES RAPIDES
// ============================================================
async function loadQuickCities() {
    if (!quickCitiesEl) return;
    try {
        const res = await fetch(`${BACKEND_URL}/cities`);
        const cities = await res.json();

        quickCitiesEl.innerHTML = "";
        cities.forEach(c => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.textContent = c.name;
            btn.addEventListener("click", () => {
                cityInput.value = c.name;
                fetchWeather(c.name);
                [...quickCitiesEl.children].forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
            });
            quickCitiesEl.appendChild(btn);
        });
    } catch (e) {
        console.error("Impossible de charger la liste des villes rapides :", e);
    }
}

// ============================================================
// RÉCUPÉRATION DES DONNÉES MÉTÉO
// ============================================================
async function fetchWeather(city) {
    stopSpeaking();

    try {
        const response = await fetch(`${BACKEND_URL}/weather?city=${encodeURIComponent(city)}`);
        const data = await response.json();
        currentWeatherData = data;

        setText("city-name", data.city);
        setText("geo-coords", `Latitude : ${data.coordinates.latitude} | Longitude : ${data.coordinates.longitude}`);

        const badge = document.getElementById("status-badge");
        if (badge) {
            if (data.source && data.source.includes("Online")) {
                badge.textContent = "🌐 Mode En Ligne";
                badge.className = "badge online";
            } else {
                badge.textContent = "⚡ Mode Hors-Ligne (Edge AI)";
                badge.className = "badge offline";
            }
        }

        const now = data.now || {};
        setText("now-icon", iconFor(now.weather_label));
        setText("now-label", now.weather_label ? now.weather_label.replace("_", " ") : "--");
        setText("temp-val", `${now.temperature ?? "--"} °C`);
        setText("humidity-val", `${now.humidity ?? "--"} %`);
        setText("wind-val", `${now.wind_speed ?? "--"} km/h`);
        setText("wind-dir-val", windDirLabel(now.wind_direction));
        setText("pressure-val", `${now.pressure ?? "--"} hPa`);
        setText("cloud-val", `${now.cloud_cover ?? "--"} %`);
        setText("rain-val", `${now.rain_probability ?? "--"} %`);
        setText("sunrise-val", now.sunrise || "N/A");
        setText("sunset-val", now.sunset || "N/A");

        if (data.predictions_1h) {
            const p = data.predictions_1h;
            setText("pred-temp", `${p.temp_1h}°C`);
            setText("pred-hum", `${p.humidity_1h}%`);
            setText("pred-wind", `${p.wind_speed_1h} km/h`);
            setText("pred-rain", `${p.rain_probability}%`);
        }

        if (data.smart_indexes) {
            const s = data.smart_indexes;
            setText("idx-comfort", s.thermal_comfort_score);
            setText("idx-clothing", s.clothing_advice);
            setText("idx-activity", s.outdoor_activity);
            setText("idx-watering", s.plant_watering_needed);
            setText("idx-wind-risk", s.wind_risk);
        }

        renderDailyForecast(data.daily_forecast || [], data.today_date);

        selectedDate = data.today_date || (data.daily_forecast?.[0]?.date);
        selectDay(selectedDate);

        updateMap();

    } catch (error) {
        console.error("Erreur lors du fetch de l'API :", error);
        alert("Impossible de contacter le serveur FastAPI. Assurez-vous qu'uvicorn soit bien lancé sur le port 8000 !");
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

// ============================================================
// PRÉVISIONS CLIQUABLES (avant-hier / hier / aujourd'hui / demain / ...)
// ============================================================
function renderDailyForecast(days, todayDate) {
    const container = document.getElementById("days-scroll");
    if (!container) return;
    container.innerHTML = "";

    if (!days.length) {
        container.innerHTML = `<p class="placeholder">Prévisions indisponibles en mode hors-ligne.</p>`;
        return;
    }

    days.forEach((d) => {
        const date = new Date(d.date + "T00:00:00");
        const dayName = d.label || (d.date === todayDate ? "Aujourd'hui" : `${DAY_NAMES_FR[date.getDay()]} ${date.getDate()}`);

        const card = document.createElement("button");
        card.type = "button";
        card.className = "day-card";
        card.dataset.date = d.date;
        card.setAttribute("aria-pressed", d.date === selectedDate ? "true" : "false");
        card.innerHTML = `
            <span class="d-name">${dayName}</span>
            <span class="d-icon">${iconFor(d.weather_label)}</span>
            <span class="d-temp">${Math.round(d.temp_max)}° <span class="lo">${Math.round(d.temp_min)}°</span></span>
        `;
        card.addEventListener("click", () => selectDay(d.date));
        container.appendChild(card);
    });
}

function selectDay(dateStr) {
    if (!currentWeatherData || !dateStr) return;
    selectedDate = dateStr;

    // 1. Mettre à jour l'onglet actif (bleu)
    document.querySelectorAll("#days-scroll .day-card").forEach(el => {
        el.setAttribute("aria-pressed", el.dataset.date === dateStr ? "true" : "false");
    });

    const hourlyByDate = currentWeatherData.hourly_by_date || {};
    const hours = hourlyByDate[dateStr] || [];

    const isToday = dateStr === currentWeatherData.today_date;
    const label = isToday
        ? "Aujourd'hui"
        : new Date(dateStr + "T00:00:00").toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "short" });

    setText("hourly-title", `🕒 Vue horaire — ${label}`);
    setText("chart-title", `📊 Évolution de la température — ${label}`);

    // 2. RÉCUPÉRATION DU JOUR SÉLECTIONNÉ
    const dailyForecast = currentWeatherData.daily_forecast || [];
    const selectedDayData = dailyForecast.find(d => d.date === dateStr);

    // 3. MISE À JOUR DU BLOC CENTRAL
    if (selectedDayData) {
        // Affiche la température Max prévue pour ce jour (ex: 25 °C ou 28 °C)
        const displayTemp = Math.round(selectedDayData.temp_max);
        
        setText("temp-val", `${displayTemp} °C`);
        setText("now-icon", iconFor(selectedDayData.weather_label));
        setText("now-label", selectedDayData.weather_label ? selectedDayData.weather_label.replace("_", " ") : "--");

        // Mise à jour des métriques moyennes/max des heures de ce jour
        if (hours.length > 0) {
            const avgHum = Math.round(hours.reduce((acc, h) => acc + (h.humidity || 0), 0) / hours.length);
            const avgWind = Math.round(hours.reduce((acc, h) => acc + (h.wind_speed || 0), 0) / hours.length);
            const maxRain = Math.max(...hours.map(h => h.rain_prob || 0));

            setText("humidity-val", `${avgHum || "--"} %`);
            setText("wind-val", `${avgWind || "--"} km/h`);
            setText("rain-val", `${maxRain}%`);
        }
    } else if (isToday) {
        // Retour aux données temps réel
        const now = currentWeatherData.now || {};
        setText("now-icon", iconFor(now.weather_label));
        setText("now-label", now.weather_label ? now.weather_label.replace("_", " ") : "--");
        setText("temp-val", `${now.temperature ?? "--"} °C`);
        setText("humidity-val", `${now.humidity ?? "--"} %`);
        setText("wind-val", `${now.wind_speed ?? "--"} km/h`);
        setText("rain-val", `${now.rain_probability ?? "--"} %`);
    }

    // 4. Mettre à jour le graphique et les heures
    renderHourlyStrip(hours);
    renderChart(hours);
}

// ============================================================
// VUE HORAIRE
// ============================================================
function renderHourlyStrip(hours) {
    const container = document.getElementById("hours-scroll");
    if (!container) return;
    container.innerHTML = "";

    if (!hours.length) {
        container.innerHTML = `<p class="placeholder">Vue horaire indisponible pour ce jour.</p>`;
        return;
    }

    hours.forEach(item => {
        const date = new Date(item.time);
        const el = document.createElement("div");
        el.className = "hour-item" + (item.is_now ? " now" : "");
        el.innerHTML = `
            <span class="h-time">${item.is_now ? "Maintenant" : date.getHours() + "h"}</span>
            <span class="h-icon">${iconFor(item.weather_label)}</span>
            <span class="h-temp">${Math.round(item.temp_c)}°</span>
            <span class="h-rain">💧${item.rain_prob}%</span>
        `;
        container.appendChild(el);
    });
}

// ============================================================
// GRAPHIQUE CHART.JS
// ============================================================
function renderChart(hours) {
    const canvas = document.getElementById("weatherChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (weatherChart) weatherChart.destroy();
    if (!hours.length) return;

    const labels = hours.map(item => `${new Date(item.time).getHours()}h`);
    const temps = hours.map(item => item.temp_c);

    const gradient = ctx.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, "rgba(59, 130, 246, 0.4)");
    gradient.addColorStop(1, "rgba(59, 130, 246, 0.0)");

    weatherChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Température (°C)",
                data: temps,
                borderColor: "#3b82f6",
                borderWidth: 3,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#8b9bb4", maxTicksLimit: 10 } },
                y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#8b9bb4" } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

// ============================================================
// CARTE MÉTÉO (Windy, intégrée en iframe)
// ============================================================
function updateMap() {
    if (!currentWeatherData || !mapFrame) return;
    const { latitude, longitude } = currentWeatherData.coordinates;

    const params = new URLSearchParams({
        lat: latitude,
        lon: longitude,
        detailLat: latitude,
        detailLon: longitude,
        zoom: 7,
        level: "surface",
        overlay: currentOverlay || "wind",
        menu: "",
        message: "",
        marker: "true",
        calendar: "now",
        pressure: "",
        type: "map",
        location: "coordinates",
        metricWind: "km/h",
        metricTemp: "default",
    });

    mapFrame.src = `https://embed.windy.com/embed2.html?${params.toString()}`;
}

// ============================================================
// BRIEFING VOCAL NATIVE & HORS-LIGNE (Web Speech API)
// ============================================================
function speakWeather() {
    if (!('speechSynthesis' in window)) {
        alert("Votre navigateur ne supporte pas la synthèse vocale.");
        return;
    }

    if (window.speechSynthesis.speaking) {
        stopSpeaking();
        return;
    }

    if (!currentWeatherData) {
        alert("Veuillez charger la météo d'une ville avant d'écouter le bulletin.");
        return;
    }

    const city = currentWeatherData.city || "votre ville";
    const now = currentWeatherData.now || {};
    const temp = Math.round(now.temperature ?? 20);
    const rain = now.rain_probability ?? 0;
    const wind = Math.round(now.wind_speed ?? 0);

    // Conseil dynamique et humain selon la température
    let advice = "";
    if (temp >= 30) {
        advice = "Attention, il fait particulièrement chaud aujourd'hui ! Pensez à bien vous hydrater et mettez-vous à l'ombre ou à l'abri.";
    } else if (temp >= 22) {
        advice = "Il fait très bon et chaud, c'est une excellente journée pour profiter de l'extérieur en tenue légère !";
    } else if (temp >= 15) {
        advice = "La température est douce et agréable, une petite veste légère fera parfaitement l'affaire.";
    } else if (temp >= 5) {
        advice = "Il fait plutôt frais dehors. Je vous conseille de porter un bon manteau avant de sortir.";
    } else {
        advice = "Il fait vraiment très froid ! N'oubliez pas votre gros manteau, écharpe et gants.";
    }

    if (rain > 50) {
        advice += " N'oubliez pas votre parapluie, le risque de pluie est important.";
    } else if (wind > 45) {
        advice += " Attention également aux fortes rafales de vent.";
    }

    const textToSpeak = `Bonjour ! Voici la météo actuelle pour ${city}. Il fait ${temp} degrés Celsius. ${advice}`;

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = "fr-FR";
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const frVoice = voices.find(v => v.lang.includes("fr") || v.lang.includes("FR"));
    if (frVoice) utterance.voice = frVoice;

    utterance.onstart = () => {
        setSpeakButtonState("playing");
    };

    utterance.onend = () => {
        setSpeakButtonState("idle");
    };

    utterance.onerror = () => {
        setSpeakButtonState("idle");
    };

    window.speechSynthesis.speak(utterance);
}

function stopSpeaking() {
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
    setSpeakButtonState("idle");
}

function setSpeakButtonState(state) {
    if (!speakBtn) return;
    speakBtn.classList.remove("playing", "loading");
    if (state === "playing") {
        speakBtn.classList.add("playing");
        speakBtn.textContent = "⏹ Stop";
    } else {
        speakBtn.textContent = "🔊 Écouter";
    }
}