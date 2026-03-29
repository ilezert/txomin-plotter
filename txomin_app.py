import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.32.9 - Arrantza Masterra", page_icon="🔱", layout="wide")

API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")

IMG_FONDO_MAR = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/fondo_cantabrico.jpg"

st.markdown(f"""
    <style>
        .stApp {{ background-image: url("{IMG_FONDO_MAR}"); background-size: cover; background-attachment: fixed; background-position: center; background-color: #011627; color: white; }}
        .main-card {{ background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); color: white; padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.2); overflow: hidden; position: relative; }}
        .metric-card {{ background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.3); }}
        .metric-card h2 {{ color: #FBBF24 !important; font-size: 2.2rem; margin: 0; display: flex; align-items: center; justify-content: center; gap: 8px; }}
        .big-arrow {{ font-size: 2.2rem; font-weight: bold; color: #FBBF24; }}
        .med-arrow {{ font-size: 1.1rem; font-weight: bold; color: #0369A1; }}
        
        /* Semáforo y Actividad */
        .status-bar {{ height: 15px; width: 100%; position: absolute; top: 0; left: 0; }}
        .bg-green {{ background-color: #10B981; }}
        .bg-yellow {{ background-color: #FBBF24; }}
        .bg-red {{ background-color: #EF4444; }}
        
        .activity-badge {{ background: #1E293B; color: #FBBF24; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; display: inline-block; margin: 10px 0; border: 1px solid #FBBF24; }}
        
        /* CARRUSEL HORIZONTAL */
        .scroll-wrapper {{ display: flex !important; flex-direction: row !important; overflow-x: auto !important; gap: 12px; padding: 10px 0 20px 0; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; width: 100%; }}
        .scroll-wrapper::-webkit-scrollbar {{ height: 6px; }}
        .scroll-wrapper::-webkit-scrollbar-thumb {{ background: rgba(0,0,0,0.2); border-radius: 10px; }}
        
        .hour-card {{ flex: 0 0 auto; width: 155px; background: rgba(255, 255, 255, 0.95); border-top: 4px solid #0369A1; border-radius: 12px; padding: 10px; text-align: center; color: #1E293B !important; scroll-snap-align: start; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); }}
        .hour-card h4 {{ margin: 0 0 5px 0; color: #0369A1 !important; font-size: 1rem; font-weight: 800; border-bottom: 1px solid #E2E8F0; }}
        .hour-card p {{ margin: 3px 0; font-size: 0.8rem; font-weight: 600; color: #334155 !important; display: flex; justify-content: space-between; }}
        .rec-badge {{ background: #059669; color: white; border-radius: 6px; padding: 3px; margin-top: 5px; font-weight: bold; font-size: 0.75rem; display: block; }}
        
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 30px; color: #1E293B; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid #E2E8F0; }}
        .card-content {{ padding: 20px; }}
        .day-forecast-title {{ font-size: 1.4rem; font-weight: bold; color: #0369A1; text-transform: capitalize; margin: 0; }}
        
        /* Estilo Especies y Aparejos */
        .rig-info {{ background: #F8FAFC; border-radius: 8px; padding: 12px; margin-top: 10px; border-left: 4px solid #FBBF24; color: #334155; font-size: 0.9rem; }}
        .rig-title {{ font-weight: bold; color: #0F172A; display: block; margin-bottom: 5px; text-transform: uppercase; border-bottom: 1px solid #CBD5E1; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA TÁCTICA ---
def flecha_desde(grados):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(grados / 45) % 8]

def flecha_hacia(grados):
    return ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"][round(grados / 45) % 8]

def generar_marea_aprox(fecha_target):
    dia = fecha_target.day
    return f"{(dia % 12) + 2:02d}:{(dia * 7 % 60):02d}", f"{((dia % 12) + 8) % 24:02d}:{(dia * 7 % 60 + 15) % 60:02d}",
