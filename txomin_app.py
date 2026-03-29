import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN Y ESTILOS SUPER ESPECTACULARES ---
st.set_page_config(page_title="Txomin v.31.1 - Edición Mutriku Pro", page_icon="🔱", layout="wide")

# Clave OpenWeather (¡Asegúrate de tenerla en Secrets!)
API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38

# --- IMÁGENES REALES DE ESPECIES Y FONDO ---
IMG_FONDO_MAR = "https://images.unsplash.com/photo-1518302015037-fe0a9202570b?q=80&w=2000&blur=10"
IMG_SARGO = "https://images.unsplash.com/photo-1594165561081-308be7e57c66?q=80&w=600"
IMG_CHICHARRO = "https://images.unsplash.com/photo-1616432041793-11816e83d8e5?q=80&w=600"
IMG_CHIPIRON = "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?q=80&w=600"
IMG_CABRARROCA = "https://images.unsplash.com/photo-1611283626245-c800c0071337?q=80&w=600"

# Estilos CSS Avanzados: Fondo Marino y Glassmorphism Pro
st.markdown(f"""
    <style>
        /* Fondo Marino Dinámico */
        .stApp {{
            background-image: url("{IMG_FONDO_MAR}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}
        
        /* Contenedores de Cristal (Glassmorphism) */
        .main-card {{
            background: rgba(3, 105, 161, 0.7); /* Azul translúcido */
            backdrop-filter: blur(10px);
            color: white;
            padding: 25px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        
        .metric-card {{
            background: rgba(255, 255, 255, 0.15); /* Vidrio esmerilado */
            backdrop-filter: blur(5px);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.25);
        }}
        .metric-card h3 {{ color: white; margin-bottom: 5px; font-size: 1.1rem; }}
        .metric-card h2 {{ color: #FBBF24; font-size: 2.2rem; margin: 0; }} /* Dorado para valor */
        .metric-card p {{ color: rgba(255, 255, 255, 0.8); margin: 0; font-size: 0.9rem; }}
        
        /* CARRUSEL DESLIZABLE (SWIPE) CADA 2 HORAS */
        .scroll-wrapper {{
            display: flex;
            overflow-x: auto;
            gap: 15px;
            padding: 15px 0;
            scroll-snap-type: x mandatory;
            -webkit-overflow-scrolling: touch; /* Suavidad en iOS */
        }}
        .scroll-wrapper::-webkit-scrollbar {{
            display: none; /* Oculta la barra en móviles */
        }}
        .hour-card {{
            flex: 0 0 auto;
            width: 170px;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.4);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            color: white;
            scroll-snap-align: start;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
            transition: 0.3s ease;
        }}
        .hour-card:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.02);
        }}
        .hour-card h4 {{ margin: 0 0 10px 0; color: #BAE6FD; font-size: 1.3rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }}
        .hour-card p {{ margin: 6px 0; font-size: 1rem; line-height: 1.3; font-weight: 500; }}
        
        .hour-card .rec-badge {{
            background: #059669; /* Verde Sostenible */
            color: white;
            border-radius: 8px;
            padding: 4px 0;
            margin-top: 10px;
            font-weight: bold;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Evaluación y Especie */
        .eval-container {{
            background: rgba(255, 255, 255, 0.95); /* Fondo blanco casi sólido */
            border-radius: 15px;
            padding: 20px;
            color: #1E293B;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            height: 100%; /* Para igualar alturas */
        }}
        .rec-image {{
            border-radius: 10px;
            width: 100%;
            height: 150px;
            object-fit: cover;
            margin-bottom: 15px;
            border: 2px solid #BAE6FD;
        }}
        
        /* Restyling Tabs */
        .stTabs [data-baseweb="tab"] {{ background-color: rgba(240, 249, 255, 0.8); backdrop-filter: blur(5px); border-radius: 10px; padding: 12px 20px; font-weight: bold; color: #0369A1; }}
        .stTabs [aria-selected="true"] {{ background-color: #0369A1 !important; color: white !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES DE APOYO Y DATOS ---
def dir_viento_real(grados):
    dirs = ["N ↓", "NE ↙", "E ←", "SE ↖", "S ↑", "SO ↗", "O →", "NO ↘"]
    return dirs[round(grados / 45) % 8]

def evaluar_pesca(ola, viento):
    puntos = 10
    if ola > 2.0: puntos -= 5
    if viento > 25: puntos -= 3
    if 0.8 < ola < 1.5: puntos += 2 # Ideal para sargo
    
    nota = max(0, min(10, puntos))
    if nota > 7: return f"🔥 EXCELENTE ({nota}/10)", "Día perfecto. Condiciones estables y mar ideal para las especies clave."
    elif nota > 4: return f"⚖️ REGULAR ({nota}/10)", "Se puede pescar, pero busca zonas resguardadas de la corriente y el viento."
    return f"⚠️ MALA ({nota}/10)", "Mar complicada o demasiado fuerte. Se recomienda precaución extrema fuera del puerto."

def recomendacion_especie_real(ola, viento):
    # Devuelve: (Nombre, TipTactico, ImagenReal)
    if ola > 0.8 and ola < 1.8:
        return "🐟 SARGO", "Consejo: Busca puestas con espuma blanca constante. Usa macizo de anchoa o gamba pelada.", IMG_SARGO
    if ola < 0.7 and viento < 12:
        return "🦑 CHIPIRÓN", "Consejo: Mareas muertas y mar plato. Trabaja poteras de tamaño 2.0 en zonas de calma al atardecer.", IMG_CHIPIRON
    if viento >= 10 and ola < 1.3:
        return "🐠 CHICHARRO", "Consejo: El viento riza la superficie; es el momento ideal para meter plumillas blancas a 3 nudos.", IMG_CHICHARRO
    return "🦂 CABRARROCA", "Consejo: Fondea en piedra dura pura y usa chambel con plomo pesado y tiras de chipirón.", IMG_CABRARROCA

@st.cache_data(ttl=600)
def fetch_data():
    try:
        # Open-Meteo para datos marinos (Ola y Corriente cada 1h)
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,sea_surface_temperature&timezone=auto"
        # OpenWeather para datos de viento (Previsión cada 3h)
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        
        res_m = requests.get(url_m).json()
        res_w = requests.get(url_w).json()
        
        return res_m, res_w
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None, None

# --- 3. INTERFAZ ESPECTACULAR ---
st.title("🔱 Txomin v.31.1 - Edición Mutriku Pro")

tab0, tab1, tab2 = st.tabs(["⚓ ESTADO DEL MAR PRO", "🗺️ MAPA IHM", "🐟 INFORMACIÓN LEGAL"])

dm_m, dw_m = fetch_data()

# --- TAB INICIAL: TORRE DE CONTROL ESPECTACULAR CON CARRUSEL ---
with tab0:
    if dm_m and 'hourly' in dm_m and dw_m and 'list' in dw_m:
        # Datos del momento actual (Índice 0)
        ola_act = dm_m['hourly']['wave_height'][0]
        ola_dir = dm_m['hourly']['wave_direction'][0]
        temp_agua = dm_m['hourly']['sea_surface_temperature'][0]
        v_corr = dm_m['hourly']['ocean_current_velocity'][0] * 3.6
        
        # OpenWeather current wind (index 0 of forecast list is near current time)
        v_viento = dw_m['list'][0]['wind']['speed'] * 3.6
        d_viento = dir_viento_real(dw_m['list'][0]['wind']['deg'])
        
        # 1. PORTADA GIGANTE
        st.markdown(f"""
            <div class='main-card'>
                <h1 style='margin:0; font-size: 2.8rem;'>MUTRIKU AHORA</h1>
                <p style='font-size:1.4rem; opacity:0.9;'>Previsión Táctica: {datetime.now().strftime('%H:%M')}</p>
            </div>
        """, unsafe_allow_html=True)

        # Métricas de Cristal
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><h3>🌬️ VIENTO</h3><h2>{v_viento:.1f} km/h</h2><p>{d_viento}</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f} m</h2><p>Dir: {ola_dir}°</p></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><h3>🌡️ AGUA</h3><h2>{temp_agua:.1f} °C</h2><p>Superficie</p></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-card'><h3>💧 CORRIENTE</h3><h2>{v_corr:.1f} km/h</h2><p>Velocidad</p></div>", unsafe_allow_html=True)

        st.divider()
        
        # Evaluación y Especie con Imagen Real
        col_eval, col_esp = st.columns(2)
        eval_txt, eval_desc = evaluar_pesca(ola_act, v_viento)
        esp_nombre, esp_tip, esp_img = recomendacion_especie_real(ola_act, v_viento)
        
        with col_eval:
            st.markdown(f"""<div class='eval-container'>
                <h3 style='margin:0 0 10px 0; color:#0369A1;'>📈 ACTIVIDAD DE PESCA</h3>
                <h2 style='margin:0;'>{eval_txt}</h2>
                <p style='margin-bottom:0;'>{eval_desc}</p>
            </div>""", unsafe_allow_html=True)
            
        with col_esp:
            st.markdown(f"""<div class='eval-container'>
                <img src='{esp_img}' class='rec-image'/>
                <h2 style='margin:0; color:#059669;'>{esp_nombre}</h2>
                <p><b>Consejo Táctico:</b> {esp_tip}</p>
            </div>""", unsafe_allow_html=True)

        # 2. CARRUSEL DESLIZABLE (SWIPE) CADk 2 HORAS
        st.markdown("<h3 style='color:white; margin-top:35px; text-shadow: 1px 1px 3px black;'>EVOLUCIÓN DEL DÍA (Desliza 👉)</h3>", unsafe_allow_html=True)
        
        # Iniciamos el envoltorio del carrusel HTML
        html_carrusel = "<div class='scroll-wrapper'>"
        
        # Cogemos las próximas 24 horas (OpenWeather da cada 3h, cogemos 8 items)
        for i in range(0, min(8, len(dw_m['list']))):
            item = dw_m['list'][i]
            hora_dt = datetime.fromtimestamp(item['dt'])
            
            # Sincronizamos índice de OpenWeather con Open-Meteo (Open-Meteo es horario, OW es 3h)
            idx_marine = i * 3
            if idx_marine < len(dm_m['hourly']['wave_height']):
                c_ola = dm_m['hourly']['wave_height'][idx_marine]
                c_viento = item['wind']['speed'] * 3.6
                c_dir_v = dir_viento_real(item['wind']['deg'])
                # Obtenemos solo el nombre de la especie
                c_esp, _, _ = recomendacion_especie_real(c_ola, c_viento)
                
                html_carrusel += f"""
                <div class='hour-card'>
                    <h4>{hora_dt.strftime('%H:%M')}</h4>
                    <p>🌬️ {c_viento:.1f} km/h<br>{c_dir_v}</p>
                    <p>🌊 {c_ola:.1f} m</p>
                    <div class='rec-badge'>{c_esp}</div>
                </div>
                """
        
        # Cerramos el envoltorio del carrusel
        html_carrusel += "</div>"
        
        # Renderizamos el carrusel en Streamlit
        st.markdown(html_carrusel, unsafe_allow_html=True)

    else:
        st.warning("📡 Conectando con los satélites marinos... Espera unos segundos.")

# --- PESTAÑA 2: MAPA (Se mantiene igual, funcional) ---
with tab1:
    st.subheader("🗺️ Plotter IHM Mutriku")
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    st_folium(m, width="100%", height=500, key="mapa_v31")

# --- PESTAÑA 3: LEGALIDAD (Requisito de Euskadi) ---
with tab2:
    st.header("⚖️ Marco Legal de Pesca Recreativa")
    st.info("De acuerdo con la legislación vigente en Euskadi, se recuerda a los usuarios respetar escrupulosamente las tallas mínimas, los cupos máximos por licencia y especie, y los períodos de veda establecidos por el Gobierno Vasco. La práctica de la pesca recreativa debe ser siempre sostenible y respetuosa con el medio marino.")
