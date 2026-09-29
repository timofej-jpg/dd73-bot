const tg = window.Telegram.WebApp;
tg.expand();

let userIsPro = false;
let map;
let currentLang = localStorage.getItem("app_lang") || "ru";

// ТЕKСТЫ И ПЕРЕВОДЫ (i18n)
const translations = {
    ru: {
        loading: "Загрузка картографии...",
        blocked_title: "🚫 Доступ ограничен",
        blocked_desc: "Сервис недоступен в вашем регионе или на запрещенных территориях.",
        forecast_title: "Прогнозы активности",
        avg_bite: "Средний клев сегодня",
        pro_lock: "🔒 Подробный почасовой прогноз доступен в PRO версии",
        premium_desc: "Доступ к карте глубин, прогнозам на 14 дней и базе водоемов без ограничений.",
        activate_pro: "Активировать PRO",
        profile_sub: "Управление профилем",
        lang_title: "Язык приложения / Мова",
        locations_title: "Мои локации",
        loc_points: "Точки",
        loc_nets: "Перемёты",
        loc_trolling: "Троллинг",
        catch_title: "Мои уловы",
        add_catch: "➕ Добавить улов",
        nav_map: "Карта",
        nav_forecast: "Прогнозы",
        nav_premium: "Премиум",
        nav_profile: "Мне",
        sea_type: "Черное море / Лиман",
        fresh_type: "Пресноводный ставок / Река",
        catch_alert: "Для добавления улова выберите точку на карте!"
    },
    uk: {
        loading: "Завантаження картографії...",
        blocked_title: "🚫 Доступ обмежено",
        blocked_desc: "Сервіс недоступний у вашому регіоні або на заборонених територіях.",
        forecast_title: "Прогнози активности",
        avg_bite: "Середній клювання сьогодні",
        pro_lock: "🔒 Детальний погодинний прогноз доступний у PRO версії",
        premium_desc: "Доступ до карти глибин, прогнозів на 14 днів та бази водойм без обмежень.",
        activate_pro: "Активувати PRO",
        profile_sub: "Управління профілем",
        lang_title: "Мова застосунку / Language",
        locations_title: "Мої локації",
        loc_points: "Точки",
        loc_nets: "Перемети",
        loc_trolling: "Тролінг",
        catch_title: "Мої улови",
        add_catch: "➕ Додати улов",
        nav_map: "Карта",
        nav_forecast: "Прогнози",
        nav_premium: "Преміум",
        nav_profile: "Профіль",
        sea_type: "Чорне море / Лиман",
        fresh_type: "Прісноводний ставок / Річка",
        catch_alert: "Для додавання улову виберіть точку на карті!"
    },
    en: {
        loading: "Loading maps...",
        blocked_title: "🚫 Access Restricted",
        blocked_desc: "Service is unavailable in your region or restricted territories.",
        forecast_title: "Activity Forecasts",
        avg_bite: "Average bite rate today",
        pro_lock: "🔒 Detailed hourly forecast available in PRO version",
        premium_desc: "Access to depth maps, 14-day forecasts and unlimited waterbody database.",
        activate_pro: "Activate PRO",
        profile_sub: "Profile Management",
        lang_title: "App Language",
        locations_title: "My Locations",
        loc_points: "Spots",
        loc_nets: "Nets",
        loc_trolling: "Trolling",
        catch_title: "My Catches",
        add_catch: "➕ Add Catch",
        nav_map: "Map",
        nav_forecast: "Forecast",
        nav_premium: "Premium",
        nav_profile: "Me",
        sea_type: "Black Sea / Estuary",
        fresh_type: "Freshwater Pond / River",
        catch_alert: "Select a spot on the map to add a catch!"
    }
};

// Инициализация
document.addEventListener("DOMContentLoaded", async () => {
    applyLanguage(currentLang);
    await checkGeoLocation();
    initMap();
    initNavigation();

    document.getElementById("loader-screen").classList.add("hidden");
});

// Переключение языка
function changeLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("app_lang", lang);
    applyLanguage(lang);
}

function applyLanguage(lang) {
    const dict = translations[lang] || translations.ru;
    
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (dict[key]) {
            el.innerText = dict[key];
        }
    });

    // Подсветить активную кнопку языка
    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.classList.remove("active");
        if (btn.getAttribute("onclick").includes(`'${lang}'`)) {
            btn.classList.add("active");
        }
    });
}

// Проверка гео/IP на РФ
async function checkGeoLocation() {
    try {
        const res = await fetch("https://ipapi.co/json/");
        const data = await res.json();
        
        if (data.country_code === "RU") {
            document.getElementById("block-screen").classList.remove("hidden");
        }
    } catch (e) {
        console.log("Geo check skipped");
    }
}

// Настройка карты
function initMap() {
    map = L.map("map").setView([46.4825, 30.7233], 10);

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19
    }).addTo(map);

    // Маска заблокированной территории
    fetch("https://raw.githubusercontent.com/johan/world.geo.json/master/countries/RUS.geo.json")
        .then(res => res.json())
        .then(data => {
            L.geoJSON(data, {
                style: {
                    fillColor: "#4a4a4a",
                    fillOpacity: 0.7,
                    color: "#222",
                    weight: 1
                }
            }).addTo(map);
        });

    map.on("click", (e) => {
        analyzeLocation(e.latlng.lat, e.latlng.lng);
    });
}

// Определение водоема и рыбы
function analyzeLocation(lat, lng) {
    const card = document.getElementById("water-info");
    const nameEl = document.getElementById("water-name");
    const typeEl = document.getElementById("water-type");
    const fishEl = document.getElementById("fish-list");
    const dict = translations[currentLang] || translations.ru;

    card.classList.remove("hidden");

    let type = dict.sea_type;
    let fishes = ["Бычок", "Камбала", "Кефаль", "Сарган", "Ставрида"];

    if (lat > 46.5) {
        type = dict.fresh_type;
        fishes = ["Карп", "Карась", "Судак", "Щука", "Окунь", "Толстолобик"];
    }

    nameEl.innerText = `${lat.toFixed(3)}, ${lng.toFixed(3)}`;
    typeEl.innerText = type;
    fishEl.innerHTML = fishes.map(f => `<span class="tag">🐟 ${f}</span>`).join("");
}

// Навигация
function initNavigation() {
    const buttons = document.querySelectorAll(".nav-btn");
    const tabs = document.querySelectorAll(".tab-content");

    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");

            buttons.forEach(b => b.classList.remove("active"));
            tabs.forEach(t => t.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(targetTab).classList.add("active");

            if (targetTab === "tab-map" && map) {
                setTimeout(() => map.invalidateSize(), 100);
            }
        });
    });
}

function buyPro() {
    tg.sendData(JSON.stringify({ action: "buy_pro" }));
}

function addCatch() {
    const dict = translations[currentLang] || translations.ru;
    tg.showAlert(dict.catch_alert);
}
