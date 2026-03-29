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
st.set_page_config(page_title="Txomin v.32.5 - Semaforoa", page_icon="🔱", layout="wide")

API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")

IMG_FONDO_MAR = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/fondo_cantabrico.jpg"

st.markdown(f"""
    <style>
        .stApp {{ background-image: url("{IMG_FONDO_MAR}"); background-size: cover; background-attachment: fixed; background-position: center; background-color: #011627; color: white; }}
        .main-card {{ background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); color: white; padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.2); }}
        .metric-card {{ background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.3); }}
        .metric-card h2 {{ color: #FBBF24 !important; font-size: 2.2rem; margin: 0; display: flex; align-items: center; justify-content: center; gap: 8px; }}
        .big-arrow {{ font-size: 2.2rem; font-weight: bold; color: #FBBF24; }}
        .med-arrow {{ font-size: 1.2rem; font-weight: bold; color: #0369A1; }}
        .tide-alert {{ background: rgba(5, 150, 105, 0.85); border-radius: 10px; padding: 10px; text-align: center; font-weight: bold; margin-bottom: 25px; border: 1px solid #34D399; }}
        
        /* Semáforo y Tarjetas de Previsión */
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 20px; color: #1E293B; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
        .status-bar {{ height: 12px; width: 100%; }}
        .bg-green {{ background-color: #10B981; }}
        .bg-yellow {{ background-color: #FBBF24; }}
        .bg-red {{ background-color: #EF4444; }}
        .card-content {{ padding: 20px; }}
        .day-forecast-title {{ font-size: 1.4rem; font-weight: bold; color: #0369A1; margin-bottom: 10px; text-transform: capitalize; border-bottom: 1px solid #E2E8F0; padding-bottom: 5px; }}
        
        .activity-badge {{ background: #1E293B; color: #FBBF24; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; display: inline-block; margin-bottom: 10px; }}
        .day-metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 10px; }}
        .metric-item {{ background: #F1F5F9; padding: 10px; border-radius: 8px; border: 1px solid #CBD5E1; text-align: center; font-size: 0.9rem; font-weight: bold; color: #334155; }}
        
        .scroll-wrapper {{ display: flex; overflow-x: auto; gap: 15px; padding: 10px 0; }}
        .hour-card {{ flex: 0 0 auto; width: 175px; background: rgba(255, 255, 255, 0.95); border-left: 5px solid #0369A1; border-radius: 12px; padding: 15px; text-align: center; color: #1E293B !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA TÁCTICA ---
def flecha_desde(grados):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(grados / 45) % 8]

def flecha_hacia(grados):
    return ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"][round(grados / 45) % 8]

def generar_marea_aprox(fecha_target):
    dia = fecha_target.day
    return f"{(dia % 12) + 2:02d}:{(dia * 7 % 60):02d}", f"{((dia % 12) + 8) % 24:02d}:{(dia * 7 % 60 + 15) % 60:02d}", 50 + (dia * 3 % 45)

def get_semaforo_color(ola, viento):
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
    return max(1, min(5, puntos))

@st.cache_data(ttl=600)
def fetch_data():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.32.5 - Semaforoa")
dm_m, dw_m = fetch_data()
ahora_local = datetime.now(ZONA_HORARIA)

tab0, tab1, tab2, tab3 = st.tabs(["⚓ ITSASOA", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

with tab0:
    if dm_m and dw_m:
        ola_act = dm_m['hourly']['wave_height'][0]
        ola_dir = flecha_desde(dm_m['hourly']['wave_direction'][0])
        v_corr = dm_m['hourly']['ocean_current_velocity'][0] * 3.6
        dir_corr = flecha_hacia(dm_m['hourly']['ocean_current_direction'][0])
        v_viento = dw_m['list'][0]['wind']['speed'] * 3.6
        dir_viento = flecha_desde(dw_m['list'][0]['wind']['deg'])
        temp_u = dm_m['hourly']['sea_surface_temperature'][0]
        pres_a = dw_m['list'][0]['main']['pressure']
        
        st.markdown(f"<div class='main-card'><h1>MUTRIKU {ahora_local.strftime('%H:%M')}</h1></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ HAIZEA</h3><h2>{v_viento:.1f} <span class='big-arrow'>{dir_viento}</span></h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f} <span class='big-arrow'>{ola_dir}</span></h2></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ URA</h3><h2>{temp_u:.1f}°</h2><p>{pres_a} hPa</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 KORR.</h3><h2>{v_corr:.1f} <span class='big-arrow'>{dir_corr}</span></h2></div>", unsafe_allow_html=True)
        
        p, b, _ = generar_marea_aprox(ahora_local)
        st.markdown(f"<div class='tide-alert'>⏳ Hurrengo marea hurbil: Plea {p} / Baja {b}</div>", unsafe_allow_html=True)

with tab1:
    st.header("📅 Hurrengo 4 Eguneko Iragarpen Taktikoa")
    if dw_m and dm_m:
        hoy = ahora_local.date()
        for i in range(1, 5):
            d = hoy + timedelta(days=i)
            plea, baja, coef = generar_marea_aprox(d)
            item_12 = next((x for x in dw_m['list'] if datetime.fromtimestamp(x['dt'], ZONA_HORARIA).date() == d and datetime.fromtimestamp(x['dt'], ZONA_HORARIA).hour in [11, 12, 13]), dw_m['list'][i*8])
            
            idx = dw_m['list'].index(item_12)
            o_p = dm_m['hourly']['wave_height'][idx*3]
            o_d = flecha_desde(dm_m['hourly']['wave_direction'][idx*3])
            v_p = item_12['wind']['speed'] * 3.6
            v_d = flecha_desde(item_12['wind']['deg'])
            c_v = dm_m['hourly']['ocean_current_velocity'][idx*3] * 3.6
            c_d = flecha_hacia(dm_m['hourly']['ocean_current_direction'][idx*3])
            t_u = dm_m['hourly']['sea_surface_temperature'][idx*3]
            p_a = item_12['main']['pressure']
            
            color_class, status_text = get_semaforo_color(o_p, v_p)
            act_score = calcular_actividad(o_p, v_p, coef, t_u, p_a)
            estrellas = "⭐" * act_score + "🌑" * (5 - act_score)
            
            st.markdown(f"""
            <div class='day-forecast-card'>
                <div class='status-bar {color_class}'></div>
                <div class='card-content'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div class='day-forecast-title'>{d.strftime('%A, %b %d')}</div>
                        <div style='font-weight:bold; color:#334155;'>{status_text}</div>
                    </div>
                    <div class='activity-badge'>Arrainen Jarduera / Actividad: {estrellas}</div>
                    <div class='day-metrics-grid'>
                        <div class='metric-item'>🌬️ Haizea<br>{v_p:.1f} km/h {v_d}</div>
                        <div class='metric-item'>🌊 Olatua<br>{o_p:.1f} m {o_d}</div>
                        <div class='metric-item'>💧 Korrontea<br>{c_v:.1f} km/h {c_d}</div>
                        <div class='metric-item'>🌡️ Ura/Presioa<br>{t_u:.1f}° / {p_a}hPa</div>
                        <div class='metric-item' style='background:#E0F2FE;'>🔼 Plea: {plea}<br>🔽 Baja: {baja}</div>
                        <div class='metric-item' style='background:#E0F2FE;'>🌊 Koef: {coef}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.subheader("🗺️ Plotterra")
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    folium.WmsTileLayer(url='https://ideihm.covam.es/wms/cartografia_espanola?', layers='relieve,isobatas', name='IHM', fmt='image/png', transparent=True, overlay=True).add_to(m)
    plugins.MeasureControl(position='topright', primary_length_unit='meters').add_to(m)
    plugins.Draw(position='topleft', draw_options={'polyline':{'shapeOptions':{'color':'#FBBF24'}}}).add_to(m)
    st_folium(m, width="100%", height=600, key="plotter_v325")

with tab3:
    st.header("🐟 Espezieak")
    st.write("1. **SARGOA**: Aparretan. 2. **LUPINA**: Spinning. 3. **TXIPIROIA**: Poterak.")
