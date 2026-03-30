import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.33.16", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# CSS Táctico Premium (Sin Sidebar, Diseño Limpio)
st.markdown("""
    <style>
        .stApp { background-color: #011627; color: white; }
        .main-title { color: #FBBF24; text-align: center; font-weight: 900; text-transform: uppercase; font-size: 2.5rem; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
        .main-card { background: rgba(30, 41, 59, 0.8); padding: 25px; border-radius: 20px; border: 1px solid rgba(251, 191, 36, 0.4); text-align: center; margin-bottom: 25px; position: relative; overflow: hidden; }
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }
        .metric-card { background: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 15px; border: 1px solid rgba(255,255,255,0.1); text-align: center; height: 100%; }
        .m-label { color: #BAE6FD; font-size: 0.8rem; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 5px; }
        .m-val { color: #FBBF24; font-size: 2.5rem; font-weight: 900; display: block; line-height: 1; }
        .badge { background: #1E293B; color: #FBBF24; padding: 8px 15px; border-radius: 25px; font-weight: bold; font-size: 1rem; border: 1px solid #FBBF24; display: inline-block; margin: 10px 0; }
        .scroll-wrapper { display: flex; overflow-x: auto; gap: 12px; padding: 10px 0 20px 0; width: 100%; scroll-snap-type: x mandatory; }
        .hour-card { flex: 0 0 auto; width: 160px; background: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 12px; text-align: center; color: #1E293B !important; border-top: 5px solid #0369A1; scroll-snap-align: start; }
        .hour-card h4 { margin: 0 0 5px 0; color: #0369A1 !important; font-weight: 800; border-bottom: 1px solid #DDD; }
        .rig-info { background: #F1F5F9; border-radius: 8px; padding: 10px; margin-top: 5px; color: #334155; font-size: 0.85rem; border-left: 4px solid #FBBF24; text-align: left; }
        .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; font-size: 1.1rem; }
        .stTabs [aria-selected="true"] { color: #FBBF24 !important; border-bottom-color: #FBBF24 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA TÁCTICA ---
def flecha(deg):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(deg / 45) % 8]

def generar_marea(f):
    dia = f.day
    plea = f"{(dia % 12) + 2:02d}:00"
    baja = f"{((dia % 12) + 8) % 24:02d}:30"
    coef = 50 + (dia * 3 % 45)
    return plea, baja, coef

def get_semaforo(ola, v_avg, v_gust):
    if ola > 2.0 or v_gust > 35: return "bg-red", "🛑 ARRISKUTSUA / PELIGRO"
    if v_avg > 12 or ola > 1.5 or v_gust > 25: return "bg-yellow", "🟡 KONTUZ / PRECAUCIÓN"
    return "bg-green", "🟢 EGOKIA / IDEAL"

def get_actividad(ola, viento, coef, temp, pres):
    p = 1
    if 60 <= coef <= 95: p += 1
    if 1010 <= pres <= 1025: p += 1
    if 13 <= temp <= 19: p += 1
    if 0.5 <= ola <= 1.5: p += 1
    if viento > 25: p -= 1
    score = max(1, min(5, p))
    return "⭐" * score + "🌑" * (5 - score)

# --- 3. ALGORITMO DE CONSENSO (TRIPLE API) ---
def fetch_consensus():
    v_data, g_data, pres_data = [], [], []
    # A. Open-Meteo
    try:
        r = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,pressure_msl&timezone=auto", timeout=3).json()
        v_data.append(r['hourly']['wind_speed_10m'][0])
        g_data.append(r['hourly']['wind_gusts_10m'][0])
        pres_data.append(r['hourly']['pressure_msl'][0])
    except: pass
    # B. OpenWeather
    try:
        api = st.secrets["OPENWEATHER_API_KEY"]
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={api}&units=metric", timeout=3).json()
        v_data.append(r['wind']['speed'] * 3.6)
        g_data.append(r['wind'].get('gust', r['wind']['speed']*1.3)*3.6)
        pres_data.append(r['main']['pressure'])
    except: pass
    # C. WeatherAPI
    try:
        api = st.secrets.get("WEATHERAPI_KEY", "")
        r = requests.get(f"http://api.weatherapi.com/v1/current.json?key={api}&q={LAT_MUTRIKU},{LON_MUTRIKU}", timeout=3).json()
        v_data.append(r['current']['wind_kph'])
        g_data.append(r['current']['gust_kph'])
        pres_data.append(r['current']['pressure_mb'])
    except: pass

    if v_data:
        return sum(v_data)/len(v_data), sum(g_data)/len(g_data), sum(pres_data)/len(pres_data), len(v_data)
    return 0, 0, 1013, 0

@st.cache_data(ttl=600)
def fetch_marine():
    try:
        u = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto&forecast_days=6"
        return requests.get(u, timeout=5).json()
    except: return None

# --- 4. INTERFAZ ---
st.markdown("<h1 class='main-title'>🔱 Txomin - Mutriku Tactical</h1>", unsafe_allow_html=True)
t0, t1, t2, t3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

v_avg, v_gust, pres, sources = fetch_consensus()
mar = fetch_marine()

with t0:
    if mar:
        idx = 0 # Simplificado para ORAIN
        ola_h, sst = mar['hourly']['wave_height'][0], mar['hourly']['sea_surface_temperature'][0]
        c_v, c_d = mar['hourly']['ocean_current_velocity'][0]*3.6, mar['hourly']['ocean_current_direction'][0]
        p_t, b_t, coef = generar_marea(ahora_local)
        c_cls, s_txt = get_semaforo(ola_h, v_avg, v_gust)
        stars = get_actividad(ola_h, v_avg, coef, sst, pres)

        st.markdown(f"""
            <div class='main-card'>
                <div class='status-bar {c_cls}'></div>
                <h2 style='margin:0;'>MUTRIKU {ahora_local.strftime('%H:%M')}</h2>
                <p style='color:#FBBF24; font-weight:bold; margin-top:10px;'>{s_txt}</p>
                <div class='badge'>Jarduera: {stars} | Consenso: {sources} APIak</div>
            </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='metric-card'><span class='m-label'>🌬️ Haizea (M/R)</span><span class='m-val'>{v_avg:.0f}/{v_gust:.0f}</span><p>km/h</p></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-card'><span class='m-label'>🌊 Olatua</span><span class='m-val'>{ola_h:.1f}</span><p>Metro</p></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-card'><span class='m-label'>🌡️ Ura / Presioa</span><span class='m-val'>{sst:.1f}°</span><p>{pres:.0f} hPa</p></div>", unsafe_allow_html=True)
        with m4: st.markdown(f"<div class='metric-card'><span class='m-label'>💧 Korrontea</span><span class='m-val'>{c_v:.1f}</span><p>{flecha(c_d)} km/h</p></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='main-card' style='background:rgba(16,185,129,0.1);'><p style='margin:0; font-weight:bold;'>⏳ Plea: {p_t} | Baja: {b_t} | Coef: {coef}</p></div>", unsafe_allow_html=True)

        st.write("### ⏱️ Hurrengo orduak")
        h_html = "<div class='scroll-wrapper'>"
        for i in range(2, 16, 2):
            h_html += f"<div class='hour-card'><h4>{(ahora_local.hour+i)%24:02d}:00</h4><p>🌊 Olatua <span style='color:#0369A1'>{mar['hourly']['wave_height'][i]:.1f}m</span></p><p>💧 Korr. <span style='color:#0369A1'>{mar['hourly']['ocean_current_velocity'][i]*3.6:.1f}</span></p></div>"
        st.markdown(h_html + "</div>", unsafe_allow_html=True)
    else:
        st.error("❌ Satelite konexio errorea. APIak egiaztatu.")

with t1:
    if mar:
        hoy = ahora_local.date()
        for i in range(1, 5):
            d = hoy + timedelta(days=i)
            p, b, c = generar_marea(d)
            st.markdown(f"""
                <div class='main-card' style='text-align:left; padding:15px;'>
                    <h4 style='margin:0; color:#FBBF24;'>{d.strftime('%A, %b %d')}</h4>
                    <p style='margin:5px 0;'>🔼 Plea: {p} | 🔽 Baja: {b} | Coef: {c}</p>
                </div>
            """, unsafe_allow_html=True)

with t2:
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    st_folium(m, width="100%", height=500, key="plot_final")

with t3:
    st.header("🐟 Arrainak, Apailuak eta Tips")
    e_list = [
        ("SARGOA", "Aparraren erregea. Itsasoa 0.8m-1.5m onena.", "Línea 0.35 / Bua 20g / Bajo 0.30mm Fluoroc.", "Tip: Arroketako aparretan izkira biziarekin ibili."),
        ("LUPINA", "Spinning señueloekin egunsentian.", "Trenzado 0.18 / Bajo 0.40mm / Grapa rápida.", "Tip: Mugimendu handiko señueloak erabili aparretan."),
        ("TXIPIROIA", "Poterak 2.0-2.5 ilunabarrean.", "Trenzado 0.10 / Bajo 0.22mm Fluoroc.", "Tip: Mugimendu oso leunak egin potera altxatzean."),
        ("DENTOIA", "Hondo handiak, zoka beharrezkoa.", "Trenzado 0.30 / Bajo 0.70mm / Tándem.", "Tip: Txibia bizia da beitari onena."),
        ("URRABURUA", "Hondarrezko hondo mistoetan.", "Corredizo / Bajo 3m (0.33mm) / Amu fuerte.", "Tip: Karramarroa beita gisa oso eraginkorra da."),
        ("TXITXARROA", "Portuetan gauez luma zuriekin.", "Sabiki / Bajo 0.30mm / Plomo 50g.", "Tip: Argi fokuetatik hurbil arrantzatu."),
        ("MOXARRA", "Harri inguruetan zizarearekin.", "0.30mm / Bua ligera / Bajo 0.22mm.", "Tip: Amu oso txikiak eta zizare korearra erabili."),
        ("BARBINA", "Salmonetea hondarretan.", "Chambel / Amuak Nº 12 / Coreana.", "Tip: Beita hondo-hondoan egon behar da."),
        ("KABRARROKA", "Harri puruan, kontuz arantzekin.", "Paternoster / Madre 0.45 / Bajo 0.35mm.", "Tip: Txipiroi tirekin oso ondo sartzen da."),
        ("BOGA", "Ogi apurrak eta amu txikia.", "0.18mm / Bua pluma / Amua Nº 14.", "Tip: Umeentzako arrantza dibertigarria portuan.")
    ]
    col1, col2 = st.columns(2)
    for i,
