import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.40.3", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# --- ESTILO VISUAL: ROJO Y BLANCO TÁCTICO ---
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #1E293B; }
        .main-title { color: #DC2626; text-align: center; font-weight: 900; text-transform: uppercase; font-size: 2.2rem; border-bottom: 3px solid #DC2626; padding-bottom: 10px; }
        .main-card { background: #FFFFFF; padding: 20px; border-radius: 15px; border: 2px solid #DC2626; text-align: center; margin-bottom: 20px; position: relative; }
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; border-radius: 15px 15px 0 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }
        
        /* Grid de métricas */
        .metric-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 15px; }
        .metric-box { background: #F8FAFC; padding: 12px; border-radius: 10px; border: 1px solid #E2E8F0; text-align: center; }
        .m-label { color: #64748B; font-size: 0.7rem; text-transform: uppercase; font-weight: bold; }
        .m-val { color: #DC2626; font-size: 2rem; font-weight: 900; display: block; }
        
        /* Carrusel Horario Detallado */
        .scroll-wrapper { display: flex; overflow-x: auto; gap: 12px; padding: 10px 0 20px 0; width: 100%; }
        .hour-card { flex: 0 0 auto; width: 190px; background: #FFFFFF; border-radius: 12px; padding: 15px; border: 1px solid #DC2626; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .hour-card h4 { margin: 0 0 10px 0; color: #FFFFFF; background: #DC2626; border-radius: 5px; padding: 5px; font-size: 1.1rem; }
        .data-row { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.85rem; font-weight: 700; border-bottom: 1px solid #F1F5F9; padding-bottom: 2px; }
        .data-label { color: #64748B; }
        .data-val { color: #DC2626; font-weight: 800; }
        
        /* Countdown Marea */
        .tide-timer { background: #FEF2F2; border: 2px dashed #DC2626; border-radius: 10px; padding: 10px; margin: 15px 0; font-weight: 900; color: #DC2626; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE DATOS ---
def flecha(deg):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(deg / 45) % 8]

def get_marea_info(f):
    dia = f.day
    # Simulamos datetimes de mareas para el countdown
    p_hora = (dia % 12) + 2
    b_hora = ((dia % 12) + 8) % 24
    plea_dt = f.replace(hour=p_hora, minute=0, second=0)
    baja_dt = f.replace(hour=b_hora, minute=30, second=0)
    
    # Próxima marea
    if f < plea_dt:
        return "PLEAMAR", plea_dt, 50 + (dia * 3 % 45)
    elif f < baja_dt:
        return "BAJAMAR", baja_dt, 50 + (dia * 3 % 45)
    else:
        return "PLEAMAR", plea_dt + timedelta(hours=12), 50 + (dia * 3 % 45)

def calcular_estrellas(ola, viento, coef):
    p = 1
    if 0.6 <= ola <= 1.4: p += 1
    if viento < 15: p += 1
    if 65 <= coef <= 90: p += 1
    score = max(1, min(5, p))
    return "⭐" * score

@st.cache_data(ttl=600)
def fetch_full_data():
    try:
        # Marine: Ola, Periodo, Corrientes
        u_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,wave_period,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        # Weather: Viento y Rachas
        u_w = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl&timezone=auto"
        dm, dw = requests.get(u_m).json(), requests.get(u_w).json()
        df = pd.DataFrame({
            'time': pd.to_datetime(dm['hourly']['time']).dt.tz_localize('UTC').dt.tz_convert(ZONA_HORARIA),
            'wave_h': dm['hourly']['wave_height'], 'wave_d': dm['hourly']['wave_direction'],
            'wave_p': dm['hourly']['wave_period'], 'sst': dm['hourly']['sea_surface_temperature'],
            'curr_v': dm['hourly']['ocean_current_velocity'], 'curr_d': dm['hourly']['ocean_current_direction'],
            'wind_s': dw['hourly']['wind_speed_10m'], 'wind_g': dw['hourly']['wind_gusts_10m'],
            'wind_d': dw['hourly']['wind_direction_10m'], 'pres': dw['hourly']['pressure_msl']
        })
        return df
    except: return None

# --- 3. INTERFAZ ---
st.markdown("<h1 class='main-title'>🔱 TXOMIN - CONTROL TÁCTICO</h1>", unsafe_allow_html=True)
tab0, tab1, tab2, tab3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

df = fetch_full_data()

with tab0:
    if df is not None:
        idx = (df['time'] >= ahora_local).idxmax()
        now = df.loc[idx]
        tipo, marea_dt, coef = get_marea_info(ahora_local)
        faltan = marea_dt - ahora_local
        horas, resto = divmod(faltan.seconds, 3600)
        minutos = resto // 60
        
        # Semáforo
        color = "bg-green" if now['wave_h'] < 1.4 and now['wind_g'] < 25 else "bg-yellow"
        if now['wind_g'] > 35 or now['wave_h'] > 2.0: color = "bg-red"

        st.markdown(f"""
            <div class='main-card'>
                <div class='status-bar {color}'></div>
                <h2 style='margin:0; color:#1E293B;'>MUTRIKU: {ahora_local.strftime('%H:%M')}</h2>
                <div class='tide-timer'>⏳ PRÓXIMA {tipo}: {horas}h {minutos}min (Coef: {coef})</div>
            </div>
        """, unsafe_allow_html=True)

        # Rejilla ORAIN
        m_html = f"""
        <div class='metric-container'>
            <div class='metric-box'><span class='m-label'>🌬️ VIENTO</span><span class='m-val'>{now['wind_s']*3.6:.0f}/{now['wind_g']*3.6:.0f}</span><span style='font-size:0.8rem;'>km/h {flecha(now['wind_d'])}</span></div>
            <div class='metric-box'><span class='m-label'>🌊 OLA</span><span class='m-val'>{now['wave_h']:.1f}m</span><span style='font-size:0.8rem;'>T: {now['wave_p']:.0f}s</span></div>
            <div class='metric-box'><span class='m-label'>🌡️ URA</span><span class='m-val'>{now['sst']:.1f}°</span><span style='font-size:0.8rem;'>{now['pres']:.0f} hPa</span></div>
            <div class='metric-box'><span class='m-label'>💧 KORR.</span><span class='m-val'>{now['curr_v']*3.6:.1f}</span><span style='font-size:0.8rem;'>km/h {flecha(now['curr_d'])}</span></div>
        </div>
        """
        st.markdown(m_html, unsafe_allow_html=True)

        st.write("---")
        st.write("### ⏱️ PREVISIÓN PRÓXIMAS 12 HORAS")
        
        h_html = "<div class='scroll-wrapper'>"
        for i in range(idx, idx + 13, 2):
            r = df.iloc[i]
            est = calcular_estrellas(r['wave_h'], r['wind_s']*3.6, coef)
            h_html += f"""
            <div class='hour-card'>
                <h4>{r['time'].strftime('%H:%M')}</h4>
                <div class='data-row'><span class='data-label'>🌬️ Viento</span><span class='data-val'>{r['wind_s']*3.6:.0f}/{r['wind_g']*3.6:.0f}</span></div>
                <div class='data-row'><span class='data-label'>🌊 Ola/T</span><span class='data-val'>{r['wave_h']:.1f}m / {r['wave_p']:.0f}s</span></div>
                <div class='data-row'><span class='data-label'>💧 Korr.</span><span class='data-val'>{r['curr_v']*3.6:.1f} {flecha(r['
