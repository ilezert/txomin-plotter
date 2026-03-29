import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.30 - Torre de Control", page_icon="🔱", layout="wide")

API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ARCHIVO_MARCAS = "marcas_exito.csv"

# Estilos Visuales Pro (Pantalla Inicial)
st.markdown("""
    <style>
        .main-card { background-color: #0369A1; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
        .metric-card { background-color: white; border: 1px solid #E2E8F0; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); }
        .status-bad { color: #EF4444; font-weight: bold; }
        .status-good { color: #10B981; font-weight: bold; }
        .eval-box { background-color: #F8FAFC; border-left: 5px solid #0369A1; padding: 15px; border-radius: 8px; margin-top: 10px; color: #1E293B; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES DE APOYO ---
def dir_viento_real(grados):
    dirs = ["N ↓", "NE ↙", "E ←", "SE ↖", "S ↑", "SO ↗", "O →", "NO ↘"]
    return dirs[round(grados / 45) % 8]

def dir_corr_real(grados):
    dirs = ["N ↑", "NE ↗", "E →", "SE ↘", "S ↓", "SO ↙", "O ←", "NO ↖"]
    return dirs[round(grados / 45) % 8]

def evaluar_pesca(ola, viento, coef):
    puntos = 10
    if ola > 2.0: puntos -= 5
    if viento > 25: puntos -= 3
    if 0.8 < ola < 1.5: puntos += 2 # Ideal para sargo
    
    nota = max(0, min(10, puntos))
    if nota > 7: return f"🔥 EXCELENTE ({nota}/10)", "Día perfecto. Las condiciones son estables."
    elif nota > 4: return f"⚖️ REGULAR ({nota}/10)", "Se puede pescar, pero busca zonas de abrigo."
    return f"⚠️ MALA ({nota}/10)", "Mar complicada. Precaución fuera del puerto."

def recomendacion_especie(ola, viento, coef):
    if ola > 0.8 and ola < 1.8: return "🐟 SARGO", "Busca las puestas con espuma. Cebo: Gamba."
    if ola < 0.7 and viento < 12: return "🦑 CHIPIRÓN", "Mar plato. Poteras de 2.0 en zonas de calma."
    if viento >= 10 and ola < 1.3: return "🐠 CHICHARRO", "Viento rizando el agua. Ideal para cacea ligera."
    return "🦂 CABRARROCA", "Pescado de fondo en las piedras marcadas."

@st.cache_data(ttl=600)
def fetch_data():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/weather?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.30.0 - Torre de Control Mutriku")

tab0, tab1, tab2 = st.tabs(["⚓ ESTADO DEL MAR", "📊 PREVISIÓN DETALLADA", "🗺️ MAPA IHM"])

dm_m, dw_now = fetch_data()

# --- PESTAÑA INICIAL: TORRE DE CONTROL ---
with tab0:
    if dm_m and 'hourly' in dm_m and dw_now:
        # Datos actuales (primera hora del índice)
        ola_act = dm_m['hourly']['wave_height'][0]
        ola_dir = dm_m['hourly']['wave_direction'][0]
        temp_agua = dm_m['hourly']['sea_surface_temperature'][0]
        v_corr = dm_m['hourly']['ocean_current_velocity'][0] * 3.6
        d_corr = dir_corr_real(dm_m['hourly']['ocean_current_direction'][0])
        v_viento = dw_now['wind']['speed'] * 3.6
        d_viento = dir_viento_real(dw_now['wind']['deg'])
        
        st.markdown(f"""
            <div class='main-card'>
                <h1 style='margin:0;'>{datetime.now().strftime('%H:%M')} - PUERTO DE MUTRIKU</h1>
                <p style='font-size:1.2rem; opacity:0.9;'>Condiciones actuales en tiempo real</p>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><h3>🌬️ VIENTO</h3><h2 style='color:#0369A1;'>{v_viento:.1f} km/h</h2><p>{d_viento}</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2 style='color:#0369A1;'>{ola_act:.1f} m</h2><p>Dir: {ola_dir}°</p></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><h3>🌡️ AGUA</h3><h2 style='color:#0369A1;'>{temp_agua:.1f} °C</h2><p>Temp. Superficie</p></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-card'><h3>💧 CORRIENTE</h3><h2 style='color:#0369A1;'>{v_corr:.1f} km/h</h2><p>{d_corr}</p></div>", unsafe_allow_html=True)

        st.divider()
        
        # Evaluación de Pesca
        eval_txt, eval_desc = evaluar_pesca(ola_act, v_viento, 80)
        esp_nombre, esp_tip = recomendacion_especie(ola_act, v_viento, 80)
        
        col_eval, col_esp = st.columns(2)
        with col_eval:
            st.subheader("📈 Actividad de Pesca")
            st.markdown(f"""<div class='eval-box'>
                <h2 style='margin:0;'>{eval_txt}</h2>
                <p>{eval_desc}</p>
            </div>""", unsafe_allow_html=True)
            
        with col_esp:
            st.subheader("🎯 Especie Recomendada")
            st.markdown(f"""<div class='eval-box'>
                <h2 style='margin:0; color:#059669;'>{esp_nombre}</h2>
                <p><b>Tip:</b> {esp_tip}</p>
            </div>""", unsafe_allow_html=True)
    else:
        st.warning("Cargando datos del satélite...")

# --- EL RESTO DE TABS (Previsión y Mapa) se mantienen igual que v.29 ---
# [Aquí iría el código de las mareas y el mapa que ya tienes]
