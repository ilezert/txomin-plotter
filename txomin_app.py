import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- 1. CONFIGURACIÓN Y ESTILO WINDFINDER ---
st.set_page_config(page_title="Txomin v.40 - Tactical", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

st.markdown("""
    <style>
        .stApp { background-color: #0B121E; color: #E2E8F0; }
        .main-card { background: #161E2E; padding: 20px; border-radius: 12px; border: 1px solid #1E293B; margin-bottom: 20px; position: relative; }
        .status-bar { height: 8px; width: 100%; position: absolute; top: 0; left: 0; border-radius: 12px 12px 0 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }
        .metric-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 15px; }
        .metric-box { background: #1F2937; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #374151; }
        .m-label { color: #9CA3AF; font-size: 0.75rem; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 5px; }
        .m-val { color: #FBBF24; font-size: 2rem; font-weight: 800; display: block; }
        .scroll-wrapper { display: flex; overflow-x: auto; gap: 8px; padding: 10px 0; }
        .hour-card { flex: 0 0 auto; width: 130px; background: #1F2937; border-radius: 8px; padding: 10px; text-align: center; border-bottom: 4px solid #3B82F6; }
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS (CONSENSO 3 APIs) ---
def fetch_consensus():
    v_data, g_data = [], []
    # API 1: Open-Meteo
    try:
        r1 = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m&timezone=auto", timeout=3).json()
        v_data.append(r1['hourly']['wind_speed_10m'][0])
        g_data.append(r1['hourly']['wind_gusts_10m'][0])
    except: pass
    # API 2: OpenWeather
    try:
        api_ow = st.secrets["OPENWEATHER_API_KEY"]
        r2 = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={api_ow}&units=metric", timeout=3).json()
        v_data.append(r2['wind']['speed'] * 3.6)
        g_data.append(r2['wind'].get('gust', r2['wind']['speed'] * 1.3) * 3.6)
    except: pass
    # API 3: WeatherAPI
    try:
        api_wa = st.secrets["WEATHERAPI_KEY"]
        r3 = requests.get(f"http://api.weatherapi.com/v1/current.json?key={api_wa}&q={LAT_MUTRIKU},{LON_MUTRIKU}", timeout=3).json()
        v_data.append(r3['current']['wind_kph'])
        g_data.append(r3['current']['gust_kph'])
    except: pass

    if v_data:
        return sum(v_data)/len(v_data), sum(g_data)/len(g_data), len(v_data)
    return 0, 0, 0

@st.cache_data(ttl=600)
def fetch_marine():
    try:
        u = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,sea_surface_temperature&timezone=auto"
        return requests.get(u, timeout=5).json()
    except: return None

# --- 3. INTERFAZ: PESTAÑA ORAIN ---
st.markdown("<h1 style='color:#FBBF24; text-align:center;'>🔱 TXOMIN TACTICAL</h1>", unsafe_allow_html=True)

# Creamos el esqueleto de pestañas
tab0, tab1, tab2, tab3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

v_avg, v_gust, n_api = fetch_consensus()
mar = fetch_marine()
