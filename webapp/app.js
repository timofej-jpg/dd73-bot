const tg = window.Telegram?.WebApp;
if(tg) { tg.expand(); }

let map, depthLayer, userMarker, selectedPointMarker;
let selectedCoords = { lat: 46.56, lng: 30.85, name: "Фонтанка / Одесса" };

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    loadRealWeatherData(selectedCoords.lat, selectedCoords.lng);
});

// 1. ИНИЦИАЛИЗА КАРТЫ С ЭХОЛОТОМ И ВЫБОРОМ ТОЧКИ
function initMap() {
    map = L.map("map", { zoomControl: false }).setView([selectedCoords.lat, selectedCoords.lng], 12);

    // Базовая спутниковая карта
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18
    }).addTo(map);

    // Рабочий слой глубин и морской батиметрии (OpenSeaMap Seamarks + Bathymetry)
    depthLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
        maxZoom: 18,
        opacity: 0.9
    }).addTo(map);

    // КЛИК ПО КАРТЕ: Выбор конкретной точки
    map.on('click', function(e) {
        const lat = e.latlng.lat.toFixed(4);
        const lng = e.latlng.lng.toFixed(4);
        
        selectedCoords = { lat, lng, name: `${lat}°N, ${lng}°E` };

        // Анимация перемещения
        map.flyTo(e.latlng, map.getZoom(), { duration: 1.0 });

        if (selectedPointMarker) map.removeLayer(selectedPointMarker);
        
        selectedPointMarker = L.marker([lat, lng]).addTo(map)
            .bindPopup(`<b>🎯 Выбрана точка</b><br>Широта: ${lat}<br>Долгота: ${lng}<br><i>Загрузка данных...</i>`)
            .openPopup();

        // Обновляем панель локации во всех вкладках
        document.querySelectorAll(".loc-display").forEach(el => el.innerText = selectedCoords.name);
        
        // Пересчитываем реальные показатели погоды и клева для точки
        loadRealWeatherData(lat, lng);
    });
}

function locateUser() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((pos) => {
            const lat = pos.coords.latitude.toFixed(4);
            const lng = pos.coords.longitude.toFixed(4);
            
            selectedCoords = { lat, lng, name: "Мое местоположение" };
            map.flyTo([lat, lng], 14, { duration: 1.2 });

            if (userMarker) map.removeLayer(userMarker);
            userMarker = L.circleMarker([lat, lng], {
                radius: 8, fillColor: "#00d2ff", color: "#fff", weight: 2, fillOpacity: 1
            }).addTo(map).bindPopup("<b>📍 Вы здесь</b>").openPopup();

            document.querySelectorAll(".loc-display").forEach(el => el.innerText = selectedCoords.name);
            loadRealWeatherData(lat, lng);
        });
    }
}

// 2. ПОЛУЧЕНИЕ РЕАЛЬНЫХ ДАННЫХ ПОГОДЫ И КЛЕВА ПО КООРДИНАТАМ (Open-Meteo API)
async function loadRealWeatherData(lat, lng) {
    try {
        const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current_weather=true&hourly=surface_pressure,relativehumidity_2m`);
        const data = await res.json();
        
        if (data && data.current_weather) {
            const temp = Math.round(data.current_weather.temperature);
            const wind = data.current_weather.windspeed;
            const pressure = Math.round(data.hourly.surface_pressure[0] * 0.750062); // hPa в мм рт. ст.

            document.getElementById("val-temp").innerText = `${temp > 0 ? '+' : ''}${temp}°C`;
            document.getElementById("val-wind").innerText = `${wind} км/ч`;
            document.getElementById("val-press").innerText = `${pressure} мм рт.ст.`;

            // Расчет реального индекса клева на основе давления и ветра
            let biteScore = 80;
            if (pressure < 745 || pressure > 765) biteScore -= 20;
            if (wind > 20) biteScore -= 25;
            
            document.getElementById("bite-val").innerText = `${Math.max(10, biteScore)}%`;
        }
    } catch (e) {
        console.error("Ошибка получения метеоданных:", e);
    }
}

// 3. ПОКУПКА ПОДПИСКИ С ОПЛАТОЙ ЧЕРЕЗ TELEGRAM STARS
function buyProSubscription() {
    if (!tg) {
        alert("Запустите WebApp внутри Telegram!");
        return;
    }

    //1. Отправляем событие бэкенду (Python / Node.js боту)
    tg.sendData(JSON.stringify({
        action: "create_invoice",
        item: "pro_subscription",
        stars: 500
    }));

    //2. Альтернативный вариант (если у вас готова прямая ссылка на оплату invoice)
    // tg.openInvoice("https://t.me/$INVOICE_LINK", function(status) {
    //     if (status === 'paid') tg.showAlert('Оплата прошла успешно!');
    // });
}

function switchMainTab(tabId, el) {
    document.querySelectorAll(".tab-view").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    document.getElementById(tabId).classList.add("active");
    el.classList.add("active");
    if(tabId === 'tab-map' && map) setTimeout(() => map.invalidateSize(), 100);
}

function switchSubForecast(sub, el) {
    document.querySelectorAll(".sub-content").forEach(s => s.classList.add("hidden"));
    document.querySelectorAll(".sub-btn").forEach(b => b.classList.remove("active"));
    document.getElementById("sub-" + sub).classList.remove("hidden");
    el.classList.add("active");
}
