import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN Y ESTILOS BLINDADOS ---
st.set_page_config(page_title="Txomin v.31.4 - Tácticas de Pesca", page_icon="🔱", layout="wide")

API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38

IMG_FONDO_MAR = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/fondo_cantabrico.jpg"
IMG_SARGO = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/especies/sargo.jpg"
IMG_CHICHARRO = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/especies/chicharro.jpg"
IMG_CHIPIRON = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/especies/chipiron.jpg"
IMG_CABRARROCA = "https://raw.githubusercontent.com/txomin-plotter/txomin-plotter/main/assets/especies/cabrarroca.jpg"

st.markdown(f"""
    <style>
        .stApp {{ background-image: url("{IMG_FONDO_MAR}"); background-size: cover; background-attachment: fixed; background-position: center; background-color: #011627; color: white; }}
        .main-card {{ background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); color: white; padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 25px; border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37); }}
        .metric-card {{ background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.3); transition: 0.3s ease; }}
        .metric-card:hover {{ transform: translateY(-3px); background: rgba(255, 255, 255, 0.25); }}
        .metric-card h3 {{ color: white !important; margin-bottom: 5px; font-size: 1.1rem; }}
        .metric-card h2 {{ color: #FBBF24 !important; font-size: 2.2rem; margin: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }}
        .metric-card p {{ color: rgba(255, 255, 255, 0.9) !important; margin: 0; font-size: 0.95rem; font-weight: 500; }}
        .scroll-wrapper {{ display: flex; overflow-x: auto; gap: 15px; padding: 15px 0; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; }}
        .scroll-wrapper::-webkit-scrollbar {{ display: none; }}
        .hour-card {{ flex: 0 0 auto; width: 170px; background: rgba(255, 255, 255, 0.2); backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.4); border-radius: 15px; padding: 15px; text-align: center; color: white !important; scroll-snap-align: start; box-shadow: 2px 2px 10px rgba(0,0,0,0.2); }}
        .hour-card h4 {{ margin: 0 0 10px 0; color: #BAE6FD !important; font-size: 1.3rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }}
        .hour-card p {{ margin: 6px 0; font-size: 1rem; line-height: 1.3; font-weight: 500; color: white !important;}}
        .hour-card .rec-badge {{ background: #059669; color: white; border-radius: 8px; padding: 4px 0; margin-top: 10px; font-weight: bold; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }}
        .eval-container {{ background: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; color: #1E293B; box-shadow: 0 4px 15px rgba(0,0,0,0.1); height: 100%; }}
        .rec-image {{ border-radius: 10px; width: 100%; height: 150px; object-fit: cover; margin-bottom: 15px; border: 2px solid #BAE6FD; background-color: #BAE6FD; }}
        
        /* Estilos Tarjetas 4 Días */
        .day-forecast-card {{ background: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; margin-bottom: 15px; color: #1E293B; border-left: 8px solid #0369A1; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
        .day-forecast-title {{ font-size: 1.3rem; font-weight: bold; color: #0369A1; margin-bottom: 10px; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; }}
        .day-metrics-row {{ display: flex; justify-content: space-between; flex-wrap: wrap; margin-bottom: 10px; font-size: 1.05rem; }}
        .day-metrics-row div {{ background: #F1F5F9; padding: 8px 12px; border-radius: 8px; margin: 5px 5px 0 0; border: 1px solid #CBD5E1; }}
        .day-tech-row {{ background: #ECFDF5; border: 1px solid #10B981; padding: 12px; border-radius: 8px; margin-top: 10px; font-size: 1rem; color: #065F46; }}
        
        .stTabs [data-baseweb="tab"] {{ background-color: rgba(240, 249, 255, 0.8); backdrop-filter: blur(5px); border-radius: 10px; padding: 12px 20px; font-weight: bold; color: #0369A1; }}
        .stTabs [aria-selected="true"] {{ background-color: #0369A1 !important; color: white !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES LÓGICAS ---
def dir_viento_real(grados):
    dirs = ["N ↓", "NE ↙", "E ←", "SE ↖", "S ↑", "SO ↗", "O →", "NO ↘"]
    return dirs[round(grados / 45) % 8]

def generar_marea_aprox(fecha_target):
    # Simulador básico de mareas para Mutriku basado en fechas de finales de marzo / abril 2026
    dia = fecha_target.day
    plea = f"{(dia % 12) + 2:02d}:{(dia * 7 % 60):02d}"
    baja = f"{((dia % 12) + 2 + 6) % 24:02d}:{(dia * 7 % 60 + 15) % 60:02d}"
    coef = 50 + (dia * 3 % 45) # Simula un coeficiente entre 50 y 95
    return plea, baja, coef

def recomendacion_tecnica(ola, viento, corriente):
    if ola > 2.2 or viento > 30:
        return "🛑 PUERTO", "Condiciones peligrosas. Aprovecha para revisar los aparejos en tierra."
    elif 0.8 <= ola <= 1.8 and viento < 20:
        return "🎣 CORCHO / SPINNING", "La espuma es ideal. Busca canales entre las rocas y lanza cerca de la rompiente."
    elif viento >= 10 and ola < 1.3:
        return "🚤 CACEA LIGERA", "Viento rizando la superficie. Saca plumillas blancas o vinilos pequeños y trolea a 3 nudos."
    elif ola < 1.0 and corriente < 1.0:
        return "⚓ JIGGING / VERTICAL", "Poca deriva y agua parada. Ideal para buscar pescado de roca en vertical sobre marcas exactas."
    else:
        return "🪨 FONDEADO", "Busca resguardo del viento, echa el ancla y usa aparejos de chambel con plomo pesado al fondo."

@st.cache_data(ttl=600)
def fetch_data():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

def recomendacion_especie_real(ola, viento):
    if 0.8 <= ola <= 1.8: return "🐟 SARGO", "Espuma constante. Usa macizo.", IMG_SARGO
    if ola < 0.7 and viento < 12: return "🦑 CHIPIRÓN", "Mar plato. Poteras de 2.0.", IMG_CHIPIRON
    if viento >= 10 and ola < 1.3: return "🐠 CHICHARRO", "Superficie rizada. Cacea.", IMG_CHICHARRO
    return "🦂 CABRARROCA", "Piedra pura. Fondo pesado.", IMG_CABRARROCA

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.31.4 - Tácticas de Pesca")

# ARREGLADO: Pestañas limpias y sin cruces
tab0, tab1, tab2, tab3 = st.tabs(["⚓ ESTADO DEL MAR", "📅 PREVISIÓN 4 DÍAS", "🗺️ MAPA IHM", "🐟 ESPECIES CANTÁBRICO"])

dm_m, dw_m = fetch_data()

# --- TAB 0: CARRUSEL (Actual) ---
with tab0:
    if dm_m and 'hourly' in dm_m and dw_m and 'list' in dw_m:
        ola_act = dm_m['hourly']['wave_height'][0]
        ola_dir = dm_m['hourly']['wave_direction'][0]
        temp_agua = dm_m['hourly']['sea_surface_temperature'][0]
        v_corr = dm_m['hourly']['ocean_current_velocity'][0] * 3.6
        v_viento = dw_m['list'][0]['wind']['speed'] * 3.6
        d_viento = dir_viento_real(dw_m['list'][0]['wind']['deg'])
        
        st.markdown(f"<div class='main-card'><h1 style='margin:0; font-size: 2.8rem;'>MUTRIKU AHORA</h1><p style='font-size:1.2rem; opacity:0.9;'>{datetime.now().strftime('%H:%M')}</p></div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ VIENTO</h3><h2>{v_viento:.1f}</h2><p>km/h {d_viento}</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f}</h2><p>m (Dir: {ola_dir}°)</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ AGUA</h3><h2>{temp_agua:.1f}</h2><p>°C</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 CORRIENTE</h3><h2>{v_corr:.1f}</h2><p>km/h</p></div>", unsafe_allow_html=True)

        st.divider()
        
        st.markdown("<h3 style='color:white; text-shadow: 1px 1px 3px black;'>EVOLUCIÓN TÁCTICA HOY (Desliza 👉)</h3>", unsafe_allow_html=True)
        html_carrusel = "<div class='scroll-wrapper'>"
        for i in range(0, min(8, len(dw_m['list']))):
            item = dw_m['list'][i]
            hora_dt = datetime.fromtimestamp(item['dt'])
            idx_marine = i * 3
            if idx_marine < len(dm_m['hourly']['wave_height']):
                c_ola = dm_m['hourly']['wave_height'][idx_marine]
                c_viento = item['wind']['speed'] * 3.6
                c_corr = dm_m['hourly']['ocean_current_velocity'][idx_marine] * 3.6
                tec_nombre, _ = recomendacion_tecnica(c_ola, c_viento, c_corr)
                
                html_carrusel += f"<div class='hour-card'><h4>{hora_dt.strftime('%H:%M')}</h4><p>🌬️ {c_viento:.1f} km/h</p><p>🌊 {c_ola:.1f} m</p><div class='rec-badge'>{tec_nombre.split(' ')[1]}</div></div>"
        
        html_carrusel += "</div>"
        st.markdown(html_carrusel, unsafe_allow_html=True)

# --- TAB 1: NUEVA PREVISIÓN 4 DÍAS CON TÉCNICAS ---
with tab1:
    st.header("📅 Planificador de Salidas (Próximos 4 Días)")
    if dw_m and 'list' in dw_m:
        hoy = datetime.now().date()
        for i in range(1, 5): 
            dia_target = hoy + timedelta(days=i)
            plea, baja, coef = generar_marea_aprox(dia_target)
            
            # Buscamos el parte de las 12:00
            item_mediodia = None
            for item in dw_m['list']:
                dt_item = datetime.fromtimestamp(item['dt'])
                if dt_item.date() == dia_target and dt_item.hour == 12:
                    item_mediodia = item
                    break
            
            if item_mediodia:
                idx_ow = dw_m['list'].index(item_mediodia)
                idx_marine = idx_ow * 3
                
                if idx_marine < len(dm_m['hourly']['wave_height']):
                    o_prev = dm_m['hourly']['wave_height'][idx_marine]
                    v_prev = item_mediodia['wind']['speed'] * 3.6
                    v_dir = dir_viento_real(item_mediodia['wind']['deg'])
                    c_prev = dm_m['hourly']['ocean_current_velocity'][idx_marine] * 3.6
                    
                    tec_nom, tec_tip = recomendacion_tecnica(o_prev, v_prev, c_prev)
                    
                    st.markdown(f"""
                    <div class='day-forecast-card'>
                        <div class='day-forecast-title'>{dia_target.strftime('%A, %d de %B').capitalize()}</div>
                        
                        <div class='day-metrics-row'>
                            <div>🌬️ <b>Viento:</b> {v_prev:.1f} km/h {v_dir}</div>
                            <div>🌊 <b>Ola:</b> {o_prev:.1f} m</div>
                            <div>💧 <b>Corriente:</b> {c_prev:.1f} km/h</div>
                        </div>
                        
                        <div class='day-metrics-row' style='background:#E0F2FE; border:1px solid #BAE6FD;'>
                            <div>🔼 <b>Plea:</b> {plea}</div>
                            <div>🔽 <b>Baja:</b> {baja}</div>
                            <div>🌊 <b>Coef:</b> {coef}</div>
                        </div>
                        
                        <div class='day-tech-row'>
                            <b>🎯 Técnica Recomendada: {tec_nom}</b><br>
                            {tec_tip}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.error("Error cargando datos de previsión.")

# --- TAB 2: MAPA (Corregido y separado) ---
with tab2:
    st.subheader("🗺️ Plotter IHM Mutriku")
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    st_folium(m, width="100%", height=500, key="mapa_v31")

# --- TAB 3: ESPECIES ---
with tab3:
    st.header("🐟 Top 10 Especies del Cantábrico")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        with st.expander("1. SARGO"): st.write("Rey de la espuma. Mar: 0.8m-1.5m. Corcho o fondo. Cebo: Gamba/Masilla.")
        with st.expander("2. LUBINA"): st.write("Rompientes. Amanecer/anochecer. Spinning con minnows o vivo.")
        with st.expander("3. CHICHARRO"): st.write("Cacea ligera a 3 nudos con plumillas blancas cuando el mar se riza.")
        with st.expander("4. CHIPIRÓN"): st.write("Aguas paradas y atardecer. Poteras de 2.0 con tirones suaves.")
        with st.expander("5. DORADA"): st.write("Fondo mixto. Cebo duro (cangrejo, navaja).")
    with col_e2:
        with st.expander("6. DENTÓN"): st.write("Grandes fondos. Jigging pesado o vivo (sepia/calamar).")
        with st.expander("7. MOJARRA"): st.write("Aguas más tranquilas. Fondo o corcho cerca de las piedras.")
        with st.expander("8. SALMONETE"): st.write("Fondos de arena. Anzuelos finos con gusana.")
        with st.expander("9. CABRARROCA"): st.write("Piedra pura. Fondo pesado con tiras de chipirón.")
        with st.expander("10. BOGA"): st.write("Medias aguas. Corcho ligero. Divertido para niños.")
