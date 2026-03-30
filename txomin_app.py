import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.40.2 - Alerta", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# --- NUEVO ESTILO VISUAL: ROJO Y BLANCO ---
st.markdown("""
    <style>
        /* Fondo Principal Blanco */
        .stApp { background-color: #FFFFFF; color: #1E293B; }
        
        /* Título Principal Rojo */
        .main-title { color: #DC2626; text-align: center; font-weight: 900; text-transform: uppercase; font-size: 2.5rem; margin-bottom: 20px; border-bottom: 3px solid #DC2626; padding-bottom: 10px; }
        
        /* Tarjetas Principales Blancas con Borde Rojo */
        .main-card { background: #FFFFFF; padding: 25px; border-radius: 15px; border: 2px solid #DC2626; text-align: center; margin-bottom: 20px; position: relative; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        
        /* EL SEMÁFORO (Se mantiene arriba) */
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; border-radius: 15px 15px 0 0; }
        .bg-green { background-color: #10B981; } /* Verde Go */
        .bg-yellow { background-color: #FBBF24; } /* Amarillo Precaución */
        .bg-red { background-color: #EF4444; } /* Rojo Peligro */
        
        /* Contenedor de Métricas */
        .metric-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-top: 25px; }
        
        /* Cajas de Métricas Blancas con borde gris suave */
        .metric-box { background: #F8FAFC; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #E2E8F0; }
        
        /* Etiquetas de Métricas en Gris Oscuro */
        .m-label { color: #64748B; font-size: 0.85rem; text-transform: uppercase; font-weight: bold; margin-bottom: 8px; display: block; }
        
        /* Valores de Métricas en ROJO TÁCTICO */
        .m-val { color: #DC2626; font-size: 2.8rem; font-weight: 900; display: block; line-height: 1; }
        
        /* Unidades en Gris */
        .m-unit { font-size: 0.9rem; color: #64748B; font-weight: bold; }

        /* Carrusel Horario */
        .scroll-wrapper { display: flex; overflow-x: auto; gap: 10px; padding: 15px 0; }
        
        /* Tarjetas Horarias Blancas con borde rojo */
        .hour-card { flex: 0 0 auto; width: 140px; background: #FFFFFF; color: #1E293B; border-radius: 10px; padding: 12px; text-align: center; border: 1px solid #DC2626; border-top: 5px solid #DC2626; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .hour-card h4 { margin: 0 0 5px 0; color: #DC2626; font-weight: 800; border-bottom: 1px solid #E2E8F0; padding-bottom: 3px; }
        .hour-card p { margin: 4px 0; font-size: 0.9rem; font-weight: 700; }
        
        /* Ajuste de Pestañas Streamlit */
        .stTabs [data-baseweb="tab"] { color: #64748B !important; font-weight: bold; font-size: 1.1rem; }
        .stTabs [aria-selected="true"] { color: #DC2626 !important; border-bottom-color: #DC2626 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS (CONSENSO RESILIENTE) ---
@st.cache_data(ttl=600)
def fetch_consensus():
    v_list, g_list, pres_list = [], [], []
    
    # Intento 1: Open-Meteo (Sin Key)
    try:
        r1 = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,pressure_msl&timezone=auto", timeout=3).json()
        v_list.append(r1['hourly']['wind_speed_10m'][0])
        g_list.append(r1['hourly']['wind_gusts_10m'][0])
        pres_list.append(r1['hourly']['pressure_msl'][0])
    except: pass

    # Intento 2: OpenWeather (Con Key)
    key_ow = st.secrets.get("OPENWEATHER_API_KEY")
    if key_ow:
        try:
            r2 = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT_MUTRIKU}&lon={LON_MUTRIKU}&appid={key_ow}&units=metric", timeout=3).json()
            v_list.append(r2['wind']['speed'] * 3.6)
            g_list.append(r2['wind'].get('gust', r2['wind']['speed'] * 1.3) * 3.6)
            pres_list.append(r2['main']['pressure'])
        except: pass

    # Intento 3: WeatherAPI (Con Key)
    key_wa = st.secrets.get("WEATHERAPI_KEY")
    if key_wa:
        try:
            r3 = requests.get(f"http://api.weatherapi.com/v1/current.json?key={key_wa}&q={LAT_MUTRIKU},{LON_MUTRIKU}", timeout=3).json()
            v_list.append(r3['current']['wind_kph'])
            g_list.append(r3['current']['gust_kph'])
            pres_list.append(r3['current']['pressure_mb'])
        except: pass

    if v_list:
        return sum(v_list)/len(v_list), sum(g_list)/len(g_list), sum(pres_list)/len(pres_list), len(v_list)
    return 0, 0, 1013, 0

@st.cache_data(ttl=600)
def fetch_marine():
    try:
        u = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,ocean_current_velocity,sea_surface_temperature&timezone=auto"
        res = requests.get(u, timeout=5).json()
        return res
    except: return None

# --- 3. ESTRUCTURA Y PESTAÑAS ---
st.markdown("<h1 class='main-title'>🔱 TXOMIN PATROIA </h1>", unsafe_allow_html=True)

tab0, tab1, tab2, tab3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

# Ejecutar carga
v_avg, v_gust, pres_atm, sources = fetch_consensus()
mar_data = fetch_marine()

with tab0:
    if mar_data and 'hourly' in mar_data:
        ola_h = mar_data['hourly']['wave_height'][0]
        temp_u = mar_data['hourly']['sea_surface_temperature'][0]
        corr_v = mar_data['hourly']['ocean_current_velocity'][0] * 3.6
        
        # LÓGICA DEL SEMÁFORO (Mantenida)
        color = "bg-green" if ola_h < 1.5 else "bg-yellow"
        if v_gust > 30 or ola_h > 2.0: color = "bg-red"

        st.markdown(f"""
            <div class='main-card'>
                <div class='status-bar {color}'></div>
                <h2 style='margin:0; color:#1E293B;'>ESTADO ACTUAL: {ahora_local.strftime('%H:%M')}</h2>
                <p style='color:#DC2626; font-weight:bold; margin:5px 0;'>Radar: {sources} fuentes de datos activas</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-box'><span class='m-label'>🌬️ VIENTO (M/R)</span><span class='m-val'>{v_avg:.0f}/{v_gust:.0f}</span><span class='m-unit'>km/h</span></div>
                <div class='metric-box'><span class='m-label'>🌊 OLATUA</span><span class='m-val'>{ola_h:.1f}</span><span class='m-unit'>metros</span></div>
                <div class='metric-box'><span class='m-label'>🌡️ URA / PRES.</span><span class='m-val'>{temp_u:.1f}°</span><span class='m-unit'>{pres_atm:.0f} hPa</span></div>
                <div class='metric-box'><span class='m-label'>💧 KORRONTEA</span><span class='m-val'>{corr_v:.1f}</span><span class='m-unit'>km/h</span></div>
            </div>
        """, unsafe_allow_html=True)

        st.write("---")
        st.write("### ⏱️ TENDENCIA PRÓXIMAS HORAS (OLA)")
        h_html = "<div class='scroll-wrapper'>"
        for i in range(0, 12, 2):
            h_h = mar_data['hourly']['wave_height'][i]
            # Tarjetas horarias en Rojo/Blanco
            h_html += f"<div class='hour-card'><h4>+ {i}h</h4><p style='color:#DC2626; font-weight:bold;'>🌊 {h_h:.1f}m</p></div>"
        st.markdown(h_html + "</div>", unsafe_allow_html=True)
    else:
        st.error("⚠️ DATOS NO DISPONIBLES: Comprueba la conexión satelital.")
        st.warning("Asegúrate de tener las APIs guardadas en 'Secrets'.")

with tab1: st.info("Pestaña en construcción: Previsión 4 días (Rojo/Blanco).")
with tab2: st.info("Pestaña en construcción: Mapa táctico.")
with tab3: st.info("Pestaña en construcción: Aparejos.")
