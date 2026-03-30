import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN BÁSICA ---
st.set_page_config(page_title="Txomin v.33.12", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# Estilos Tácticos (Diseño limpio como pediste)
st.markdown("""
    <style>
        .stApp { background-color: #011627; color: white; }
        .main-title { color: #FBBF24; text-align: center; font-weight: 900; text-transform: uppercase; margin-bottom: 20px; }
        .main-card { background: rgba(30, 41, 59, 0.8); padding: 20px; border-radius: 20px; border: 1px solid #FBBF24; text-align: center; margin-bottom: 20px; }
        .metric-card { background: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255,255,255,0.1); }
        .m-val { color: #FBBF24; font-size: 2.2rem; font-weight: 800; display: block; }
        .m-label { color: #BAE6FD; font-size: 0.8rem; text-transform: uppercase; }
        .scroll-wrapper { display: flex; overflow-x: auto; gap: 10px; padding: 10px 0; }
        .hour-card { flex: 0 0 auto; width: 140px; background: white; color: #1E293B; border-radius: 10px; padding: 10px; text-align: center; }
        .rig-info { background: #F1F5F9; border-radius: 8px; padding: 8px; margin-top: 5px; color: #334155; font-size: 0.8rem; border-left: 4px solid #FBBF24; text-align: left; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES ---
def flecha(deg):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(deg / 45) % 8]

def get_marea(f):
    d = f.day
    return f"{(d % 12) + 2:02d}:00", f"{((d % 12) + 8) % 24:02d}:30", 50 + (d * 3 % 45)

# --- 3. CARGA DE DATOS (SISTEMA SEGURO) ---
@st.cache_data(ttl=600)
def fetch_meteo():
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        url_w = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl&timezone=auto"
        dm = requests.get(url_m, timeout=10).json()
        dw = requests.get(url_w, timeout=10).json()
        df = pd.DataFrame({
            'time': pd.to_datetime(dm['hourly']['time']).dt.tz_localize('UTC').dt.tz_convert(ZONA_HORARIA),
            'wave_h': dm['hourly']['wave_height'], 'wave_d': dm['hourly']['wave_direction'],
            'wind_s': dw['hourly']['wind_speed_10m'], 'wind_g': dw['hourly']['wind_gusts_10m'],
            'wind_d': dw['hourly']['wind_direction_10m'], 'curr_v': dm['hourly']['ocean_current_velocity'],
            'curr_d': dm['hourly']['ocean_current_direction'], 'sst': dm['hourly']['sea_surface_temperature'],
            'pres': dw['hourly']['pressure_msl']
        })
        return df
    except: return None

# --- 4. INTERFAZ ---
st.markdown("<h1 class='main-title'>🔱 Txomin Tactical</h1>", unsafe_allow_html=True)

df = fetch_meteo()

tab1, tab2, tab3 = st.tabs(["⚓ ORAIN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

with tab1:
    if df is not None:
        idx = (df['time'] >= ahora_local).idxmax()
        now = df.loc[idx]
        p, b, c = get_marea(ahora_local)
        
        st.markdown(f"""
            <div class='main-card'>
                <h2 style='margin:0;'>MUTRIKU {ahora_local.strftime('%H:%M')}</h2>
                <p style='color:#10B981; font-weight:bold;'>Marea: Plea {p} / Baja {b} (Coef: {c})</p>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><span class='m-label'>🌬️ Haizea (M/R)</span><span class='m-val'>{now['wind_s']*3.6:.0f}/{now['wind_g']*3.6:.0f}</span><p>{flecha(now['wind_d'])}</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><span class='m-label'>🌊 Olatua</span><span class='m-val'>{now['wave_h']:.1f}</span><p>{flecha(now['wave_d'])}</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><span class='m-label'>🌡️ Ura</span><span class='m-val'>{now['sst']:.1f}°</span><p>{now['pres']:.0f} hPa</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><span class='m-label'>💧 Korr.</span><span class='m-val'>{now['curr_v']*3.6:.1f}</span><p>{flecha(now['curr_d'])}</p></div>", unsafe_allow_html=True)
        
        st.write("### ⏱️ Hurrengo orduak")
        html_h = "<div class='scroll-wrapper'>"
        for i in range(idx, min(idx+12, len(df)), 2):
            r = df.iloc[i]
            html_h += f"<div class='hour-card'><b>{r['time'].strftime('%H:%M')}</b><br>🌬️ {r['wind_s']*3.6:.0f}/{r['wind_g']*3.6:.0f}<br>🌊 {r['wave_h']:.1f}m</div>"
        st.markdown(html_h + "</div>", unsafe_allow_html=True)
    else:
        st.warning("⏳ Satelite datuak kargatzen... APIa zain dago.")

with tab2:
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    st_folium(m, width="100%", height=500, key="mapa_final")

with tab3:
    st.header("🐟 Espezieak")
    e_list = [("SARGOA", "Aparretan.", "Línea 0.35 / Bajo 0.30mm."), ("LUPINA", "Spinning.", "Trenzado 0.18 / Bajo 0.40mm.")]
    for name, tip, rig in e_list:
        with st.expander(f"📌 {name}"):
            st.write(tip)
            st.markdown(f"<div class='rig-info'>🛠️ {rig}</div>", unsafe_allow_html=True)
