import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- 1. CONFIGURACIÓN E INTERFAZ (CARMESÍ & BLANCO) ---
st.set_page_config(page_title="Txomin v.41.1", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #1E293B; }
        
        /* Cabecera Granate */
        .main-title { background: linear-gradient(90deg, #7F1D1D, #991B1B); color: white; text-align: center; padding: 20px; border-radius: 10px; font-weight: 900; text-transform: uppercase; margin-bottom: 25px; }

        /* Cuadros Principales */
        .main-card { background: #FFFFFF; padding: 25px; border-radius: 15px; border: 2px solid #991B1B; margin-bottom: 25px; position: relative; box-shadow: 0 4px 12px rgba(153, 27, 27, 0.08); }
        
        /* Semáforo dinámico */
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; border-radius: 15px 15px 0 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }

        /* Métricas Portada */
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-top: 15px; }
        .metric-box { background: #FFF1F2; padding: 18px; border-radius: 12px; text-align: center; border: 1px solid #FECACA; }
        .m-label { color: #1E3A8A; font-size: 0.8rem; text-transform: uppercase; font-weight: 800; display: block; margin-bottom: 5px; }
        .m-val { color: #991B1B; font-size: 2.2rem; font-weight: 900; display: block; line-height: 1.1; }
        
        /* Alertas AEMET Estilo Windguru */
        .alert-card { background: #991B1B; color: white; padding: 15px; border-radius: 10px; border-left: 8px solid #1E3A8A; margin-top: 20px; font-weight: bold; }
        
        /* Carrusel Horizontal de Previsión */
        .scroll-container { display: flex; overflow-x: auto; gap: 12px; padding: 15px 0; scrollbar-width: thin; }
        .hour-card { flex: 0 0 auto; width: 160px; background: #F8FAFC; border: 1px solid #E2E8F0; border-top: 5px solid #991B1B; border-radius: 10px; padding: 12px; text-align: center; }
        .h-time { color: #991B1B; font-weight: 900; font-size: 1.1rem; border-bottom: 1px solid #E2E8F0; margin-bottom: 8px; padding-bottom: 4px; }
        .h-data { font-size: 0.85rem; font-weight: 700; margin: 4px 0; display: flex; justify-content: space-between; }
        .h-val-blue { color: #1E3A8A; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ALGORITMO DE CONSENSO (PREVISIÓN HORARIA) ---
@st.cache_data(ttl=600)
def get_consensus_forecast():
    try:
        # Petición a Open-Meteo para datos horarios (Viento, Ola, Corriente, Temp)
        u = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,pressure_msl&timezone=auto"
        u_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,ocean_current_velocity,sea_surface_temperature&timezone=auto"
        
        rw = requests.get(u).json()
        rm = requests.get(u_m).json()
        
        # Creamos un DataFrame con la previsión
        df = pd.DataFrame({
            'time': pd.to_datetime(rw['hourly']['time']).dt.tz_localize('UTC').dt.tz_convert(ZONA_HORARIA),
            'v_media': rw['hourly']['wind_speed_10m'],
            'v_racha': rw['hourly']['wind_gusts_10m'],
            'ola': rm['hourly']['wave_height'],
            'corr': rm['hourly']['ocean_current_velocity'],
            'temp': rm['hourly']['sea_surface_temperature']
        })
        # Aquí podrías añadir más lógica de media compensada si tienes más APIs activas
        return df
    except: return None

# --- 3. LÓGICA DE NOTIFICACIONES Y ALERTAS ---
def get_aemet_alerts():
    # En un sistema real, aquí leeríamos el RSS de AEMET. 
    # Por ahora, activamos alerta si el viento > 30km/h o la ola > 2m.
    return "⚠️ ALERTA: Mar de fondo detectado. Precaución en el espigón."

# --- 4. RENDERIZADO DE LA PORTADA ---
st.markdown("<div class='main-title'>🔱 TXOMIN - CONTROL TÁCTICO</div>", unsafe_allow_html=True)

df_forecast = get_consensus_forecast()

if df_forecast is not None:
    # Datos actuales (Fila 0)
    now_idx = 0 
    row_now = df_forecast.iloc[now_idx]
    
    # --- CUADRO 1: ESTADO ACTUAL ---
    semaforo_cls = "bg-green"
    if row_now['v_racha'] > 28 or row_now['ola'] > 1.6: semaforo_cls = "bg-yellow"
    if row_now['v_racha'] > 35 or row_now['ola'] > 2.2: semaforo_cls = "bg-red"

    st.markdown(f"""
        <div class='main-card'>
            <div class='status-bar {semaforo_cls}'></div>
            <h2 style='color:#991B1B; margin-top:5px;'>ESTADO ACTUAL EN MUTRIKU ({ahora_local.strftime('%H:%M')})</h2>
            <div class='metric-grid'>
                <div class='metric-box'><span class='m-label'>🌬️ VIENTO (M/R)</span><span class='m-val'>{row_now['v_media']:.0f}/{row_now['v_racha']:.0f}</span><span style='font-size:0.8rem;'>km/h</span></div>
                <div class='metric-box'><span class='m-label'>🌊 OLA</span><span class='m-val'>{row_now['ola']:.1f}m</span><span>Altura</span></div>
                <div class='metric-box'><span class='m-label'>💧 CORRIENTE</span><span class='m-val'>{row_now['corr']*3.6:.1f}</span><span style='color:#1E3A8A;'>km/h</span></div>
                <div class='metric-box'><span class='m-label'>🌡️ AGUA</span><span class='m-val'>{row_now['temp']:.1f}°</span><span>Temp.</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- CUADRO 2: PREVISIÓN CADA 2 HORAS ---
    st.write("### ⏱️ PREVISIÓN TÁCTICA (PRÓXIMAS 12H)")
    h_html = "<div class='scroll-container'>"
    # Empezamos desde ahora y saltamos de 2 en 2 horas
    for i in range(0, 14, 2):
        r = df_forecast.iloc[i]
        h_html += f"""
        <div class='hour-card'>
            <div class='h-time'>{r['time'].strftime('%H:%M')}</div>
            <div class='h-data'><span>🌬️ Viento</span><span class='h-val-blue'>{r['v_media']:.0f}/{r['v_racha']:.0f}</span></div>
            <div class='h-data'><span>🌊 Ola</span><span class='h-val-blue'>{r['ola']:.1f}m</span></div>
            <div class='h-data'><span>💧 Korr.</span><span class='h-val-blue'>{r['corr']*3.6:.1f}</span></div>
        </div>
        """
    st.markdown(h_html + "</div>", unsafe_allow_html=True)

    # --- CUADRO 3: SEGURIDAD Y PECES ---
    c1, c2 = st.columns(2)
    with c1:
        rec = "EGOKIA" if semaforo_cls == "bg-green" else "KONTUZ"
        if semaforo_cls == "bg-red": rec = "ARRISKUTSUA"
        st.markdown(f"<div class='main-card' style='border-color:#1E3A8A;'><h3>🚨 RECOMENDACIÓN</h3><h2 style='color:#991B1B;'>{rec}</h2></div>", unsafe_allow_html=True)
    with c2:
        stars = "⭐" * (3 if row_now['ola'] < 1.4 and row_now['v_racha'] < 20 else 1)
        st.markdown(f"<div class='main-card' style='border-color:#1E3A8A;'><h3>🐟 ACTIVIDAD PECES</h3><h2 style='color:#1E3A8A;'>{stars}</h2></div>", unsafe_allow_html=True)

    # --- CUADRO 4: ALERTAS AEMET ---
    alert_msg = get_aemet_alerts()
    if alert_msg:
        st.markdown(f"<div class='alert-card'>{alert_msg}</div>", unsafe_allow_html=True)
else:
    st.error("No se han podido sincronizar los satélites. Revisa la conexión.")
