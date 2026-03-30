import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.33.17", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# CSS Táctico (Diseño limpio y oscuro)
st.markdown("""
    <style>
        .stApp { background-color: #011627; color: white; }
        .main-title { color: #FBBF24; text-align: center; font-weight: 900; text-transform: uppercase; font-size: 2.5rem; margin-bottom: 20px; }
        .main-card { background: rgba(30, 41, 59, 0.8); padding: 25px; border-radius: 20px; border: 1px solid rgba(251, 191, 36, 0.4); text-align: center; margin-bottom: 25px; position: relative; overflow: hidden; }
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }
        .metric-card { background: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 15px; border: 1px solid rgba(255,255,255,0.1); text-align: center; height: 100%; }
        .m-label { color: #BAE6FD; font-size: 0.8rem; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 5px; }
        .m-val { color: #FBBF24; font-size: 2.5rem; font-weight: 900; display: block; line-height: 1; }
        .scroll-wrapper { display: flex; overflow-x: auto; gap: 12px; padding: 10px 0 20px 0; width: 100%; }
        .hour-card { flex: 0 0 auto; width: 160px; background: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 12px; text-align: center; color: #1E293B !important; border-top: 5px solid #0369A1; }
        .rig-info { background: #F1F5F9; border-radius: 8px; padding: 10px; margin-top: 5px; color: #334155; font-size: 0.85rem; border-left: 4px solid #FBBF24; text-align: left; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA TÁCTICA ---
def flecha(deg):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(deg / 45) % 8]

def generar_marea(f):
    dia = f.day
    return f"{(dia % 12) + 2:02d}:00", f"{((dia % 12) + 8) % 24:02d}:30", 50 + (dia * 3 % 45)

def get_semaforo(ola, v_avg, v_gust):
    if ola > 2.0 or v_gust > 35: return "bg-red", "🛑 ARRISKUTSUA / PELIGRO"
    if v_avg > 12 or ola > 1.5 or v_gust > 25: return "bg-yellow", "🟡 KONTUZ / PRECAUCIÓN"
    return "bg-green", "🟢 EGOKIA / IDEAL"

# --- 3. ALGORITMO DE CONSENSO (TRIPLE API) ---
def fetch_consensus():
    v_data, g_data, pres_data = [], [], []
    try:
        r = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,pressure_msl&timezone=auto", timeout=3).json()
        v_data.append(r['hourly']['wind_speed_10m'][0])
        g_data.append(r['hourly']['wind_gusts_10m'][0])
        pres_data.append(r['hourly']['pressure_msl'][0])
    except: pass
    try:
        api = st.secrets["OPENWEATHER_API_KEY"]
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={api}&units=metric", timeout=3).json()
        v_data.append(r['wind']['speed'] * 3.6)
        g_data.append(r['wind'].get('gust', r['wind']['speed']*1.3)*3.6)
        pres_data.append(r['main']['pressure'])
    except: pass
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
st.markdown("<h1 class='main-title'>🔱 Txomin Tactical</h1>", unsafe_allow_html=True)
t0, t1, t2, t3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

v_avg, v_gust, pres, sources = fetch_consensus()
mar = fetch_marine()

with t0:
    if mar:
        ola_h, sst = mar['hourly']['wave_height'][0], mar['hourly']['sea_surface_temperature'][0]
        c_v, c_d = mar['hourly']['ocean_current_velocity'][0]*3.6, mar['hourly']['ocean_current_direction'][0]
        p_t, b_t, coef = generar_marea(ahora_local)
        c_cls, s_txt = get_semaforo(ola_h, v_avg, v_gust)
        st.markdown(f"<div class='main-card'><div class='status-bar {c_cls}'></div><h2>MUTRIKU {ahora_local.strftime('%H:%M')}</h2><p style='color:#FBBF24; font-weight:bold;'>{s_txt}</p></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><span class='m-label'>Haizea (M/R)</span><span class='m-val'>{v_avg:.0f}/{v_gust:.0f}
