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
st.set_page_config(page_title="Txomin v.32.4 - Espezieak eta Plotterra", page_icon="🔱", layout="wide")

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
        .scroll-wrapper {{ display: flex; overflow-x: auto; gap: 15px; padding: 10px 0; }}
        .hour-card {{ flex: 0 0 auto; width: 175px; background: rgba(255, 255, 255, 0.95); border-left: 5px solid #0369A1; border-radius: 12px; padding: 15px; text-align: center; color: #1E293B !important; }}
        .hour-card h4 {{ margin: 0; color: #0369A1 !important; font-size: 1.2rem; border-bottom: 1px solid #E2E8F0; padding-bottom: 5px; margin-bottom: 5px; }}
        .rec-badge {{ background: #059669; color: white; border-radius: 8px; padding: 4px; margin-top: 10px; font-weight: bold; font-size: 0.8rem; display: block; }}
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; margin-bottom: 15px; color: #1E293B; border-left: 8px solid #0369A1; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
        .day-forecast-title {{ font-size: 1.3rem; font-weight: bold; color: #0369A1; margin-bottom: 10px; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; text-transform: capitalize; }}
        .day-metrics-row {{ display: flex; justify-content: space-between; flex-wrap: wrap; margin-bottom: 10px; font-size: 1.05rem; }}
        .day-metrics-row div {{ background: #F1F5F9; padding: 8px 12px; border-radius: 8px; margin: 5px 5px 0 0; border: 1px solid #CBD5E1; display:flex; align-items:center; gap:5px; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA ---
def flecha_desde(grados):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(grados / 45) % 8]

def flecha_hacia(grados):
    return ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"][round(grados / 45) % 8]

def generar_marea_aprox(fecha_target):
    dia = fecha_target.day
    return f"{(dia % 12) + 2:02d}:{(dia * 7 % 60):02d}", f"{((dia % 12) + 8) % 24:02d}:{(dia * 7 % 60 + 15) % 60:02d}", 50 + (dia * 3 % 45)

def recomendacion_tecnica(ola, viento, corriente):
    if ola > 2.2: return "🛑 PORTUA", "Itsaso zakarregia."
    if 0.8 <= ola <= 1.8: return "🎣 KORTXOA", "Aparretan arrantza."
    return "⚓ JIGGING", "Ur lasaia hondoan."

@st.cache_data(ttl=600)
def fetch_data():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.32.4")
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
        
        st.markdown(f"<div class='main-card'><h1>MUTRIKU {ahora_local.strftime('%H:%M')}</h1></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ HAIZEA</h3><h2>{v_viento:.1f} <span class='big-arrow'>{dir_viento}</span></h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f} <span class='big-arrow'>{ola_dir}</span></h2></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ URA</h3><h2>{dm_m['hourly']['sea_surface_temperature'][0]:.1f}°</h2></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 KORR.</h3><h2>{v_corr:.1f} <span class='big-arrow'>{dir_corr}</span></h2></div>", unsafe_allow_html=True)
        
        p, b, _ = generar_marea_aprox(ahora_local)
        st.markdown(f"<div class='tide-alert'>⏳ Hurrengo marea hurbil: Plea {p} / Baja {b}</div>", unsafe_allow_html=True)
        
        html_c = "<div class='scroll-wrapper'>"
        for i in range(0, 8):
            item = dw_m['list'][i]
            h = datetime.fromtimestamp(item['dt'], ZONA_HORARIA)
            o = dm_m['hourly']['wave_height'][i*3]
            tec, _ = recomendacion_tecnica(o, 0, 0)
            html_c += f"<div class='hour-card'><h4>{h.strftime('%H:%M')}</h4><p>🌬️ {item['wind']['speed']*3.6:.0f} <span class='med-arrow'>{flecha_desde(item['wind']['deg'])}</span></p><p>🌊 {o:.1f} <span class='med-arrow'>{flecha_desde(dm_m['hourly']['wave_direction'][i*3])}</span></p><span class='rec-badge'>{tec}</span></div>"
        st.markdown(html_c + "</div>", unsafe_allow_html=True)

with tab1:
    st.header("📅 4 Eguneko Iragarpena")
    if dw_m:
        hoy = ahora_local.date()
        for i in range(1, 5):
            d = hoy + timedelta(days=i)
            plea, baja, coef = generar_marea_aprox(d)
            item_12 = next((x for x in dw_m['list'] if datetime.fromtimestamp(x['dt'], ZONA_HORARIA).date() == d and datetime.fromtimestamp(x['dt'], ZONA_HORARIA).hour in [11, 12, 13]), None)
            if item_12:
                idx = dw_m['list'].index(item_12)
                o_p = dm_m['hourly']['wave_height'][idx*3]
                o_d = flecha_desde(dm_m['hourly']['wave_direction'][idx*3])
                v_p = item_12['wind']['speed'] * 3.6
                v_d = flecha_desde(item_12['wind']['deg'])
                st.markdown(f"<div class='day-forecast-card'><div class='day-forecast-title'>{d.strftime('%A, %b %d')}</div><div class='day-metrics-row'><div>🌬️ {v_p:.1f} <span class='med-arrow'>{v_d}</span></div><div>🌊 {o_p:.1f} <span class='med-arrow'>{o_d}</span></div></div><div class='day-metrics-row' style='background:#E0F2FE;'><div>🔼 Plea: {plea}</div><div>🔽 Baja: {baja}</div><div>🌊 Koef: {coef}</div></div></div>", unsafe_allow_html=True)

with tab2:
    st.subheader("🗺️ Plotterra")
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    folium.WmsTileLayer(url='https://ideihm.covam.es/wms/cartografia_espanola?', layers='relieve,isobatas', name='IHM', fmt='image/png', transparent=True, overlay=True).add_to(m)
    plugins.MeasureControl(position='topright', primary_length_unit='meters').add_to(m)
    plugins.Draw(position='topleft', draw_options={'polyline':{'shapeOptions':{'color':'#FBBF24'}}}).add_to(m)
    st_folium(m, width="100%", height=600, key="plotter_v324")

with tab3:
    st.header("🐟 Kantauriko 10 Espezie Nagusiak")
    c_e1, c_e2 = st.columns(2)
    with c_e1:
        with st.expander("1. SARGOA"): st.write("**Aholkua:** Aparraren erregea. Itsasoa: 0.8m-1.5m. Kortxoa edo hondoa. Beita: Izkira edo masia.")
        with st.expander("2. LUPINA"): st.write("**Aholkua:** Aparretan. Egunsentian edo ilunabarrean. Spinning minnow-ekin edo bizirik.")
        with st.expander("3. TXITXARROA"): st.write("**Aholkua:** Kakea arina 3 korapilotara luma zuriekin itsasoa kizkurtzean.")
        with st.expander("4. TXIPIROIA"): st.write("**Aholkua:** Ur geldoak eta ilunabarra. 2.0-ko poterak tirakada leunekin.")
        with st.expander("5. URRABURUA (Dorada)"): st.write("**Aholkua:** Hondarrezko hondo mistoa. Beita gogorra (karramarroa, navaja).")
    with c_e2:
        with st.expander("6. DENTOIA"): st.write("**Aholkua:** Hondo handiak. Jigging astuna edo beita bizia (txibia/kalamarra).")
        with st.expander("7. MOXARRA"): st.write("**Aholkua:** Ur lasaiagoak. Hondoa edo kortxoa arroketatik gertu.")
        with st.expander("8. SALMONETEA"): st.write("**Aholkua:** Hondarrezko hondoak. Amu finak zizarearekin (koreana).")
        with st.expander("9. KABRARROKA"): st.write("**Aholkua:** Harri purua. Hondo astuna txipiroi tirekin. Kontuz arantzekin!")
        with st.expander("10. BOGA"): st.write("**Aholkua:** Ur erdiak. Kortxo arina. Dibertigarria umeentzat.")
