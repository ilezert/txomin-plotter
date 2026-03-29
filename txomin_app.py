import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Txomin v.33.6 - Master", page_icon="🔱", layout="wide")

# Verificación de Seguridad para la API Key
if "OPENWEATHER_API_KEY" in st.secrets:
    API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
else:
    st.error("API Key falta en los Secrets de Streamlit.")
    st.stop()

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")

# --- SIDEBAR: FACTOR CORRECTOR ---
st.sidebar.header("🛠️ KALIBRAZIOA / AJUSTE")
st.sidebar.write("Doitu satelitearen datuak:")
f_viento = st.sidebar.slider("Haizea / Viento (%)", 50, 150, 100) / 100.0
f_ola = st.sidebar.slider("Olatua / Ola (m)", -1.0, 1.0, 0.0, 0.1)

IMG_FONDO_MAR = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/fondo_cantabrico.jpg"

st.markdown(f"""
    <style>
        .stApp {{ background-image: url("{IMG_FONDO_MAR}"); background-size: cover; background-attachment: fixed; background-position: center; background-color: #011627; color: white; }}
        .main-card {{ background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); color: white; padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.2); position: relative; overflow: hidden; }}
        .metric-card {{ background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.3); }}
        .metric-card h2 {{ color: #FBBF24 !important; font-size: 2.2rem; margin: 0; font-weight: 800; }}
        .metric-card h3 {{ text-transform: uppercase; font-size: 0.9rem; color: #BAE6FD; margin-bottom: 5px; }}
        .big-arrow {{ font-size: 2.2rem; font-weight: bold; color: #FBBF24; }}
        .status-bar {{ height: 15px; width: 100%; position: absolute; top: 0; left: 0; }}
        .bg-green {{ background-color: #10B981; }}
        .bg-yellow {{ background-color: #FBBF24; }}
        .bg-red {{ background-color: #EF4444; }}
        .activity-badge {{ background: #1E293B; color: #FBBF24; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; display: inline-block; margin: 10px 0; border: 1px solid #FBBF24; }}
        .tide-alert {{ background: rgba(5, 150, 105, 0.85); border-radius: 10px; padding: 10px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 1px solid #34D399; font-size: 1.1rem; }}
        .scroll-wrapper {{ display: flex !important; flex-direction: row !important; overflow-x: auto !important; gap: 12px; padding: 10px 0 20px 0; width: 100%; }}
        .hour-card {{ flex: 0 0 auto; width: 165px; background: rgba(255, 255, 255, 0.95); border-top: 5px solid #0369A1; border-radius: 12px; padding: 12px; text-align: center; color: #1E293B !important; box-shadow: 2px 2px 8px rgba(0,0,0,0.2); }}
        .hour-card h4 {{ margin: 0 0 8px 0; color: #0369A1 !important; font-size: 1.1rem; font-weight: 800; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; }}
        .hour-card p {{ margin: 5px 0; font-size: 0.85rem; font-weight: 700; color: #334155 !important; display: flex; justify-content: space-between; align-items: center; }}
        .val {{ color: #0369A1; font-weight: 900; }}
        .rec-badge {{ background: #059669; color: white; border-radius: 6px; padding: 4px; margin-top: 8px; font-weight: bold; font-size: 0.8rem; display: block; }}
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 30px; color: #1E293B; overflow: hidden; border: 1px solid #E2E8F0; }}
        .card-content {{ padding: 20px; }}
        .rig-info {{ background: #F8FAFC; border-radius: 8px; padding: 12px; margin-top: 10px; border-left: 4px solid #FBBF24; color: #334155; font-size: 0.85rem; text-align: left; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA TÁCTICA ---
def flecha_desde(grados):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(grados / 45) % 8]

def flecha_hacia(grados):
    return ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"][round(grados / 45) % 8]

def generar_marea_aprox(fecha_target):
    dia = fecha_target.day
    return f"{(dia % 12) + 2:02d}:00", f"{((dia % 12) + 8) % 24:02d}:30", 50 + (dia * 3 % 45)

def get_semaforo_info(ola, viento_avg, viento_gust):
    if ola > 2.0 or viento_gust > 35: return "bg-red", "🛑 ARRISKUTSUA / PELIGRO"
    if viento_avg > 12 or ola > 1.5 or viento_gust > 25: return "bg-yellow", "🟡 KONTUZ / PRECAUCIÓN"
    return "bg-green", "🟢 EGOKIA / IDEAL"

def calcular_actividad(ola, viento, coef, temp, pres):
    puntos = 1
    if 60 <= coef <= 95: puntos += 1
    if 1010 <= pres <= 1025: puntos += 1
    if 13 <= temp <= 19: puntos += 1
    if 0.5 <= ola <= 1.5: puntos += 1
    if viento > 25: puntos -= 1
    score = max(1, min(5, puntos))
    return "⭐" * score + "🌑" * (5 - score)

@st.cache_data(ttl=600)
def fetch_master_data():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto&forecast_days=7"
        url_w = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl&timezone=auto&forecast_days=7"
        dm = requests.get(url_m).json()
        dw = requests.get(url_w).json()
        df = pd.DataFrame({
            'time': pd.to_datetime(dm['hourly']['time']).dt.tz_localize('UTC').dt.tz_convert(ZONA_HORARIA),
            'wave_h': dm['hourly']['wave_height'], 'wave_d': dm['hourly']['wave_direction'],
            'curr_v': dm['hourly']['ocean_current_velocity'], 'curr_d': dm['hourly']['ocean_current_direction'],
            'sst': dm['hourly']['sea_surface_temperature'],
            'wind_s': dw['hourly']['wind_speed_10m'], 'wind_g': dw['hourly']['wind_gusts_10m'],
            'wind_d': dw['hourly']['wind_direction_10m'], 'pres': dw['hourly']['pressure_msl']
        })
        return df
    except:
        return None

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.33.6 - Mutriku Tactical")
ahora_local = datetime.now(ZONA_HORARIA)

# CREAMOS LAS PESTAÑAS PRIMERO (Para que siempre sean visibles)
tab0, tab1, tab2, tab3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

# INTENTAMOS CARGAR LOS DATOS
df_master = fetch_master_data()

if df_master is not None:
    # Sincronización horaria exacta
    idx_ahora = (df_master['time'] >= ahora_local).idxmax()
    row_now = df_master.loc[idx_ahora]

    with tab0:
        ola_act = row_now['wave_h'] + f_ola
        v_avg = row_now['wind_s'] * 3.6 * f_viento
        v_gust = row_now['wind_g'] * 3.6 * f_viento
        c_cls, s_txt = get_semaforo_info(ola_act, v_avg, v_gust)
        p, b, coef = generar_marea_aprox(ahora_local)
        estrellas = calcular_actividad(ola_act, v_avg, coef, row_now['sst'], row_now['pres'])

        st.markdown(f"<div class='main-card'><div class='status-bar {c_cls}'></div><h1 style='margin-top:10px;'>MUTRIKU {ahora_local.strftime('%H:%M')}</h1><div style='font-weight:bold; color:#FBBF24;'>{s_txt}</div><div class='activity-badge'>Arrainen Jarduera: {estrellas}</div></div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ HAIZEA (M/R)</h3><h2>{v_avg:.0f}/{v_gust:.0f} <span class='big-arrow'>{flecha_desde(row_now['wind_d'])}</span></h2><p>km/h</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f} <span class='big-arrow'>{flecha_desde(row_now['wave_d'])}</span></h2><p>m</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ URA</h3><h2>{row_now['sst']:.1f}°</h2><p>{row_now['pres']:.0f} hPa</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 KORR.</h3><h2>{row_now['curr_v']*3.6:.1f} <span class='big-arrow'>{flecha_hacia(row_now['curr_d'])}</span></h2><p>km/h</p></div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='tide-alert'>⏳ Itsasgora {p} / Itsasbehera {b} (Coef: {coef})</div>", unsafe_allow_html=True)
        
        st.write("### ⏱️ GAURKO EBOLUZIOA (2 ORDURO)")
        html_c = "<div class='scroll-wrapper'>"
        for i in range(idx_ahora, min(idx_ahora + 16, len(df_master)), 2):
            r = df_master.iloc[i]
            v_a, v_g = r['wind_s'] * 3.6 * f_viento, r['wind_g'] * 3.6 * f_viento
            o, c = r['wave_h'] + f_ola, r
