const BACKEND_URL = "http://127.0.0.1:8000";
let weatherChart = null;
let currentWeatherData = null;   // dernière réponse complète de l'API
let currentOverlay = "";          // couche Windy active ("" = vue d'ensemble)

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

document.addEventListener("DOMContentLoaded", () => {
    loadQuickCities();
    fetchWeather(cityInput.value);
});

searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const city = cityInput.value.trim();
    if (city) fetchWeather(city);
});

layerSwitchEl.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-overlay]");
    if (!btn) return;
    currentOverlay = btn.dataset.overlay;
    [...layerSwitchEl.children].forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    updateMap();
});

// ============================================================
// VILLES RAPIDES
// ============================================================
async function loadQuickCities() {
    try {
        const res = await fetch(`${BACKEND_URL}/cities`);
        const cities = await res.json();

        quickCitiesEl.innerHTML = "";
        cities.forEach(c => {
            const btn = document.createElement("button");
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
    try {
        const response = await fetch(`${BACKEND_URL}/weather?city=${encodeURIComponent(city)}`);
        const data = await response.json();
        currentWeatherData = data;

        // -- En-tête ville --
        document.getElementById("city-name").textContent = data.city;
        document.getElementById("geo-coords").textContent =
            `Latitude : ${data.coordinates.latitude} | Longitude : ${data.coordinates.longitude}`;

        // -- Badge de statut --
        const badge = document.getElementById("status-badge");
        if (data.source.includes("Online")) {
            badge.textContent = "🌐 Mode En Ligne";
            badge.className = "badge online";
        } else {
            badge.textContent = "⚡ Mode Hors-Ligne (Edge AI)";
            badge.className = "badge offline";
        }

        // -- Conditions actuelles --
        const now = data.now;
        document.getElementById("now-icon").textContent = iconFor(now.weather_label);
        document.getElementById("now-label").textContent = now.weather_label ? now.weather_label.replace("_", " ") : "--";
        document.getElementById("temp-val").textContent = `${now.temperature} °C`;
        document.getElementById("humidity-val").textContent = `${now.humidity} %`;
        document.getElementById("wind-val").textContent = `${now.wind_speed} km/h`;
        document.getElementById("wind-dir-val").textContent = windDirLabel(now.wind_direction);
        document.getElementById("pressure-val").textContent = `${now.pressure ?? "--"} hPa`;
        document.getElementById("cloud-val").textContent = `${now.cloud_cover ?? "--"} %`;
        document.getElementById("rain-val").textContent = `${now.rain_probability ?? "--"} %`;
        document.getElementById("sunrise-val").textContent = now.sunrise || "N/A";
        document.getElementById("sunset-val").textContent = now.sunset || "N/A";

        // -- Prédiction IA +1h --
        if (data.predictions_1h) {
            const p = data.predictions_1h;
            document.getElementById("pred-temp").textContent = `${p.temp_1h}°C`;
            document.getElementById("pred-hum").textContent = `${p.humidity_1h}%`;
            document.getElementById("pred-wind").textContent = `${p.wind_speed_1h} km/h`;
            document.getElementById("pred-rain").textContent = `${p.rain_probability}%`;
        }

        // -- Indices intelligents --
        if (data.smart_indexes) {
            const s = data.smart_indexes;
            document.getElementById("idx-comfort").textContent = s.thermal_comfort_score;
            document.getElementById("idx-clothing").textContent = s.clothing_advice;
            document.getElementById("idx-activity").textContent = s.outdoor_activity;
            document.getElementById("idx-watering").textContent = s.plant_watering_needed;
            document.getElementById("idx-wind-risk").textContent = s.wind_risk;
        }

        // -- Prévisions cliquables (avant-hier / hier / aujourd'hui / demain / ...) --
        renderDailyForecast(data.daily_forecast || [], data.today_date);

        // -- Sélectionne "aujourd'hui" par défaut --
        selectDay(data.today_date);

        // -- Carte Windy centrée sur la ville --
        updateMap();

    } catch (error) {
        console.error("Erreur lors du fetch de l'API :", error);
        alert("Impossible de contacter le serveur FastAPI. Assurez-vous qu'uvicorn soit bien lancé sur le port 8000 !");
    }
}

// ============================================================
// PRÉVISIONS CLIQUABLES (bandeau du haut)
// ============================================================
function renderDailyForecast(days, todayDate) {
    const container = document.getElementById("days-scroll");
    container.innerHTML = "";

    if (!days.length) {
        container.innerHTML = `<p class="placeholder">Prévisions indisponibles en mode hors-ligne.</p>`;
        return;
    }

    days.forEach((d) => {
        const date = new Date(d.date + "T00:00:00");
        let dayName;
        if (d.date === todayDate) dayName = "Aujourd'hui";
        else dayName = DAY_NAMES_FR[date.getDay()] + " " + date.getDate();

        const card = document.createElement("button");
        card.type = "button";
        card.className = "day-card";
        card.dataset.date = d.date;
        card.setAttribute("aria-pressed", d.date === todayDate ? "true" : "false");
        card.innerHTML = `
            <span class="d-name">${dayName}</span>
            <span class="d-icon">${iconFor(d.weather_label)}</span>
            <span class="d-temp">${Math.round(d.temp_max)}° <span class="lo">${Math.round(d.temp_min)}°</span></span>
        `;
        card.addEventListener("click", () => selectDay(d.date));
        container.appendChild(card);
    });
}

// ============================================================
// SÉLECTION D'UN JOUR : met à jour vue horaire + graphique
// ============================================================
function selectDay(dateStr) {
    if (!currentWeatherData) return;

    // Met en évidence la carte du jour choisi
    document.querySelectorAll("#days-scroll .day-card").forEach(el => {
        el.setAttribute("aria-pressed", el.dataset.date === dateStr ? "true" : "false");
    });

    const hourlyByDate = currentWeatherData.hourly_by_date || {};
    const hours = hourlyByDate[dateStr] || [];

    const isToday = dateStr === currentWeatherData.today_date;
    const label = isToday ? "Aujourd'hui" : new Date(dateStr + "T00:00:00").toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "short" });

    document.getElementById("hourly-title").textContent = `🕒 Vue horaire — ${label}`;
    document.getElementById("chart-title").textContent = `📊 Évolution de la température — ${label}`;

    renderHourlyStrip(hours);
    renderChart(hours);
}

// ============================================================
// VUE HORAIRE (pour le jour sélectionné)
// ============================================================
function renderHourlyStrip(hours) {
    const container = document.getElementById("hours-scroll");
    container.innerHTML = "";

    if (!hours.length) {
        container.innerHTML = `<p class="placeholder">Vue horaire indisponible pour ce jour (mode hors-ligne ou date hors plage).</p>`;
        return;
    }

    hours.forEach(item => {
        const date = new Date(item.time);
        const el = document.createElement("div");
        el.className = "hour-item";
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
// GRAPHIQUE CHART.JS (pour le jour sélectionné)
// ============================================================
function renderChart(hours) {
    const ctx = document.getElementById("weatherChart").getContext("2d");
    if (weatherChart) weatherChart.destroy();

    if (!hours.length) return;

    const labels = hours.map(item => `${new Date(item.time).getHours()}h`);
    const temps = hours.map(item => item.temp_c);

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, "rgba(59, 130, 246, 0.5)");
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
                pointRadius: 2,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#8b9bb4", maxTicksLimit: 8 } },
                y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#8b9bb4" } }
            },
            plugins: { legend: { labels: { color: "#ffffff" } } }
        }
    });
}

// ============================================================
// CARTE MÉTÉO (Windy, intégrée en iframe)
// ============================================================
// overlay : "" (vue d'ensemble), "temp", "wind", "rh" (humidité)
function updateMap() {
    if (!currentWeatherData) return;
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
