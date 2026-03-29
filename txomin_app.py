import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Txomin v.33.0 - Master", page_icon="🔱", layout="wide")

# Seguridad para la API Key
if "OPENWEATHER_API_KEY" in st.secrets:
    API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
else:
    st.error("Falta la API Key en los Secrets de Streamlit.")
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
        .metric-card h2 {{ color: #FBBF24 !important; font-size: 2.2rem; margin: 0; display: flex; align-items: center; justify-content: center; gap: 8px; }}
        .big-arrow {{ font-size: 2.2rem; font-weight: bold; color: #FBBF24; }}
        .med-arrow {{ font-size: 1.1rem; font-weight: bold; color: #0369A1; }}
        .status-bar {{ height: 15px; width: 100%; position: absolute; top: 0; left: 0; }}
        .bg-green {{ background-color: #10B981; }}
        .bg-yellow {{ background-color: #FBBF24; }}
        .bg-red {{ background-color: #EF4444; }}
        .activity-badge {{ background: #1E293B; color: #FBBF24; padding: 8px 15px; border-radius: 25px; font-weight: bold; display: inline-block; margin: 15px 0; border: 1px solid #FBBF24; }}
        .scroll-wrapper {{ display: flex !important; flex-direction: row !important; overflow-x: auto !important; gap: 12px; padding: 10px 0 20px 0; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; width: 100%; }}
        .hour-card {{ flex: 0 0 auto; width: 155px; background: rgba(255, 255, 255, 0.95); border-top: 4px solid #0369A1; border-radius: 12px; padding: 10px; text-align: center; color: #1E293B !important; scroll-snap-align: start; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); }}
        .hour-card h4 {{ margin: 0 0 5px 0; color: #0369A1 !important; font-size: 1rem; font-weight: 800; border-bottom: 1px solid #E2E8F0; }}
        .hour-card p {{ margin: 3px 0; font-size: 0.8rem; font-weight: 600; color: #334155 !important; display: flex; justify-content: space-between; }}
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 25px; color: #1E293B; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
        .card-content {{ padding: 15px; }}
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
dm_m, dw_m = fetch_data()
ahora_local = datetime.now(ZONA_HORARIA)

tab0, tab1, tab2, tab3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

if dm_m and dw_m:
    # APLICAR FACTOR CORRECTOR
    ola_act = dm_m['hourly']['wave_height'][0] + f_ola
    v_viento = (dw_m['list'][0]['wind']['speed'] * 3.6) * f_viento
    
    with tab0:
        color_cls, status_txt = get_semaforo_info(ola_act, v_viento)
        _, _, coef_act = generar_marea_aprox(ahora_local)
        estrellas = calcular_actividad(ola_act, v_viento, coef_act, dm_m['hourly']['sea_surface_temperature'][0], dw_m['list'][0]['main']['pressure'])
        
        st.markdown(f"<div class='main-card'><div class='status-bar {color_cls}'></div><h1 style='margin-top:10px;'>MUTRIKU {ahora_local.strftime('%H:%M')}</h1><div style='font-weight:bold; color:#FBBF24;'>{status_txt}</div><div class='activity-badge'>Arrainen Jarduera: {estrellas}</div></div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ HAIZEA</h3><h2>{v_viento:.1f} <span class='big-arrow'>{flecha_desde(dw_m['list'][0]['wind']['deg'])}</span></h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f} <span class='big-arrow'>{flecha_desde(dm_m['hourly']['wave_direction'][0])}</span></h2></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ URA</h3><h2>{dm_m['hourly']['sea_surface_temperature'][0]:.1f}°</h2></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 KORR.</h3><h2>{dm_m['hourly']['ocean_current_velocity'][0]*3.6:.1f} <span class='big-arrow'>{flecha_hacia(dm_m['hourly']['ocean_current_direction'][0])}</span></h2></div>", unsafe_allow_html=True)
        
        st.write("### ⏱️ GAURKO EBOLUZIOA")
        html_c = "<div class='scroll-wrapper'>"
        for i in range(0, 12, 2):
            o = dm_m['hourly']['wave_height'][i] + f_ola
            v = (dw_m['list'][i//3]['wind']['speed']*3.6) * f_viento
            html_c += f"<div class='hour-card'><h4>{(ahora_local.hour+i)%24:02d}:00</h4><p>🌬️ {v:.0f} <span>{flecha_desde(dw_m['list'][i//3]['wind']['deg'])}</span></p><p>🌊 {o:.1f} <span>{flecha_desde(dm_m['hourly']['wave_direction'][i])}</span></p><span class='rec-badge'>{"KORTXOA" if o > 1 else "JIGGING"}</span></div>"
        st.markdown(html_c + "</div>", unsafe_allow_html=True)

    with tab1:
        st.header("📅 4 Eguneko Iragarpena")
        hoy = ahora_local.date()
        for i in range(1, 5):
            d = hoy + timedelta(days=i)
            p, b, coef = generar_marea_aprox(d)
            idx_12 = (i * 24) + 12
            o_d = dm_m['hourly']['wave_height'][idx_12] + f_ola
            v_d = (dw_m['list'][(idx_12//3)%len(dw_m['list'])]['wind']['speed']*3.6) * f_viento
            c_cls, s_txt = get_semaforo_info(o_d, v_d)
            estrellas_d = calcular_actividad(o_d, v_d, coef, dm_m['hourly']['sea_surface_temperature'][idx_12], 1015)
            
            html_day = f"<div class='day-forecast-card'><div class='status-bar {c_cls}'></div><div class='card-content'>"
            html_day += f"<div style='display:flex; justify-content:space-between; align-items:center;'><h3>{d.strftime('%A, %b %d')}</h3><b>{s_txt}</b></div>"
            html_day += f"<div class='activity-badge'>Jarduera: {estrellas_d}</div><div class='scroll-wrapper'>"
            for h_p in range(8, 23, 3):
                idx = (i * 24) + h_p
                o = dm_m['hourly']['wave_height'][idx] + f_ola
                v = (dw_m['list'][(idx//3)%len(dw_m['list'])]['wind']['speed']*3.6) * f_viento
                html_day += f"<div class='hour-card'><h4>{h_p:02d}:00</h4><p>🌬️ {v:.0f} <span>{flecha_desde(dw_m['list'][(idx//3)%len(dw_m['list'])]['wind']['deg'])}</span></p><p>🌊 {o:.1f} <span>{flecha_desde(dm_m['hourly']['wave_direction'][idx])}</span></p></div>"
            html_day += "</div></div></div>"
            st.markdown(html_day, unsafe_allow_html=True)

    with tab2:
        m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
        folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        plugins.MeasureControl(position='topright').add_to(m)
        plugins.Draw(position='topleft').add_to(m)
        st_folium(m, width="100%", height=500, key="plot_v330")

    with tab3:
        st.header("🐟 Kantauriko 10 Espezieak eta Apailuak")
        e1, e2 = st.columns(2)
        with e1:
            with st.expander("📌 1. SARGOA"):
                st.write("Aparraren erregea da. Olatuek arroketan jotzen duten lekuetan ibiltzen da. Itsasoa 0.8m eta 1.5m artean onena.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Línea 0.35mm. Bua 20-40g. Behea 2m Fluorocarbono (0.30mm). Amua Nº 1-2.</div>", unsafe_allow_html=True)
            with st.expander("🐠 2. LUBINA"):
                st.write("Oso arrain argia. Aparretan ehizatzen du. Spinningerako ezin hobea señueloekin egunsentian.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Trenzado 0.18mm. Behea 1m Fluorocarbono (0.40mm). Grapa azkarra señueloentzat.</div>", unsafe_allow_html=True)
            with st.expander("🐟 3. TXITXARROA"):
                st.write("Talde handietan ibiltzen da. Gauez portuko argietan hurbiltzen da. Kakea arina egiteko aproposa.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Sabiki aparejua luma zuriekin. Behea 0.30mm. Beruna 50g amaieran.</div>", unsafe_allow_html=True)
            with st.expander("🦑 4. TXIPIROIA"):
                st.write("Ur geldoak eta garbiak. Itsasbehera denean eta ilunabarrean hasten da mugimendua.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Trenzado 0.10mm. Behea 1.5m Fluorocarbono (0.22mm). Potera 2.0 neurrikoa.</div>", unsafe_allow_html=True)
            with st.expander("👑 5. URRABURUA"):
                st.write("Hondarrezko hondoetan ibiltzen da beita gogorren bila. Oso arrain mesfidatia da.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Montaje Corredizoa. Behea 3m Fluorocarbono (0.33mm). Amu indartsua.</div>", unsafe_allow_html=True)
        with e2:
            with st.expander("🦈 6. DENTOIA"):
                st.write("Hondo handietako harraparia. Kantilen eta hondo harritsuetan bizi da. Indar handiko arraina.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Zoka. Trenzado 0.30mm. Beruna 250g. Behea 1.5m (0.70mm). Amuak tándem.</div>", unsafe_allow_html=True)
            with st.expander("🐚 7. MOXARRA"):
                st.write("Ur lasaiagoetan ibiltzen da. Harri inguruetan kortxoarekin arrantzatzen da zizareekin.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Linea 0.30mm. Bua arina. Behea 0.22mm. Amua Nº 8 txikia.</div>", unsafe_allow_html=True)
            with st.expander("🦐 8. BARBINA"):
                st.write("Hondarrezko hondoetan bizi da lurra mugituz. Usain handiko beitak behar dituzte.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Chambel. 3 gameta motz lerroan. Amuak Nº 12 tija luzekoak. Beita: Coreana.</div>", unsafe_allow_html=True)
            with st.expander("Scorpaena 9. KABRARROKA"):
                st.write("Harri puruan bizi da. Hondoan txipiroi tirekin arrantzatu. Kontuz arantzekin desanzuelatzerakoan.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Paternoster. Linea nagusia 0.45mm. Behea 0.35mm sendoa. Amua Nº 1.</div>", unsafe_allow_html=True)
            with st.expander("Boops 10. BOGA"):
                st.write("Ur erdi eta azaletik hurbil ibiltzen da. Talde handiak sortzen ditu eta oso gosetia da.")
                st.markdown("<div class='rig-info'><b>🛠️ APAILUA:</b> Linea 0.18mm. Bua pluma motakoa. Amua Nº 14 oso txikia. Beita: Ogia.</div>", unsafe_allow_html=True)
