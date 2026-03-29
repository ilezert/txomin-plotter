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
st.set_page_config(page_title="Txomin v.32.6 - Arrantza Maisua", page_icon="🔱", layout="wide")

API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")

IMG_FONDO_MAR = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/fondo_cantabrico.jpg"

st.markdown(f"""
    <style>
        .stApp {{ background-image: url("{IMG_FONDO_MAR}"); background-size: cover; background-attachment: fixed; background-position: center; background-color: #011627; color: white; }}
        .main-card {{ background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); color: white; padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.2); overflow: hidden; }}
        .metric-card {{ background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.3); }}
        .metric-card h2 {{ color: #FBBF24 !important; font-size: 2.2rem; margin: 0; display: flex; align-items: center; justify-content: center; gap: 8px; }}
        .big-arrow {{ font-size: 2.2rem; font-weight: bold; color: #FBBF24; }}
        .med-arrow {{ font-size: 1.2rem; font-weight: bold; color: #0369A1; }}
        
        /* Semáforo y Actividad */
        .status-bar {{ height: 15px; width: 100%; position: absolute; top: 0; left: 0; }}
        .bg-green {{ background-color: #10B981; }}
        .bg-yellow {{ background-color: #FBBF24; }}
        .bg-red {{ background-color: #EF4444; }}
        
        .activity-badge {{ background: #1E293B; color: #FBBF24; padding: 8px 15px; border-radius: 25px; font-weight: bold; font-size: 1.1rem; display: inline-block; margin: 15px 0; border: 1px solid #FBBF24; }}
        .tide-alert {{ background: rgba(5, 150, 105, 0.85); border-radius: 10px; padding: 10px; text-align: center; font-weight: bold; margin-bottom: 25px; border: 1px solid #34D399; }}
        
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 20px; color: #1E293B; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
        .card-content {{ padding: 20px; }}
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
def fetch_data():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.32.6 - Mutriku Tactical")
dm_m, dw_m = fetch_data()
ahora_local = datetime.now(ZONA_HORARIA)

tab0, tab1, tab2, tab3 = st.tabs(["⚓ ITSASOA ORAIN", "📅 4 EGUNEKO IRAGARPENA", "🗺️ MAPA", "🐟 ESPEZIEAK"])

if dm_m and dw_m:
    # Datos actuales para Tab 0
    ola_act = dm_m['hourly']['wave_height'][0]
    v_viento = dw_m['list'][0]['wind']['speed'] * 3.6
    temp_u = dm_m['hourly']['sea_surface_temperature'][0]
    pres_a = dw_m['list'][0]['main']['pressure']
    _, _, coef_act = generar_marea_aprox(ahora_local)
    
    color_cls, status_txt = get_semaforo_info(ola_act, v_viento)
    estrellas_act = calcular_actividad(ola_act, v_viento, coef_act, temp_u, pres_a)

    with tab0:
        st.markdown(f"""
            <div class='main-card'>
                <div class='status-bar {color_cls}'></div>
                <h1 style='margin-top:10px;'>MUTRIKU {ahora_local.strftime('%H:%M')}</h1>
                <div style='font-weight:bold; font-size:1.2rem; color:#FBBF24;'>{status_txt}</div>
                <div class='activity-badge'>Arrainen Jarduera / Actividad: {estrellas_act}</div>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ HAIZEA</h3><h2>{v_viento:.1f} <span class='big-arrow'>{flecha_desde(dw_m['list'][0]['wind']['deg'])}</span></h2><p>km/h</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLATUA</h3><h2>{ola_act:.1f} <span class='big-arrow'>{flecha_desde(dm_m['hourly']['wave_direction'][0])}</span></h2><p>m</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ URA</h3><h2>{temp_u:.1f}°</h2><p>{pres_a} hPa</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 KORR.</h3><h2>{dm_m['hourly']['ocean_current_velocity'][0]*3.6:.1f} <span class='big-arrow'>{flecha_hacia(dm_m['hourly']['ocean_current_direction'][0])}</span></h2><p>km/h</p></div>", unsafe_allow_html=True)
        
        p, b, _ = generar_marea_aprox(ahora_local)
        st.markdown(f"<div class='tide-alert'>⏳ Hurrengo marea hurbil: Itsasgora {p} / Itsasbehera {b}</div>", unsafe_allow_html=True)

    with tab1:
        st.header("📅 Iragarpen Taktikoa")
        hoy = ahora_local.date()
        for i in range(1, 5):
            d = hoy + timedelta(days=i)
            plea, baja, coef = generar_marea_aprox(d)
            item_12 = next((x for x in dw_m['list'] if datetime.fromtimestamp(x['dt'], ZONA_HORARIA).date() == d and datetime.fromtimestamp(x['dt'], ZONA_HORARIA).hour in [11, 12, 13]), dw_m['list'][i*8])
            idx = dw_m['list'].index(item_12)
            o_p, v_p = dm_m['hourly']['wave_height'][idx*3], item_12['wind']['speed'] * 3.6
            c_cls, s_txt = get_semaforo_info(o_p, v_p)
            estrellas = calcular_actividad(o_p, v_p, coef, dm_m['hourly']['sea_surface_temperature'][idx*3], item_12['main']['pressure'])
            
            st.markdown(f"""
            <div class='day-forecast-card'>
                <div class='status-bar {c_cls}'></div>
                <div class='card-content'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div class='day-forecast-title'>{d.strftime('%A, %b %d')}</div>
                        <div style='font-weight:bold;'>{s_txt}</div>
                    </div>
                    <div class='activity-badge'>Jarduera: {estrellas}</div>
                    <div class='day-metrics-grid'>
                        <div class='metric-item'>🌬️ {v_p:.1f} km/h {flecha_desde(item_12['wind']['deg'])}</div>
                        <div class='metric-item'>🌊 {o_p:.1f} m {flecha_desde(dm_m['hourly']['wave_direction'][idx*3])}</div>
                        <div class='metric-item'>💧 {dm_m['hourly']['ocean_current_velocity'][idx*3]*3.6:.1f} km/h {flecha_hacia(dm_m['hourly']['ocean_current_direction'][idx*3])}</div>
                        <div class='metric-item' style='background:#E0F2FE;'>🔼 {plea} / 🔽 {baja} (K:{coef})</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
        folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium.WmsTileLayer(url='https://ideihm.covam.es/wms/cartografia_espanola?', layers='relieve,isobatas', name='IHM', fmt='image/png', transparent=True, overlay=True).add_to(m)
        plugins.MeasureControl(position='topright').add_to(m)
        plugins.Draw(position='topleft').add_to(m)
        st_folium(m, width="100%", height=500, key="plotter_v326")

    with tab3:
        st.header("🐟 Kantauriko 10 Espezieak: Gida Taktikoa")
        e1, e2 = st.columns(2)
        with e1:
            with st.expander("📌 1. SARGOA (Diplodus sargus)"):
                st.write("""Aparraren erregea da. Olatuek arroketan jotzen duten lekuetan ibiltzen da jaten, apar zuri asko dagoen lekuetan. 
                Gomendioa: Itsasoa 0.8m eta 1.5m artean dagoenean da onena. Erabili korchoa edo hondoa izkira edo masiarekin.""")
            with st.expander("🐠 2. LUPINA (Dicentrarchus labrax)"):
                st.write("""Oso arrain argia eta mesfidatia. Aparretan eta erreka-ahoetan ehizatzen du. 
                Gomendioa: Spinning egiteko ezin hobea da egunsentian edo ilunabarrean, itsasoa mugitua dagoenean señuelo artifizialekin.""")
            with st.expander("🐟 3. TXITXARROA (Trachurus trachurus)"):
                st.write("""Talde handietan ibiltzen den arraina. Gauez portuko argien inguruan asko hurbiltzen da. 
                Gomendioa: Kakea arina egiteko aproposa 3 korapilotara, luma zuriak erabiliz itsasoa haizearekin kizkurtuta dagoenean.""")
            with st.expander("🦑 4. TXIPIROIA (Loligo vulgaris)"):
                st.write("""Ur geldoak eta garbiak maite ditu. Itsasbehera denean eta ilunabarrean hasten da mugimendua. 
                Gomendioa: 2.0 edo 2.5 neurriko poterak erabili, tirakada oso leunak emanez eta astiro jasoz. Ilunabarra da unerik onena.""")
            with st.expander("👑 5. URRABURUA (Sparus aurata)"):
                st.write("""Hondarrezko hondo mistoetan eta arroka inguruetan ibiltzen da beita gogorren bila. 
                Gomendioa: Hondoan arrantzatu behar da aparailu korredizoarekin. Beita gogorrak erabili: karramarro berdea, tita edo navaja.""")
        with e2:
            with st.expander("🦈 6. DENTOIA (Dentex dentex)"):
                st.write("""Hondo handietako harraparia, indar handiko arraina. Kantilen eta hondo harritsuetan bizi da. 
                Gomendioa: Jigging astuna edo beita bizia (txibia edo kalamarra) beharrezkoa da sakonera handian harrapatzeko.""")
            with st.expander("🐚 7. MOXARRA (Diplodus vulgaris)"):
                st.write("""Sargoaren familiakoa baina ur lasaiagoetan eta sakonera gutxiagoan ibiltzen da. 
                Gomendioa: Harri inguruetan kortxoarekin edo hondoan arrantzatzen da beita txikiekin: zizareak edo izkira txikiak.""")
            with st.expander("🦐 8. BARBINA / SALMONETEA (Mullus surmuletus)"):
                st.write("""Hondarrezko hondoetan bizi da, muturrarekin lurra mugituz janari bila. 
                Gomendioa: Hondoan arrantzatu amu finekin. Beitarik onenak usain handikoak dira, koreana edo hondarrezko zizarea adibidez.""")
            with st.expander("🦂 9. KABRARROKA (Scorpaena scrofa)"):
                st.write("""Harri puruan eta zuloetan bizi den arraina, mugitzen ez dena. Oso goxoa baina kontuz pozoiarekin. 
                Gomendioa: Hondoan berun astunarekin eta txipiroi tirekin arrantzatu. Kontu handia izan arantzekin desanzuelatzerakoan.""")
            with st.expander("🍥 10. BOGA (Boops boops)"):
                st.write("""Ur erdi eta azaletik hurbil ibiltzen den arrain txiki eta gosetia. Talde handiak sortzen ditu. 
                Gomendioa: Kortxo arinarekin eta ogi apurrekin edo zizarearekin arrantzatzen da. Umeentzako oso dibertigarria da.""")
