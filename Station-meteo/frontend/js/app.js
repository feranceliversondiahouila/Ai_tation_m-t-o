const BACKEND_URL = "http://127.0.0.1:8000/weather";
let weatherChart = null;
let myGlobe = null;

// Éléments du DOM
const cityInput = document.getElementById("city-input");
const searchBtn = document.getElementById("search-btn");

// Charger la météo au lancement de la page
document.addEventListener("DOMContentLoaded", () => {
    fetchWeather(cityInput.value);
});

// Recherche au clic sur le bouton
searchBtn.addEventListener("click", () => {
    const city = cityInput.value.trim();
    if (city) fetchWeather(city);
});

// Touche Entrée dans l'input
cityInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        searchBtn.click();
    }
});

// 1. Récupération des données FastAPI
async function fetchWeather(city) {
    try {
        const response = await fetch(`${BACKEND_URL}?city=${encodeURIComponent(city)}`);
        const data = await response.json();

        // Mise à jour de la topbar & ville
        document.getElementById("city-name").textContent = data.city;
        document.getElementById("geo-coords").textContent = 
            `Latitude : ${data.coordinates.latitude} | Longitude : ${data.coordinates.longitude}`;

        const badge = document.getElementById("status-badge");
        if (data.source.includes("Online")) {
            badge.textContent = "🌐 Mode En Ligne";
            badge.className = "badge online";
        } else {
            badge.textContent = "⚡ Mode Hors-Ligne (Edge AI)";
            badge.className = "badge offline";
        }

        // Mise à jour des cartes météo
        document.getElementById("temp-val").textContent = `${data.now.temperature} °C`;
        document.getElementById("humidity-val").textContent = `${data.now.humidity} %`;
        document.getElementById("wind-val").textContent = `${data.now.wind_speed} km/h`;
        document.getElementById("sunrise-val").textContent = data.now.sunrise || "N/A";
        document.getElementById("sunset-val").textContent = data.now.sunset || "N/A";

        // Graphique Chart.js
        renderChart(data.timeline_hourly);

        // Globe 3D
        update3DGlobe(
            data.coordinates.latitude, 
            data.coordinates.longitude, 
            data.city, 
            data.now.temperature
        );

    } catch (error) {
        console.error("Erreur lors du fetch de l'API :", error);
        alert("Impossible de contacter le serveur FastAPI. Assurez-vous qu'uvicorn soit bien lancé sur le port 8000 !");
    }
}

// 2. Rendu du graphique temporel Chart.js
function renderChart(timelineData) {
    if (!timelineData) return;

    const history = timelineData.history_past_48h || [];
    const current = timelineData.current_hour ? [timelineData.current_hour] : [];
    const forecast = timelineData.forecast_next_24h || [];

    const fullData = [...history, ...current, ...forecast];

    const labels = fullData.map(item => {
        const date = new Date(item.time);
        return `${date.getHours()}h (${date.getDate()}/${date.getMonth()+1})`;
    });

    const temps = fullData.map(item => item.temp_c);
    const ctx = document.getElementById("weatherChart").getContext("2d");

    if (weatherChart) {
        weatherChart.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, "rgba(59, 130, 246, 0.5)");
    gradient.addColorStop(1, "rgba(59, 130, 246, 0.0)");

    weatherChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Température (°C)',
                data: temps,
                borderColor: '#3b82f6',
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
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#8b9bb4' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#8b9bb4' }
                }
            },
            plugins: {
                legend: { labels: { color: '#ffffff' } }
            }
        }
    });
}

// 3. Rendu et animation du Globe 3D
function update3DGlobe(lat, lon, cityName, temp) {
    const container = document.getElementById('globeViz');

    const markerData = [{
        lat: lat,
        lng: lon,
        name: cityName,
        temp: `${temp} °C`
    }];

    // Si le globe est déjà créé, on fait pivoter la vue vers la nouvelle ville
    if (myGlobe) {
        myGlobe
            .pointsData(markerData)
            .labelsData(markerData)
            .pointOfView({ lat: lat, lng: lon, altitude: 2 }, 1500);
        return;
    }

    // Création initiale du Globe 3D avec Globe.gl
    myGlobe = Globe()(container)
        .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-dark.jpg')
        .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundColor('#0b0f19')
        .width(container.clientWidth)
        .height(450)
        
        // Point lumineux sur les coordonnées
        .pointsData(markerData)
        .pointAltitude(0.05)
        .pointColor(() => '#3b82f6')
        .pointRadius(0.7)
        
        // Étiquette 3D avec le nom de la ville et sa température
        .labelsData(markerData)
        .labelLat(d => d.lat)
        .labelLng(d => d.lng)
        .labelText(d => `${d.name} : ${d.temp}`)
        .labelSize(1.8)
        .labelDotRadius(0.4)
        .labelColor(() => '#ffffff')
        .labelResolution(3);

    // Ajustement initial de la vue
    myGlobe.pointOfView({ lat: lat, lng: lon, altitude: 2 });

    // Activation de la rotation lente automatique
    myGlobe.controls().autoRotate = true;
    myGlobe.controls().autoRotateSpeed = 0.5;
}