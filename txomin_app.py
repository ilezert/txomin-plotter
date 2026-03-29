import streamlit as stimport streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Txomin v.31 - Portada Táctil", page_icon="🔱", layout="wide")

API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38

# Imágenes de fondo y especies
IMG_FONDO_MAR = "https://images.unsplash.com/photo-1518302015037-fe0a9202570b?q=80&w=2000&blur=10"
IMG_SARGO = "https://images.unsplash.com/photo-1594165561081-308be7e57c66?q=80&w=600"
IMG_CHICHARRO = "https://images.unsplash.com/photo-1616432041793-11816e83d8e5?q=80&w=600"
IMG_CHIPIRON = "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?q=80&w=600"
IMG_CABRARROCA = "https://images.unsplash.com/photo-1611283626245-c800c0071337?q=80&w=600"

st.markdown(f"""
    <style>
        .stApp {{
            background-image: url("{IMG_FONDO_MAR}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}
        .main-card {{
            background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); color: white;
            padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 15px;
            padding: 15px; text-align: center; color: white !important; border: 1px solid rgba(255, 255, 255, 0.3);
        }}
        .metric-card h3 {{ margin-bottom: 5px; font-size: 1.1rem; }}
        .metric-card h2 {{ color: #FBBF24; font-size: 2rem; margin: 0; }}
        
        /* CARRUSEL DESLIZABLE (SWIPE) */
        .scroll-wrapper {{
            display: flex; overflow-x: auto; gap: 15px; padding: 10px 0; scroll-snap-type: x mandatory;
        }}
        .scroll-wrapper::-webkit-scrollbar {{ display: none; }} /* Oculta la barra en móviles */
        .hour-card {{
            flex: 0 0 auto; width: 160px; background: rgba(255, 255, 255, 0.2); backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.4); border-radius: 15px; padding: 15px;
            text-align: center; color: white; scroll-snap-align: start;
        }}
        .hour-card h4 {{ margin: 0 0 10px 0; color: #BAE6FD; font-size: 1.2rem; }}
        .hour-card p {{ margin: 5px 0; font-size: 0.95rem; line-height: 1.3; }}
        .hour-card .rec-badge {{ background: #059669; border-radius: 5px; padding: 3px 0; margin-top: 8px; font-weight: bold; font-size: 0.85rem; }}
        
        .eval-container {{
            background: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; color: #1E293B;
        }}
        .rec-image {{ border-radius: 10px; width: 100%; height: 140px; object-fit: cover; margin-bottom: 10px; }}
        .stTabs [data-baseweb="tab"] {{ background-color: rgba(240, 249, 255, 0.8); border-radius: 10px; padding: 12px 20px; color: #0369A1; }}
        .stTabs [aria-selected="true"] {{ background-color: #0369A1 !important; color: white !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES LÓGICAS ---
def dir_viento_real(grados):
    dirs = ["N ↓", "NE ↙", "E ←", "SE ↖", "S ↑", "SO ↗", "O →", "NO ↘"]
    return dirs[round(grados / 45) % 8]

def evaluar_pesca(ola, viento):
    puntos = 10
    if ola > 2.0: puntos -= 5
    if viento > 25: puntos -= 3
    if 0.8 < ola < 1.5: puntos += 2
    nota = max(0, min(10, puntos))
    if nota > 7: return f"🔥 EXCELENTE ({nota}/10)", "Día perfecto. Condiciones estables para salir."
    elif nota > 4: return f"⚖️ REGULAR ({nota}/10)", "Pesca posible, pero busca zonas resguardadas."
    return f"⚠️ MALA ({nota}/10)", "Mar complicada. Mejor revisar equipo en puerto."

def recomendacion_especie_real(ola, viento):
    # Tip de pesca integrado para cada especie recomendado en Txomin
    if 0.8 <= ola <= 1.8: return "🐟 SARGO", "Tip: Busca zonas con buena espuma y usa macizo de anchoa o gamba pelada.", IMG_SARGO
    if ola < 0.7 and viento < 12: return "🦑 CHIPIRÓN", "Tip: Trabaja poteras de tamaño 2.0 o 2.5 con tirones muy suaves al atardecer.", IMG_CHIPIRON
    if viento >= 10 and ola < 1.3: return "🐠 CHICHARRO", "Tip: El viento riza la superficie; es el momento ideal para meter plumillas blancas a 3 nudos.", IMG_CHICHARRO
    return "🦂 CABRARROCA", "Tip: Fondea en piedra dura pura y usa chambel con plomo pesado y tiras de chipirón.", IMG_CABRARROCA

@st.cache_data(ttl=600)
def fetch_data():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={lon_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# Parche temporal de coordenadas en fetch_data por error tipográfico (lon_MUTRIKU a LON_MUTRIKU)
@st.cache_data(ttl=600)
def fetch_data_fix():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.31.0 - Mutriku Pro")

tab0, tab1, tab2 = st.tabs(["⚓ ESTADO DEL MAR", "🗺️ MAPA IHM", "🐟 INFO LEGAL"])

dm_m, dw_m = fetch_data_fix()

# --- PESTAÑA PRINCIPAL: PORTADA Y CARRUSEL ---
with tab0:
    if dm_m and 'hourly' in dm_m and dw_m and 'list' in dw_m:
        # Datos del momento exacto actual
        ola_act = dm_m['hourly']['wave_height'][0]
        ola_dir = dm_m['hourly']['wave_direction'][0]
        temp_agua = dm_m['hourly']['sea_surface_temperature'][0]
        v_corr = dm_m['hourly']['ocean_current_velocity'][0] * 3.6
        
        # OpenWeather forecast list item 0 for current wind
        v_viento = dw_m['list'][0]['wind']['speed'] * 3.6
        d_viento = dir_viento_real(dw_m['list'][0]['wind']['deg'])
        
        # 1. PORTADA GIGANTE
        st.markdown(f"""
            <div class='main-card'>
                <h1 style='margin:0; font-size: 2.5rem;'>MUTRIKU AHORA</h1>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ VIENTO</h3><h2>{v_viento:.1f}</h2><p>km/h {d_viento}</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f}</h2><p>m (Dir: {ola_dir}°)</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ AGUA</h3><h2>{temp_agua:.1f}</h2><p>°C Superficie</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 CORRIENTE</h3><h2>{v_corr:.1f}</h2><p>km/h</p></div>", unsafe_allow_html=True)

        st.divider()
        
        col_eval, col_esp = st.columns(2)
        eval_txt, eval_desc = evaluar_pesca(ola_act, v_viento)
        esp_nombre, esp_tip, esp_img = recomendacion_especie_real(ola_act, v_viento)
        
        with col_eval:
            st.markdown(f"""<div class='eval-container'>
                <h3 style='margin:0 0 10px 0; color:#0369A1;'>📈 ACTIVIDAD</h3>
                <h2 style='margin:0;'>{eval_txt}</h2><p>{eval_desc}</p>
            </div>""", unsafe_allow_html=True)
        with col_esp:
            st.markdown(f"""<div class='eval-container'>
                <img src='{esp_img}' class='rec-image'/>
                <h2 style='margin:0; color:#059669;'>{esp_nombre}</h2>
                <p><b>CONSEJO:</b> {esp_tip}</p>
            </div>""", unsafe_allow_html=True)

        # 2. CARRUSEL DESLIZABLE (SWIPE) CADA 2 HORAS
        st.markdown("<h3 style='color:white; margin-top:30px; text-shadow: 1px 1px 2px black;'>EVOLUCIÓN DEL DÍA (Desliza 👉)</h3>", unsafe_allow_html=True)
        
        html_carrusel = "<div class='scroll-wrapper'>"
        
        # Cogemos las próximas 24 horas saltando de 2 en 2 (12 tarjetas)
        for i in range(0, min(12, len(dw_m['list']))):
            item = dw_m['list'][i]
            # Sincronizamos índice de OpenWeather (cada 3h) con Open-Meteo (cada 1h) aproximando
            hora_dt = datetime.fromtimestamp(item['dt'])
            idx_marine = i * 3 
            
            if idx_marine < len(dm_m['hourly']['wave_height']):
                c_ola = dm_m['hourly']['wave_height'][idx_marine]
                c_viento = item['wind']['speed'] * 3.6
                c_dir_v = dir_viento_real(item['wind']['deg'])
                c_esp, _, _ = recomendacion_especie_real(c_ola, c_viento)
                
                html_carrusel += f"""
                <div class='hour-card'>
                    <h4>{hora_dt.strftime('%H:%M')}</h4>
                    <p>🌬️ {c_viento:.1f} km/h {c_dir_v}</p>
                    <p>🌊 {c_ola:.1f} m</p>
                    <div class='rec-badge'>{c_esp.split(" ")[1]}</div>
                </div>
                """
        
        html_carrusel += "</div>"
        st.markdown(html_carrusel, unsafe_allow_html=True)

