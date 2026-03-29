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
st.set_page_config(page_title="Txomin v.32.7 - Evoluzio Osoa", page_icon="🔱", layout="wide")

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
        
        .activity-badge {{ background: #1E293B; color: #FBBF24; padding: 8px 15px; border-radius: 25px; font-weight: bold; font-size: 1rem; display: inline-block; margin: 15px 0; border: 1px solid #FBBF24; }}
        
        /* CARRUSEL PRO */
        .scroll-wrapper {{ display: flex; overflow-x: auto; gap: 12px; padding: 10px 0 20px 0; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; }}
        .scroll-wrapper::-webkit-scrollbar {{ height: 6px; }}
        .scroll-wrapper::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.3); border-radius: 10px; }}
        
        .hour-card {{ flex: 0 0 auto; width: 160px; background: rgba(255, 255, 255, 0.95); border-top: 4px solid #0369A1; border-radius: 12px; padding: 12px; text-align: center; color: #1E293B !important; scroll-snap-align: start; box-shadow: 2px 2px 8px rgba(0,0,0,0.2); }}
        .hour-card h4 {{ margin: 0 0 8px 0; color: #0369A1 !important; font-size: 1.1rem; font-weight: 800; border-bottom: 1px solid #E2E8F0; }}
        .hour-card p {{ margin: 4px 0; font-size: 0.85rem; font-weight: 600; color: #334155 !important; display: flex; justify-content: space-between; }}
        
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 25px; color: #1E293B; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
        .card-content {{ padding: 15px; }}
        .day-forecast-title {{ font-size: 1.3rem; font-weight: bold; color: #0369A1; text-transform: capitalize; }}
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
st.title("🔱 Txomin v.32.7 - Arrantza Maisua")
dm_m, dw_m = fetch_data()
ahora_local = datetime.now(ZONA_HORARIA)

tab0, tab1, tab2, tab3 = st.tabs(["⚓ ITSASOA ORAIN", "📅 4 EGUNEKO IRAGARPENA", "🗺️ MAPA", "🐟 ESPEZIEAK"])

if dm_m and dw_m:
    # --- TAB 0: PORTADA ---
    with tab0:
        ola_act = dm_m['hourly']['wave_height'][0]
        v_viento = dw_m['list'][0]['wind']['speed'] * 3.6
        temp_u = dm_m['hourly']['sea_surface_temperature'][0]
        pres_a = dw_m['list'][0]['main']['pressure']
        _, _, coef_act = generar_marea_aprox(ahora_local)
        
        color_cls, status_txt = get_semaforo_info(ola_act, v_viento)
        estrellas_act = calcular_actividad(ola_act, v_viento, coef_act, temp_u, pres_a)

        st.markdown(f"""
            <div class='main-card'>
                <div class='status-bar {color_cls}'></div>
                <h1 style='margin-top:10px;'>MUTRIKU {ahora_local.strftime('%H:%M')}</h1>
                <div style='font-weight:bold; font-size:1.1rem; color:#FBBF24;'>{status_txt}</div>
                <div class='activity-badge'>Arrainen Jarduera: {estrellas_act}</div>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ HAIZEA</h3><h2>{v_viento:.1f} <span class='big-arrow'>{flecha_desde(dw_m['list'][0]['wind']['deg'])}</span></h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLATUA</h3><h2>{ola_act:.1f} <span class='big-arrow'>{flecha_desde(dm_m['hourly']['wave_direction'][0])}</span></h2></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ URA</h3><h2>{temp_u:.1f}°</h2><p>{pres_a} hPa</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 KORR.</h3><h2>{dm_m['hourly']['ocean_current_velocity'][0]*3.6:.1f} <span class='big-arrow'>{flecha_hacia(dm_m['hourly']['ocean_current_direction'][0])}</span></h2></div>", unsafe_allow_html=True)
        
        st.write("### ⏱️ GAURKO EBOLUZIOA (2 ORDURO)")
        html_c = "<div class='scroll-wrapper'>"
        for i in range(0, 12, 2): # Cada 2 horas hoy
            item_w = dw_m['list'][i//3 * 3 if i < len(dw_m['list']) else 0]
            h = ahora_local.replace(hour=(ahora_local.hour + i)%24, minute=0)
            o = dm_m['hourly']['wave_height'][i]
            v = item_w['wind']['speed'] * 3.6
            c = dm_m['hourly']['ocean_current_velocity'][i] * 3.6
            tec = recomendacion_tecnica(o, v)
            html_c += f"<div class='hour-card'><h4>{h.strftime('%H:%M')}</h4><p>🌬️ {v:.0f} km/h <span>{flecha_desde(item_w['wind']['deg'])}</span></p><p>🌊 {o:.1f} m <span>{flecha_desde(dm_m['hourly']['wave_direction'][i])}</span></p><p>💧 {c:.1f} km/h <span>{flecha_hacia(dm_m['hourly']['ocean_current_direction'][i])}</span></p><span class='rec-badge'>{tec}</span></div>"
        st.markdown(html_c + "</div>", unsafe_allow_html=True)

    # --- TAB 1: 4 EGUN ---
    with tab1:
        st.header("📅 4 Eguneko Iragarpen Taktikoa (2 orduro)")
        hoy = ahora_local.date()
        for i in range(1, 5):
            d = hoy + timedelta(days=i)
            plea, baja, coef = generar_marea_aprox(d)
            st.markdown(f"""
            <div class='day-forecast-card'>
                <div class='card-content'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div class='day-forecast-title'>{d.strftime('%A, %b %d')}</div>
                        <div style='font-size:0.9rem; font-weight:bold; color:#0369A1;'>🔼 {plea} | 🔽 {baja} (K:{coef})</div>
                    </div>
                    <div class='scroll-wrapper'>
            """, unsafe_allow_html=True)
            
            html_day = ""
            # Horas de pesca: 08:00 a 22:00 cada 2 horas
            for h_p in range(8, 23, 2):
                idx = (i * 24) + h_p
                if idx < len(dm_m['hourly']['wave_height']):
                    o_p = dm_m['hourly']['wave_height'][idx]
                    o_d = flecha_desde(dm_m['hourly']['wave_direction'][idx])
                    c_v = dm_m['hourly']['ocean_current_velocity'][idx] * 3.6
                    c_d = flecha_hacia(dm_m['hourly']['ocean_current_direction'][idx])
                    # Viento aproximado del forecast (cada 3h)
                    item_w = dw_m['list'][(idx//3) % len(dw_m['list'])]
                    v_p = item_w['wind']['speed'] * 3.6
                    v_d = flecha_desde(item_w['wind']['deg'])
                    tec = recomendacion_tecnica(o_p, v_p)
                    
                    html_day += f"<div class='hour-card'><h4>{h_p:02d}:00</h4><p>🌬️ {v_p:.0f} <span>{v_d}</span></p><p>🌊 {o_p:.1f} <span>{o_d}</span></p><p>💧 {c_v:.1f} <span>{c_d}</span></p><span class='rec-badge'>{tec}</span></div>"
            
            st.markdown(html_day + "</div></div></div>", unsafe_allow_html=True)

    # --- TAB 2: MAPA ---
    with tab2:
        m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
        folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium.WmsTileLayer(url='https://ideihm.covam.es/wms/cartografia_espanola?', layers='relieve,isobatas', name='IHM', fmt='image/png', transparent=True, overlay=True).add_to(m)
        plugins.MeasureControl(position='topright').add_to(m)
        plugins.Draw(position='topleft').add_to(m)
        st_folium(m, width="100%", height=500, key="plotter_v327")

    # --- TAB 3: ESPECIES ---
    with tab3:
        st.header("🐟 Kantauriko 10 Espezie Nagusiak")
        e1, e2 = st.columns(2)
        with e1:
            with st.expander("📌 1. SARGOA (Diplodus sargus)"):
                st.write("""Aparraren erregea da. Olatuek arroketan jotzen duten lekuetan ibiltzen da jaten, apar zuri asko dagoen lekuetan. 
                Gomendioa: Itsasoa 0.8m eta 1.5m artean dagoenean da onena. Erabili korchoa edo hondoa izkira edo masia erabiliz. 
                Ezinbestekoa da inguruak ondo ezagutzea olatuek ez harrapatzeko.""")
            with st.expander("🐠 2. LUPINA (Dicentrarchus labrax)"):
                st.write("""Oso arrain argia eta mesfidatia. Aparretan eta erreka-ahoetan ehizatzen du, ur oxigenatuaren bila. 
                Gomendioa: Spinning egiteko ezin hobea da egunsentian edo ilunabarrean, itsasoa mugitua dagoenean. 
                Señuelo artifizialak (minnow) mugimendu azkarrekin erabili.""")
            with st.expander("🐟 3. TXITXARROA (Trachurus trachurus)"):
                st.write("""Talde handietan ibiltzen den arraina. Gauez portuko argien inguruan asko hurbiltzen da janari bila. 
                Gomendioa: Kakea arina egiteko aproposa 3 korapilotara, luma zuriak erabiliz. 
                Haizeak itsasoa apur bat kizkurtzen duenean aktibatzen dira gehien.""")
            with st.expander("🦑 4. TXIPIROIA (Loligo vulgaris)"):
                st.write("""Ur geldoak eta garbiak maite ditu. Itsasbehera denean eta ilunabarrean hasten da mugimendua. 
                Gomendioa: 2.0 edo 2.5 neurriko poterak erabili, tirakada oso leunak emanez. 
                Kolore naturalak erabili ur garbiarekin eta deigarriagoak ur zikinarekin.""")
            with st.expander("👑 5. URRABURUA (Sparus aurata)"):
                st.write("""Hondarrezko hondo mistoetan eta arroka inguruetan ibiltzen da beita gogorren bila. 
                Gomendioa: Hondoan arrantzatu behar da apareju korredizoarekin. 
                Beita gogorrak erabili: karramarro berdea, tita edo navaja, arrain txikiek jan ez dezaten.""")
        with e2:
            with st.expander("🦈 6. DENTOIA (Dentex dentex)"):
                st.write("""Hondo handietako harraparia, indar handiko arraina. Kantilen eta hondo harritsuetan bizi da. 
                Gomendioa: Jigging astuna edo beita bizia (txibia edo kalamarra) beharrezkoa da sakonera handian. 
                Pazientzia handiko arrantza da, baina pieza handiak ematen ditu.""")
            with st.expander("🐚 7. MOXARRA (Diplodus vulgaris)"):
                st.write("""Sargoaren familiakoa baina ur lasaiagoetan eta sakonera gutxiagoan ibiltzen da normalean. 
                Gomendioa: Harri inguruetan kortxoarekin edo hondoan arrantzatzen da beita txikiekin. 
                Zizareak edo izkira txikiak dira beitarik onenak mozarra deitzeko.""")
            with st.expander("🦐 8. BARBINA / SALMONETEA (Mullus surmuletus)"):
                st.write("""Hondarrezko hondoetan bizi da, muturrarekin lurra mugituz janari bila (zizareak eta krustazeo txikiak). 
                Gomendioa: Hondoan arrantzatu amu finekin eta hondarrezko zizarearekin. 
                Usain handiko beitak behar dituzte hondoan detektatzeko.""")
            with st.expander("🦂 9. KABRARROKA (Scorpaena scrofa)"):
                st.write("""Harri puruan eta zuloetan bizi den arraina, mugitzen ez dena. Oso preziatua gastronomian. 
                Gomendioa: Hondoan berun astunarekin eta txipiroi tirekin arrantzatu harri artean. 
                Kontu handia izan arantzekin desanzuelatzerakoan, pozoitsuak baitira.""")
            with st.expander("🍥 10. BOGA (Boops boops)"):
                st.write("""Ur erdi eta azaletik hurbil ibiltzen den arrain txiki eta gosetia. Talde handiak sortzen ditu. 
                Gomendioa: Kortxo arinarekin eta ogi apurrekin edo zizarearekin arrantzatzen da. 
                Umeentzako oso dibertigarria da haien abiadura eta gosea dela eta.""")
    
    st.divider()
    st.caption("⚖️ Eusko Jaurlaritzaren araudia errespetatu: neurri txikienak eta kupoak.")
