import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- 1. CONFIGURACIÓN E INTERFAZ (ESTILO CARMESÍ) ---
st.set_page_config(page_title="Txomin v.41.0", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

st.markdown("""
    <style>
        /* Fondo y Colores Base */
        .stApp { background-color: #FDF2F2; color: #1E293B; }
        
        /* Título Estilo Windfinder */
        .main-title { background-color: #991B1B; color: white; text-align: center; padding: 15px; border-radius: 10px; font-weight: 900; text-transform: uppercase; margin-bottom: 20px; }

        /* Cuadro Estado Actual */
        .main-card { background: #FFFFFF; padding: 20px; border-radius: 15px; border: 2px solid #991B1B; margin-bottom: 25px; position: relative; box-shadow: 0 4px 10px rgba(153, 27, 27, 0.1); }
        
        /* Semáforo de Seguridad */
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; border-radius: 15px 15px 0 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }

        /* Métricas */
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 15px; }
        .metric-box { background: #FEE2E2; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #FECACA; }
        .m-label { color: #1E3A8A; font-size: 0.75rem; text-transform: uppercase; font-weight: 800; display: block; } /* Toque azul */
        .m-val { color: #7F1D1D; font-size: 2rem; font-weight: 900; display: block; }
        
        /* Alertas AEMET */
        .alert-box { background: #991B1B; color: white; padding: 15px; border-radius: 10px; font-weight: bold; margin-top: 20px; border-left: 10px solid #1E3A8A; }
        
        /* Carrusel Horario */
        .scroll-wrapper { display: flex; overflow-x: auto; gap: 10px; padding: 10px 0; }
        .hour-card { flex: 0 0 auto; width: 150px; background: #FFFFFF; border: 1px solid #991B1B; border-top: 5px solid #1E3A8A; border-radius: 10px; padding: 10px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ALGORITMO DE CONSENSO TXOMIN ---
def fetch_weather_consensus():
    v_media, v_racha = [], []
    
    # Fuente 1: Open-Meteo
    try:
        r1 = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m&timezone=auto", timeout=3).json()
        v_media.append(r1['hourly']['wind_speed_10m'][0])
        v_racha.append(r1['hourly']['wind_gusts_10m'][0])
    except: pass

    # Fuente 2: OpenWeather
    try:
        api_ow = st.secrets["OPENWEATHER_API_KEY"]
        r2 = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={api_ow}&units=metric", timeout=3).json()
        v_media.append(r2['wind']['speed'] * 3.6)
        v_racha.append(r2['wind'].get('gust', r2['wind']['speed'] * 1.3) * 3.6)
    except: pass

    # Fuente 3: WeatherAPI
    try:
        api_wa = st.secrets["WEATHERAPI_KEY"]
        r3 = requests.get(f"http://api.weatherapi.com/v1/current.json?key={api_wa}&q={LAT_MUTRIKU},{LON_MUTRIKU}", timeout=3).json()
        v_media.append(r3['current']['wind_kph'])
        v_racha.append(r3['current']['gust_kph'])
    except: pass

    if v_media:
        return sum(v_media)/len(v_media), sum(v_racha)/len(v_racha), len(v_media)
    return 0, 0, 0

@st.cache_data(ttl=600)
def fetch_marine_data():
    try:
        u = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        return requests.get(u, timeout=5).json()
    except: return None

def fetch_alerts():
    # Simulamos o consultamos alertas de Open-Meteo (que integra avisos nacionales)
    try:
        u = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=temperature_2m&timezone=auto"
        # En una versión avanzada, aquí conectaríamos con el RSS de AEMET
        return "⚠️ AVISO AMARILLO: Mar de fondo en la costa de Gipuzkoa (Simulado)"
    except: return None

# --- 3. DISEÑO DE LA PORTADA ---
st.markdown("<h1 class='main-title'>🔱 TXOMIN - CONTROL TÁCTICO</h1>", unsafe_allow_html=True)

v_avg, v_gst, sources = fetch_weather_consensus()
mar = fetch_marine_data()
alerta_txt = fetch_alerts()

if mar:
    ola_act = mar['hourly']['wave_height'][0]
    corr_v = mar['hourly']['ocean_current_velocity'][0] * 3.6
    corr_d = mar['hourly']['ocean_current_direction'][0]
    temp_u = mar['hourly']['sea_surface_temperature'][0]

    # --- CUADRO 1: ESTADO ACTUAL ---
    semaforo = "bg-green" if v_gst < 25 and ola_act < 1.5 else "bg-yellow"
    if v_gst > 35 or ola_act > 2.0: semaforo = "bg-red"

    st.markdown(f"""
        <div class='main-card'>
            <div class='status-bar {semaforo}'></div>
            <h2 style='color:#7F1D1D;'>ESTADO ACTUAL: {ahora_local.strftime('%H:%M')}</h2>
            <div class='metric-grid'>
                <div class='metric-box'><span class='m-label'>🌬️ VIENTO (M/R)</span><span class='m-val'>{v_avg:.0f}/{v_gst:.0f}</span><span style='color:#7F1D1D;'>km/h</span></div>
                <div class='metric-box'><span class='m-label'>🌊 OLA</span><span class='m-val'>{ola_act:.1f}m</span><span>Altura media</span></div>
                <div class='metric-box'><span class='m-label'>💧 CORRIENTE</span><span class='m-val'>{corr_v:.1f}</span><span style='color:#1E3A8A;'>km/h ({corr_d}°)</span></div>
                <div class='metric-box'><span class='m-label'>🌡️ AGUA</span><span class='m-val'>{temp_u:.1f}°</span><span>Superficie</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- CUADRO 2: PREVISIÓN 2H ---
    st.write("### ⏱️ PREVISIÓN CADA 2 HORAS")
    h_html = "<div class='scroll-wrapper'>"
    for i in range(0, 14, 2):
        h_html += f"""
        <div class='hour-card'>
            <h4 style='color:#991B1B;'>{(ahora_local.hour+i)%24:02d}:00</h4>
            <p style='font-size:0.8rem;'>🌬️ {v_avg:.0f}/{v_gst:.0f} km/h</p>
            <p style='font-size:0.8rem; color:#1E3A8A;'>🌊 {mar['hourly']['wave_height'][i]:.1f}m</p>
            <p style='font-size:0.8rem;'>💧 {mar['hourly']['ocean_current_velocity'][i]*3.6:.1f} km/h</p>
        </div>
        """
    st.markdown(h_html + "</div>", unsafe_allow_html=True)

    # --- CUADRO 3: SEGURIDAD Y PECES ---
    st.write("---")
    col_s, col_p = st.columns(2)
    with col_s:
        rec = "EGOKIA / IDEAL" if semaforo == "bg-green" else "KONTUZ / PRECAUCIÓN"
        if semaforo == "bg-red": rec = "ARRISKUTSUA / PELIGRO"
        st.markdown(f"<div class='main-card'><h3>🚨 SEGURIDAD</h3><h2 style='color:#7F1D1D;'>{rec}</h2></div>", unsafe_allow_html=True)
    with col_p:
        stars = "⭐" * (3 if ola_act < 1.4 else 1)
        st.markdown(f"<div class='main-card'><h3>🐟 ACTIVIDAD</h3><h2 style='color:#1E3A8A;'>{stars}</h2></div>", unsafe_allow_html=True)

    # --- CUADRO 4: ALERTAS ---
    if alerta_txt:
        st.markdown(f"<div class='alert-box'>{alerta_txt}</div>", unsafe_allow_html=True)

else:
    st.error("Error al cargar datos del satélite.")

# --- NOTIFICACIONES MÓVILES (CONCEPTUAL) ---
# En Streamlit web, las notificaciones 'push' nativas requieren un PWA o servicio externo.
# Dejamos la lógica lista para integrar OneSignal o Telegram Bot.
