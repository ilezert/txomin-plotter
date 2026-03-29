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
st.set_page_config(page_title="Txomin v.32.8 - Master Pantaila", page_icon="🔱", layout="wide")

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
        
        /* CARRUSEL HORIZONTAL FIX */
        .scroll-wrapper {{ display: flex !important; flex-direction: row !important; overflow-x: auto !important; gap: 12px; padding: 10px 0 20px 0; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; width: 100%; }}
        .scroll-wrapper::-webkit-scrollbar {{ height: 6px; }}
        .scroll-wrapper::-webkit-scrollbar-thumb {{ background: rgba(0,0,0,0.2); border-radius: 10px; }}
        
        .hour-card {{ flex: 0 0 auto; width: 150px; background: rgba(255, 255, 255, 0.95); border-top: 4px solid #0369A1; border-radius: 12px; padding: 10px; text-align: center; color: #1E293B !important; scroll-snap-align: start; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); }}
        .hour-card h4 {{ margin: 0 0 5px 0; color: #0369A1 !important; font-size: 1rem; font-weight: 800; border-bottom: 1px solid #E2E8F0; }}
        .hour-card p {{ margin: 3px 0; font-size: 0.8rem; font-weight: 600; color: #334155 !important; display: flex; justify-content: space-between; }}
        .rec-badge {{ background: #059669; color: white; border-radius: 6px; padding: 3px; margin-top: 5px; font-weight: bold; font-size: 0.75rem; display: block; }}
        
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 30px; color: #1E293B; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid #E2E8F0; }}
        .card-content {{ padding: 20px; }}
        .day-forecast-title {{ font-size: 1.4rem; font-weight: bold; color: #0369A1; text-transform: capitalize; margin: 0; }}
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

def get_semaforo_info(ola, viento):
    if ola > 2.0 or viento > 25: return "bg-red", "🛑 ARRISKUTSUA"
    if viento > 10 or ola > 1.5: return "bg-yellow", "🟡 KONTUZ"
    return "bg-green", "🟢 EGOKIA"

def calcular_actividad(ola, viento, coef, temp, pres):
    puntos = 1
    if 60 <= coef <= 95: puntos += 1
    if 1010 <= pres <= 1025: puntos += 1
    if 13 <= temp <= 19: puntos += 1
    if 0.5 <= ola <= 1.5: puntos += 1
    if viento > 25: puntos -= 1
    score = max(1, min(5, puntos))
    return "⭐" * score + "🌑" * (5 - score)

def recomendacion_tecnica(ola, viento):
    if ola > 2.0: return "PORTUA"
    if 0.8 <= ola <= 1.8: return "KORTXOA"
    if viento > 12: return "KAKEA"
    return "JIGGING"

@st.cache_data(ttl=600)
def fetch_data():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.32.8")
dm_m, dw_m = fetch_data()
ahora_local = datetime.now(ZONA_HORARIA)

tab0, tab1, tab2, tab3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

if dm_m and dw_m:
    # --- TAB 0: PORTADA ---
    with tab0:
        ola_act = dm_m['hourly']['wave_height'][0]
        v_viento = dw_m['list'][0]['wind']['speed'] * 3.6
        temp_u = dm_m['hourly']['sea_surface_temperature'][0]
        pres_a = dw_m['list'][0]['main']['pressure']
        _, _, coef_act = generar_marea_aprox(ahora_local)
        
        c_cls, s_txt = get_semaforo_info(ola_act, v_viento)
        estrellas = calcular_actividad(ola_act, v_viento, coef_act, temp_u, pres_a)

        st.markdown(f"<div class='main-card'><div class='status-bar {c_cls}'></div><h1 style='margin-top:10px;'>MUTRIKU {ahora_local.strftime('%H:%M')}</h1><div style='font-weight:bold; color:#FBBF24;'>{s_txt}</div><div class='activity-badge'>Jarduera: {estrellas}</div></div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ HAIZEA</h3><h2>{v_viento:.1f} <span class='big-arrow'>{flecha_desde(dw_m['list'][0]['wind']['deg'])}</span></h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f} <span class='big-arrow'>{flecha_desde(dm_m['hourly']['wave_direction'][0])}</span></h2></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ URA</h3><h2>{temp_u:.1f}°</h2><p>{pres_a} hPa</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 KORR.</h3><h2>{dm_m['hourly']['ocean_current_velocity'][0]*3.6:.1f} <span class='big-arrow'>{flecha_hacia(dm_m['hourly']['ocean_current_direction'][0])}</span></h2></div>", unsafe_allow_html=True)
        
        st.write("### ⏱️ GAURKO EBOLUZIOA")
        html_c = "<div class='scroll-wrapper'>"
        for i in range(0, 12, 2):
            idx = i
            o = dm_m['hourly']['wave_height'][idx]
            v = dw_m['list'][idx//3]['wind']['speed']*3.6
            c = dm_m['hourly']['ocean_current_velocity'][idx]*3.6
            html_c += f"<div class='hour-card'><h4>{(ahora_local.hour+i)%24:02d}:00</h4><p>🌬️ {v:.0f} <span>{flecha_desde(dw_m['list'][idx//3]['wind']['deg'])}</span></p><p>🌊 {o:.1f} <span>{flecha_desde(dm_m['hourly']['wave_direction'][idx])}</span></p><p>💧 {c:.1f} <span>{flecha_hacia(dm_m['hourly']['ocean_current_direction'][idx])}</span></p><span class='rec-badge'>{recomendacion_tecnica(o,v)}</span></div>"
        st.markdown(html_c + "</div>", unsafe_allow_html=True)

    # --- TAB 1: 4 EGUN (FIXED HORIZONTAL & SEMAPHORE) ---
    with tab1:
        st.header("📅 4 Eguneko Iragarpena")
        hoy = ahora_local.date()
        for i in range(1, 5):
            d = hoy + timedelta(days=i)
            p, b, coef = generar_marea_aprox(d)
            
            # Datos mediodía para el semáforo diario
            idx_12 = (i * 24) + 12
            o_d = dm_m['hourly']['wave_height'][idx_12]
            v_d = dw_m['list'][(idx_12//3)%len(dw_m['list'])]['wind']['speed']*3.6
            c_cls, s_txt = get_semaforo_info(o_d, v_d)
            estrellas = calcular_actividad(o_d, v_d, coef, dm_m['hourly']['sea_surface_temperature'][idx_12], 1015)

            # HTML CARD
            html_day = f"<div class='day-forecast-card'><div class='status-bar {c_cls}'></div><div class='card-content'>"
            html_day += f"<div style='display:flex; justify-content:space-between; align-items:center;'><h3 class='day-forecast-title'>{d.strftime('%A, %b %d')}</h3><b style='color:#334155;'>{s_txt}</b></div>"
            html_day += f"<div class='activity-badge'>Jarduera: {estrellas}</div>"
            html_day += f"<p style='margin:0; font-weight:bold; color:#0369A1;'>🔼 {p} | 🔽 {b} | Coef: {coef}</p>"
            
            # Carrusel Horizontal
            html_day += "<div class='scroll-wrapper'>"
            for h_p in range(8, 23, 3):
                idx = (i * 24) + h_p
                if idx < len(dm_m['hourly']['wave_height']):
                    o = dm_m['hourly']['wave_height'][idx]
                    v = dw_m['list'][(idx//3)%len(dw_m['list'])]['wind']['speed']*3.6
                    cur = dm_m['hourly']['ocean_current_velocity'][idx]*3.6
                    html_day += f"<div class='hour-card'><h4>{h_p:02d}:00</h4><p>🌬️ {v:.0f} <span>{flecha_desde(dw_m['list'][(idx//3)%len(dw_m['list'])]['wind']['deg'])}</span></p><p>🌊 {o:.1f} <span>{flecha_desde(dm_m['hourly']['wave_direction'][idx])}</span></p><p>💧 {cur:.1f} <span>{flecha_hacia(dm_m['hourly']['ocean_current_direction'][idx])}</span></p><span class='rec-badge'>{recomendacion_tecnica(o,v)}</span></div>"
            html_day += "</div></div></div>"
            st.markdown(html_day, unsafe_allow_html=True)

    with tab2:
        m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
        folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium.WmsTileLayer(url='https://ideihm.covam.es/wms/cartografia_espanola?', layers='relieve,isobatas', name='IHM', fmt='image/png', transparent=True, overlay=True).add_to(m)
        plugins.MeasureControl(position='topright').add_to(m)
        plugins.Draw(position='topleft').add_to(m)
        st_folium(m, width="100%", height=500, key="plot_v328")

    with tab3:
        st.header("🐟 Kantauriko 10 Espezie Nagusiak")
        e1, e2 = st.columns(2)
        with e1:
            with st.expander("📌 1. SARGOA"): st.write("Aparraren erregea. 0.8m-1.5m artean onena. Beita: Izkira edo masia.")
            with st.expander("🐠 2. LUPINA"): st.write("Oso argia. Egunsentian spinning egiteko ezin hobea señueloekin.")
            with st.expander("🐟 3. TXITXARROA"): st.write("Gauez portuetan. Kakea arina 3 korapilotara luma zuriekin.")
            with st.expander("🦑 4. TXIPIROIA"): st.write("Ur geldoak. 2.0 poterak tirakada leunekin ilunabarrean.")
            with st.expander("👑 5. URRABURUA"): st.write("Hondarrezko hondoak. Beita gogorra: karramarroa edo navaja.")
        with e2:
            with st.expander("🦈 6. DENTOIA"): st.write("Hondo handiko harraparia. Jigging astuna edo beita bizia behar du.")
            with st.expander("🐚 7. MOXARRA"): st.write("Ur lasaiak. Hondoan arrantzatzen da zizare edo izkira txikiekin.")
            with st.expander("🦐 8. BARBINA"): st.write("Hondarrezko hondoak. Amu finak eta hondarrezko zizarea erabili.")
            with st.expander("🦂 9. KABRARROKA"): st.write("Harri puruan bizi da. Hondoan txipiroi tirekin. Kontuz arantzekin!")
            with st.expander("🍥 10. BOGA"): st.write("Ur erdiak. Kortxo arina eta ogia. Umeentzako dibertigarria.")