# --- PESTAÑA 2: MAPA ---
with tab1:
    st.subheader("🗺️ Plotter IHM Mutriku")
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    st_folium(m, width="100%", height=500, key="mapa_v31")

# --- PESTAÑA 3: LEGALIDAD ---
with tab2:
    st.header("⚖️ Marco Legal de Pesca")
    st.info("De acuerdo con la legislación vigente en Euskadi, se recuerda a los usuarios respetar escrupulosamente las tallas mínimas, los cupos máximos por licencia y especie, y los períodos de veda establecidos por el Gobierno Vasco. La práctica de la pesca recreativa debe ser siempre sostenible y respetuosa con el medio marino.")
import requests
import pandas as pd
import os
from datetime import datetime
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Txomin v.31 - Portada Táctil", page_icon="🔱", layout="wide")

API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38

# Imágenes de fondo y especies
IMG_FONDO_MAR = "https://images.unsplash.com/photo-1518302015037-fe0a9202570b?q=80&w=2000&blur=10"
IMG_SARGO = "https://images.unsplash.com/photo-1594165561081-308be7e57c66?q=80&w=600"
IMG_CHICHARRO = "https://images.unsplash.com/photo-1616432041793-11816e83d8e5?q=80&w=600"
IMG_CHIPIRON = "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?q=80&w=600"
IMG_CABRARROCA = "https://images.unsplash.com/photo-1611283626245-c800c0071337?q=80&w=600"

