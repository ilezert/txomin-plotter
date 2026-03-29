import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.33.8", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# CSS Profesional (A prueba de errores de sintaxis)
st.markdown("""
    <style>
        .stApp { background-color: #011627; color: white; }
        .main-card { background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.2); position: relative; overflow: hidden; }
        .metric-card { background: rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.2); }
        .metric-card h2 { color: #FBBF24 !important; font-size: 2.2rem; margin: 0; font-weight: 800; }
        .metric-card h3 { text-transform: uppercase; font-size: 0.9rem; color: #BAE6FD; }
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }
        .activity-badge { background: #1E293B; color: #FBBF24; padding: 6px 15px; border-radius: 20px; font-weight: bold; border: 1px solid #FBBF24; margin: 10px 0; display: inline-block; }
        .scroll-wrapper { display: flex !important; flex-direction: row !important; overflow-x: auto !important; gap: 12px; padding: 10px 0 20px 0; width: 100%; }
        .hour-card { flex: 0 0 auto; width: 160px; background: rgba(255,255,255,0.95); border-radius: 12px; padding: 10px; text-align: center; color: #1E293B !important; border-top: 5px solid #0369A1; }
        .hour-card h4 { margin: 0 0 5px 0; color: #0369A1 !important; font-weight: 800; border-bottom: 1px solid #DDD; }
        .hour-card p { margin: 4px 0; font-size: 0.8rem; font-weight: 700; display: flex; justify-content: space-between; }
        .val-blue { color: #0369A1; }
        .day-forecast-card { background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 25px; color: #1E293B; overflow: hidden; border: 1px solid #E2E8F0; }
        .rig-info { background: #F1F5F9; border-radius: 8px; padding: 10px; margin-top: 5px; color: #334155; font-size: 0.85rem; border-left: 4px solid #FBBF24; text-align: left; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE MOTOR ---
def flecha_desde(grados):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(grados / 45) % 8]

def flecha_hacia(grados):
    return ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"][round(grados / 45) % 8]

def generar_marea_aprox(fecha):
    dia = fecha.day
    return f"{(dia % 12) + 2:02d}:00", f"{((dia % 12) + 8) % 24:02d}:30", 50 + (dia * 3 % 45)

def get_semaforo(ola, v_avg, v_gust):
    if ola > 2.0 or v_gust > 35: return "bg-red", "🛑 PELIGRO"
    if v_avg > 12 or ola > 1.5 or v_gust > 25: return "bg-yellow", "🟡 PRECAUCIÓN"
    return "bg-green", "🟢 IDEAL"

def get_actividad(ola, viento, coef, temp, pres):
    p = 1
    if 60 <= coef <= 95: p += 1
    if 1010 <= pres <= 1025: p += 1
    if 13 <= temp <= 19: p += 1
    if 0.5 <= ola <= 1.5: p += 1
    if viento > 25: p -= 1
    score = max(1
