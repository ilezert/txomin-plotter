import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- 1. CONFIGURACIÓN E INTERFAZ (BLANCO, ROJO Y NAVY) ---
st.set_page_config(page_title="Txomin v.41.3", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

st.markdown("""
    <style>
        /* Fondo Blanco e Interfaz General */
        .stApp { background-color: #FFFFFF; color: #1E3A8A; }
        
        /* Banner Principal Rojo/Granate */
        .main-banner { 
            background-color: #991B1B; 
            color: #FFFFFF; 
            text-align: center; 
            padding: 20px; 
            border-radius: 10px; 
            font-weight: 900; 
            text-transform: uppercase; 
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* Cuadros de Información (Borde Rojo, Texto Navy) */
        .main-card { 
            background: #FFFFFF; 
            padding: 25px; 
            border-radius: 15px; 
            border: 2px solid #991B1B; 
            margin-bottom: 25px; 
            position: relative;
            color: #1E3A8A;
        }
        
        /* Semáforo de Seguridad */
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; border-radius: 15px 15px 0 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }

        /* Métricas (Tipografía Azul Navy para etiquetas) */
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-top: 15px; }
        .metric-box { background: #F8FAFC; padding: 18px; border-radius: 12px; text-align: center; border: 1px solid #E2E8F0; }
        .m-label { color: #1E3A8A; font-size: 0.8rem; text-transform: uppercase; font-weight: 800; display: block; margin-bottom: 5px; }
        .m-val { color: #991B1B; font-size: 2.3rem; font-weight: 900; display: block; line-height: 1.1; }
        
        /* Alertas (Banner Rojo con detalle Navy) */
        .alert-banner { 
            background: #991B1B; 
            color: white; 
            padding: 15px; 
            border-radius: 10px; 
            border-left: 10px solid #1E3A8A; 
            margin-top: 20px; 
            font-weight: bold; 
        }
        
        /* Carrusel Horizontal (Borde Rojo) */
        .scroll-container { display: flex; overflow-x: auto; gap: 12px; padding: 15px 0; }
        .hour-card { 
            flex: 0 0 auto; 
            width: 160px; 
            background: #FFFFFF; 
            border: 1px solid #E2E8F0; 
            border-top: 5px solid #991B1B; 
            border-radius: 10px; 
            padding: 12px; 
            text-align: center;
            color: #1E3A8A;
        }
        .h-time { color: #991B1B; font-weight: 900; font-size: 1.1rem; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS RESILIENTE ---
@st.cache_data(ttl=600)
def fetch_tactical_data():
    try:
        # Open-Meteo como base sólida
        u_w = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,pressure_msl&timezone=auto&forecast_days=3"
        u_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,ocean_current_velocity,sea_surface_temperature&timezone=auto&forecast_days=3"
        
        rw = requests.get(u_w, timeout=5).json()
        rm = requests.get(u_m, timeout=5).json()
        
        df = pd.DataFrame({
            'time': pd.to_datetime(rw['hourly']['time']).dt.tz_localize('UTC').dt.tz_convert(ZONA_HORARIA),
            'v_media': rw['hourly']['wind_speed_10m'],
            'v_racha': rw['hourly']['wind_gusts_10m'],
            'ola': rm['hourly']['wave_height'],
            'corr': rm['hourly']['ocean_current_velocity'],
            'temp': rm['hourly']['sea_surface_temperature'],
            'pres': rw['hourly']['pressure_msl']
        })
        return df
    except: return pd.DataFrame()

# --- 3. RENDERIZADO DE PORTADA ---
st.markdown("<div class='main-banner'>🔱 TXOMIN - ITSAS APLIKAZIOA </div>", unsafe_allow_html=True)

df_forecast = fetch_tactical_data()

if not df_forecast.empty:
    now = df_forecast.iloc[0]
    
    # Lógica de Semáforo
    semaforo_cls = "bg-green"
    if now['v_racha'] > 28 or now['ola'] > 1.6: semaforo_cls = "bg-yellow"
    if now['v_racha'] > 35 or now['ola'] > 2.2: semaforo_cls = "bg-red"

    # --- CUADRO ACTUAL ---
    st.markdown(f"""
        <div class='main-card'>
            <div class='status-bar {semaforo_cls}'></div>
            <h2 style='color:#1E3A8A; margin-top:5px;'>ESTADO ACTUAL ({ahora_local.strftime('%H:%M')})</h2>
            <div class='metric-grid'>
                <div class='metric-box'><span class='m-label'>🌬️ VIENTO (M/R)</span><span class='m-val'>{now['v_media']:.0f}/{now['v_racha']:.0f}</span><span style='color:#1E3A8A; font-weight:bold;'>km/h</span></div>
                <div class='metric-box'><span class='m-label'>🌊 OLA</span><span class='m-val'>{now['ola']:.1f}m</span><span style='color:#1E3A8A; font-weight:bold;'>Altura</span></div>
                <div class='metric-box'><span class='m-label'>💧 CORRIENTE</span><span class='m-val'>{now['corr']*3.6:.1f}</span><span style='color:#1E3A8A; font-weight:bold;'>km/h</span></div>
                <div class='metric-box'><span class='m-label'>🌡️ AGUA</span><span class='m-val'>{now['temp']:.1f}°</span><span style='color:#1E3A8A; font-weight:bold;'>{now['pres']:.0f} hPa</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- CUADRO 2: PREVISIÓN HORARIA ---
    st.write("### ⏱️ PREVISIÓN TÁCTICA (CADA 2 HORAS)")
    h_html = "<div class='scroll-container'>"
    for i in range(0, 14, 2):
        r = df_forecast.iloc[i]
        h_html += f"""
        <div class='hour-card'>
            <div class='h-time'>{r['time'].strftime('%H:%M')}</div>
            <div style='font-size:0.9rem;'>🌬️ <b>{r['v_media']:.0f}/{r['v_racha']:.0f}</b></div>
            <div style='font-size:0.9rem; color:#991B1B;'>🌊 <b>{r['ola']:.1f}m</b></div>
            <div style='font-size:0.9rem;'>💧 <b>{r['corr']*3.6:.1f}</b></div>
        </div>
        """
    st.markdown(h_html + "</div>", unsafe_allow_html=True)

    # --- CUADRO 3: SEGURIDAD Y PECES ---
    c1, c2 = st.columns(2)
    with c1:
        rec = "EGOKIA / IDEAL" if semaforo_cls == "bg-green" else "KONTUZ / PRECAUCIÓN"
        if semaforo_cls == "bg-red": rec = "ARRISKUTSUA / PELIGRO"
        st.markdown(f"<div class='main-card' style='border-color:#1E3A8A;'><h3>🚨 SEGURIDAD</h3><h2 style='color:#991B1B;'>{rec}</h2></div>", unsafe_allow_html=True)
    with c2:
        stars = "⭐" * (4 if now['ola'] < 1.3 else 1)
        st.markdown(f"<div class='main-card' style='border-color:#1E3A8A;'><h3>🐟 ACTIVIDAD</h3><h2 style='color:#1E3A8A;'>{stars}</h2></div>", unsafe_allow_html=True)

    # --- ALERTA AEMET (Simulada por umbrales) ---
    if now['v_racha'] > 30 or now['ola'] > 2.0:
        st.markdown("<div class='alert-banner'>⚠️ AEMET: AVISO POR FENÓMENOS COSTEROS EN GIPUZKOA</div>", unsafe_allow_html=True)

else:
    st.error("📡 Error de sincronización satelital. Reintentando...")