st.markdown(f"""
    <style>
        .stApp {{
            background-image: url("{IMG_FONDO_MAR}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}
        .main-card {{
            background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); color: white;
            padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(5px); border-radius: 15px;
            padding: 15px; text-align: center; color: white !important; border: 1px solid rgba(255, 255, 255, 0.3);
        }}
        .metric-card h3 {{ margin-bottom: 5px; font-size: 1.1rem; }}
        .metric-card h2 {{ color: #FBBF24; font-size: 2rem; margin: 0; }}
        
        /* CARRUSEL DESLIZABLE (SWIPE) */
        .scroll-wrapper {{
            display: flex; overflow-x: auto; gap: 15px; padding: 10px 0; scroll-snap-type: x mandatory;
        }}
        .scroll-wrapper::-webkit-scrollbar {{ display: none; }} /* Oculta la barra en móviles */
        .hour-card {{
            flex: 0 0 auto; width: 160px; background: rgba(255, 255, 255, 0.2); backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.4); border-radius: 15px; padding: 15px;
            text-align: center; color: white; scroll-snap-align: start;
        }}
        .hour-card h4 {{ margin: 0 0 10px 0; color: #BAE6FD; font-size: 1.2rem; }}
        .hour-card p {{ margin: 5px 0; font-size: 0.95rem; line-height: 1.3; }}
        .hour-card .rec-badge {{ background: #059669; border-radius: 5px; padding: 3px 0; margin-top: 8px; font-weight: bold; font-size: 0.85rem; }}
        
        .eval-container {{
            background: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 20px; color: #1E293B;
        }}
        .rec-image {{ border-radius: 10px; width: 100%; height: 140px; object-fit: cover; margin-bottom: 10px; }}
        .stTabs [data-baseweb="tab"] {{ background-color: rgba(240, 249, 255, 0.8); border-radius: 10px; padding: 12px 20px; color: #0369A1; }}
        .stTabs [aria-selected="true"] {{ background-color: #0369A1 !important; color: white !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES LÓGICAS ---
def dir_viento_real(grados):
    dirs = ["N ↓", "NE ↙", "E ←", "SE ↖", "S ↑", "SO ↗", "O →", "NO ↘"]
    return dirs[round(grados / 45) % 8]

def evaluar_pesca(ola, viento):
    puntos = 10
    if ola > 2.0: puntos -= 5
    if viento > 25: puntos -= 3
    if 0.8 < ola < 1.5: puntos += 2
    nota = max(0, min(10, puntos))
    if nota > 7: return f"🔥 EXCELENTE ({nota}/10)", "Día perfecto. Condiciones estables para salir."
    elif nota > 4: return f"⚖️ REGULAR ({nota}/10)", "Pesca posible, pero busca zonas resguardadas."
    return f"⚠️ MALA ({nota}/10)", "Mar complicada. Mejor revisar equipo en puerto."

def recomendacion_especie_real(ola, viento):
    # Tip de pesca integrado para cada especie recomendado en Txomin
    if 0.8 <= ola <= 1.8: return "🐟 SARGO", "Tip: Busca zonas con buena espuma y usa macizo de anchoa o gamba pelada.", IMG_SARGO
    if ola < 0.7 and viento < 12: return "🦑 CHIPIRÓN", "Tip: Trabaja poteras de tamaño 2.0 o 2.5 con tirones muy suaves al atardecer.", IMG_CHIPIRON
    if viento >= 10 and ola < 1.3: return "🐠 CHICHARRO", "Tip: El viento riza la superficie; es el momento ideal para meter plumillas blancas a 3 nudos.", IMG_CHICHARRO
    return "🦂 CABRARROCA", "Tip: Fondea en piedra dura pura y usa chambel con plomo pesado y tiras de chipirón.", IMG_CABRARROCA

@st.cache_data(ttl=600)
def fetch_data():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={lon_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# Parche temporal de coordenadas en fetch_data por error tipográfico (lon_MUTRIKU a LON_MUTRIKU)
@st.cache_data(ttl=600)
def fetch_data_fix():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.31.0 - Mutriku Pro")

tab0, tab1, tab2 = st.tabs(["⚓ ESTADO DEL MAR", "🗺️ MAPA IHM", "🐟 INFO LEGAL"])

dm_m, dw_m = fetch_data_fix()

# --- PESTAÑA PRINCIPAL: PORTADA Y CARRUSEL ---
with tab0:
    if dm_m and 'hourly' in dm_m and dw_m and 'list' in dw_m:
        # Datos del momento exacto actual
        ola_act = dm_m['hourly']['wave_height'][0]
        ola_dir = dm_m['hourly']['wave_direction'][0]
        temp_agua = dm_m['hourly']['sea_surface_temperature'][0]
        v_corr = dm_m['hourly']['ocean_current_velocity'][0] * 3.6
        
        # OpenWeather forecast list item 0 for current wind
        v_viento = dw_m['list'][0]['wind']['speed'] * 3.6
        d_viento = dir_viento_real(dw_m['list'][0]['wind']['deg'])
        
        # 1. PORTADA GIGANTE
        st.markdown(f"""
            <div class='main-card'>
                <h1 style='margin:0; font-size: 2.5rem;'>MUTRIKU AHORA</h1>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ VIENTO</h3><h2>{v_viento:.1f}</h2><p>km/h {d_viento}</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 OLA</h3><h2>{ola_act:.1f}</h2><p>m (Dir: {ola_dir}°)</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ AGUA</h3><h2>{temp_agua:.1f}</h2><p>°C Superficie</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 CORRIENTE</h3><h2>{v_corr:.1f}</h2><p>km/h</p></div>", unsafe_allow_html=True)

        st.divider()
        
        col_eval, col_esp = st.columns(2)
        eval_txt, eval_desc = evaluar_pesca(ola_act, v_viento)
        esp_nombre, esp_tip, esp_img = recomendacion_especie_real(ola_act, v_viento)
        
        with col_eval:
            st.markdown(f"""<div class='eval-container'>
                <h3 style='margin:0 0 10px 0; color:#0369A1;'>📈 ACTIVIDAD</h3>
                <h2 style='margin:0;'>{eval_txt}</h2><p>{eval_desc}</p>
            </div>""", unsafe_allow_html=True)
        with col_esp:
            st.markdown(f"""<div class='eval-container'>
                <img src='{esp_img}' class='rec-image'/>
                <h2 style='margin:0; color:#059669;'>{esp_nombre}</h2>
                <p><b>CONSEJO:</b> {esp_tip}</p>
            </div>""", unsafe_allow_html=True)

        # 2. CARRUSEL DESLIZABLE (SWIPE) CADA 2 HORAS
        st.markdown("<h3 style='color:white; margin-top:30px; text-shadow: 1px 1px 2px black;'>EVOLUCIÓN DEL DÍA (Desliza 👉)</h3>", unsafe_allow_html=True)
        
        html_carrusel = "<div class='scroll-wrapper'>"
        
        # Cogemos las próximas 24 horas saltando de 2 en 2 (12 tarjetas)
        for i in range(0, min(12, len(dw_m['list']))):
            item = dw_m['list'][i]
            # Sincronizamos índice de OpenWeather (cada 3h) con Open-Meteo (cada 1h) aproximando
            hora_dt = datetime.fromtimestamp(item['dt'])
            idx_marine = i * 3 
            
            if idx_marine < len(dm_m['hourly']['wave_height']):
                c_ola = dm_m['hourly']['wave_height'][idx_marine]
                c_viento = item['wind']['speed'] * 3.6
                c_dir_v = dir_viento_real(item['wind']['deg'])
                c_esp, _, _ = recomendacion_especie_real(c_ola, c_viento)
                
                html_carrusel += f"""
                <div class='hour-card'>
                    <h4>{hora_dt.strftime('%H:%M')}</h4>
                    <p>🌬️ {c_viento:.1f} km/h {c_dir_v}</p>
                    <p>🌊 {c_ola:.1f} m</p>
                    <div class='rec-badge'>{c_esp.split(" ")[1]}</div>
                </div>
                """
        
        html_carrusel += "</div>"
        st.markdown(html_carrusel, unsafe_allow_html=True)

# --- PESTAÑA 2: MAPA ---
with tab1:
    st.subheader("🗺️ Plotter IHM Mutriku")
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    st_folium(m, width="100%", height=500, key="mapa_v31")

# --- PESTAÑA 3: LEGALIDAD ---
with tab2:
    st.header("⚖️ Marco Legal de Pesca")
    st.info("De acuerdo con la legislación vigente en Euskadi, se recuerda a los usuarios respetar escrupulosamente las tallas mínimas, los cupos máximos por licencia y especie, y los períodos de veda establecidos por el Gobierno Vasco. La práctica de la pesca recreativa debe ser siempre sostenible y respetuosa con el medio marino.")
