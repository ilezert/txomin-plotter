import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Txomin v33.2 - Master Taktikoa", page_icon="🔱", layout="wide")

# Seguridad para la API Key
if "OPENWEATHER_API_KEY" in st.secrets:
    API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
else:
    st.error("API Key falta en los Secrets.")
    st.stop()

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")

# --- SIDEBAR: FACTOR CORRECTOR ---
st.sidebar.header("🛠️ KALIBRAZIOA / AJUSTE")
st.sidebar.write("Doitu satelitearen datuak errealitatera egokitzeko:")
f_viento = st.sidebar.slider("Haizea / Viento (%)", 50, 150, 100) / 100.0
f_ola = st.sidebar.slider("Olatua / Ola (m)", -1.0, 1.0, 0.0, 0.1)

IMG_FONDO_MAR = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/fondo_cantabrico.jpg"

st.markdown(f"""
    <style>
        .stApp {{ background-image: url("{IMG_FONDO_MAR}"); background-size: cover; background-attachment: fixed; background-position: center; background-color: #011627; color: white; }}
        .main-card {{ background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); color: white; padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.2); overflow: hidden; position: relative; }}
        .metric-card {{ background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.3); }}
        .metric-card h2 {{ color: #FBBF24 !important; font-size: 2.5rem; margin: 0; display: flex; align-items: center; justify-content: center; gap: 8px; font-weight: 800; }}
        .metric-card h3 {{ text-transform: uppercase; font-size: 0.9rem; color: #BAE6FD; margin-bottom: 5px; }}
        .big-arrow {{ font-size: 2.5rem; font-weight: bold; color: #FBBF24; }}
        .status-bar {{ height: 15px; width: 100%; position: absolute; top: 0; left: 0; }}
        .bg-green {{ background-color: #10B981; }}
        .bg-yellow {{ background-color: #FBBF24; }}
        .bg-red {{ background-color: #EF4444; }}
        .activity-badge {{ background: #1E293B; color: #FBBF24; padding: 8px 18px; border-radius: 25px; font-weight: bold; display: inline-block; margin: 15px 0; border: 2px solid #FBBF24; }}
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 30px; color: #1E293B; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid #E2E8F0; }}
        .card-content {{ padding: 20px; }}
        .rig-info {{ background: #F8FAFC; border-radius: 8px; padding: 12px; margin-top: 10px; border-left: 4px solid #FBBF24; color: #334155; font-size: 0.85rem; text-align: left; }}
        .stTabs [data-baseweb="tab"] {{ color: white !important; font-weight: bold; }}
        .stTabs [aria-selected="true"] {{ color: #FBBF24 !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA TÁCTICA (LAS PIEZAS DEL MOTOR) ---
def flecha_desde(grados):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(grados / 45) % 8]

def flecha_hacia(grados):
    return ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"][round(grados / 45) % 8]

def generar_marea_aprox(fecha_target):
    dia = fecha_target.day
    plea = f"{(dia % 12) + 2:02d}:00"
    baja = f"{((dia % 12) + 8) % 24:02d}:30"
    coef = 50 + (dia * 3 % 45)
    return plea, baja, coef

def get_semaforo_info(ola, viento):
    if ola > 2.0 or viento > 25: return "bg-red", "🛑 ARRISKUTSUA / PELIGRO"
    if viento > 10 or ola > 1.5: return "bg-yellow", "🟡 KONTUZ / PRECAUCIÓN"
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
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto&forecast_days=6"
        url_w = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_direction_10m,pressure_msl&timezone=auto&forecast_days=6"
        dm = requests.get(url_m).json()
        dw = requests.get(url_w).json()
        df = pd.DataFrame({
            'time': pd.to_datetime(dm['hourly']['time']),
            'wave_h': dm['hourly']['wave_height'],
            'wave_d': dm['hourly']['wave_direction'],
            'curr_v': dm['hourly']['ocean_current_velocity'],
            'curr_d': dm['hourly']['ocean_current_direction'],
            'sst': dm['hourly']['sea_surface_temperature'],
            'wind_s': dw['hourly']['wind_speed_10m'],
            'wind_d': dw['hourly']['wind_direction_10m'],
            'pres': dw['hourly']['pressure_msl']
        })
        return df
    except Exception as e:
        st.error(f"Ezin dira datuak kargatu: {e}")
        return None

def crear_grafico_taktikoa(df_plot, titulo):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("💨 Haizea (km/h)", "🌊 Olatua (m)", "💧 Korrontea (km/h)"))
    
    viento_cal = df_plot['wind_s'] * f_viento
    fig.add_trace(go.Scatter(x=df_plot['time'], y=viento_cal, line=dict(color='#BAE6FD', width=3), name='Haizea'), row=1, col=1)
    
    ola_cal = np.maximum(df_plot['wave_h'] + f_ola, 0.1)
    fig.add_trace(go.Scatter(x=df_plot['time'], y=ola_cal, line=dict(color='#FBBF24', width=3), name='Olatua'), row=2, col=1)
    
    curr_kmh = df_plot['curr_v'] * 3.6
    fig.add_trace(go.Scatter(x=df_plot['time'], y=curr_kmh, line=dict(color='#10B981', width=3), name='Korrontea'), row=3, col=1)

    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(30,41,59,0.5)', height=600, showlegend=False)
    return fig

# --- 3. INTERFAZ ---
df_master = fetch_master_data()
ahora_local = datetime.now(ZONA_HORARIA)

tab0, tab1, tab2, tab3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

if df_master is not None:
    # Datos actuales para la portada
    ola_act = df_master.iloc[0]['wave_h'] + f_ola
    v_viento = (df_master.iloc[0]['wind_s'] * 3.6) * f_viento
    p, b, coef_act = generar_marea_aprox(ahora_local) # AQUÍ SE LLAMA A LA FUNCIÓN
    
    with tab0:
        c_cls, s_txt = get_semaforo_info(ola_act, v_viento)
        estrellas = calcular_actividad(ola_act, v_viento, coef_act, df_master.iloc[0]['sst'], df_master.iloc[0]['pres'])
        
        st.markdown(f"<div class='main-card'><div class='status-bar {c_cls}'></div><h1 style='margin-top:10px;'>MUTRIKU {ahora_local.strftime('%H:%M')}</h1><div style='font-weight:bold; color:#FBBF24;'>{s_txt}</div><div class='activity-badge'>Arrainen Jarduera: {estrellas}</div></div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ HAIZEA</h3><h2>{v_viento:.1f} <span class='big-arrow'>{flecha_desde(df_master.iloc[0]['wind_d'])}</span></h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f} <span class='big-arrow'>{flecha_desde(df_master.iloc[0]['wave_d'])}</span></h2></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ URA</h3><h2>{df_master.iloc[0]['sst']:.1f}°</h2></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 KORR.</h3><h2>{df_master.iloc[0]['curr_v']*3.6:.1f} <span class='big-arrow'>{flecha_hacia(df_master.iloc[0]['curr_d'])}</span></h2></div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='tide-alert'>⏳ Itsasgora {p} / Itsasbehera {b} (K:{coef_act})</div>", unsafe_allow_html=True)
        
        st.divider()
        st.subheader("📊 GAURKO EBOLUZIO TAKTIKOA")
        fig_hoy = crear_grafico_taktikoa(df_master.iloc[:18:2], "Gaurko Bilakaera")
        st.plotly_chart(fig_hoy, use_container_width=True)

    with tab1:
        st.header("📅 Hurrengo 4 Egunak")
        hoy = ahora_local.date()
        for i in range(1, 5):
            d = hoy + timedelta(days=i)
            p, b, coef = generar_marea_aprox(d) # LLAMADA EN BUCLE
            idx_12 = (i * 24) + 12
            o_d = df_master.iloc[idx_12]['wave_h'] + f_ola
            v_d = df_master.iloc[idx_12]['wind_s'] * 3.6 * f_viento
            c_cls, s_txt = get_semaforo_info(o_d, v_d)
            
            st.markdown(f"<div class='day-forecast-card'><div class='status-bar {c_cls}'></div><div class='card-content'><h3>{d.strftime('%A, %b %d')}</h3><p><b>{s_txt}</b> | 🔼 {p} / 🔽 {b} | Coef: {coef}</p></div></div>", unsafe_allow_html=True)
            fig_d = crear_grafico_taktikoa(df_master.iloc[(i*24)+8:(i*24)+22:2], f"{d.strftime('%A')}rako Iragarpena")
            st.plotly_chart(fig_d, use_container_width=True, key=f"g_{i}")

    with tab2:
        m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
        folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        plugins.MeasureControl(position='topright').add_to(m)
        plugins.Draw(position='topleft').add_to(m)
        st_folium(m, width="100%", height=500)

    with tab3:
        st.header("🐟 Espezieak eta Apailuak")
        col1, col2 = st.columns(2)
        especies = [
            ("SARGOA", "Aparraren erregea.", "Línea 0.35mm. Bua 20-40g. Fluorocarbono 0.30mm."),
            ("LUPINA", "Egunsentian spinning señueloekin.", "Trenzado 0.18mm. Behea 0.40mm."),
            ("TXIPIROIA", "Poterak 2.0-2.5 ilunabarrean.", "Trenzado 0.10mm. Fluorocarbono 0.22mm.")
        ]
        for name, tip, rig in especies:
            with st.expander(f"📌 {name}"):
                st.write(tip)
                st.markdown(f"<div class='rig-info'>🛠️ {rig}</div>", unsafe_allow_html=True)
