import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.33.9", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# CSS Profesional Blindado
st.markdown("""
    <style>
        .stApp { background-color: #011627; color: white; }
        .main-card { background: rgba(3, 105, 161, 0.7); backdrop-filter: blur(10px); padding: 25px; border-radius: 20px; text-align: center; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.2); position: relative; overflow: hidden; }
        .metric-card { background: rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.2); }
        .metric-card h2 { color: #FBBF24 !important; font-size: 2.2rem; margin: 0; font-weight: 800; }
        .metric-card h3 { text-transform: uppercase; font-size: 0.9rem; color: #BAE6FD; }
        .status-bar { height: 15px; width: 100%; position: absolute; top: 0; left: 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }
        .activity-badge { background: #1E293B; color: #FBBF24; padding: 6px 15px; border-radius: 20px; font-weight: bold; border: 1px solid #FBBF24; margin: 10px 0; display: inline-block; }
        .scroll-wrapper { display: flex !important; flex-direction: row !important; overflow-x: auto !important; gap: 12px; padding: 10px 0 20px 0; width: 100%; }
        .hour-card { flex: 0 0 auto; width: 160px; background: rgba(255,255,255,0.95); border-radius: 12px; padding: 10px; text-align: center; color: #1E293B !important; border-top: 5px solid #0369A1; }
        .hour-card h4 { margin: 0 0 5px 0; color: #0369A1 !important; font-weight: 800; border-bottom: 1px solid #DDD; }
        .hour-card p { margin: 4px 0; font-size: 0.8rem; font-weight: 700; display: flex; justify-content: space-between; }
        .val-blue { color: #0369A1; }
        .day-forecast-card { background: rgba(255, 255, 255, 0.98); border-radius: 15px; padding: 0; margin-bottom: 25px; color: #1E293B; overflow: hidden; border: 1px solid #E2E8F0; }
        .rig-info { background: #F1F5F9; border-radius: 8px; padding: 10px; margin-top: 5px; color: #334155; font-size: 0.85rem; border-left: 4px solid #FBBF24; text-align: left; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE MOTOR ---
def flecha_desde(grados):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(grados / 45) % 8]

def generar_marea(fecha):
    dia = fecha.day
    return f"{(dia % 12) + 2:02d}:00", f"{((dia % 12) + 8) % 24:02d}:30", 50 + (dia * 3 % 45)

def get_semaforo(ola, v_avg, v_gust):
    if ola > 2.0 or v_gust > 35: return "bg-red", "🛑 ARRISKUTSUA / PELIGRO"
    if v_avg > 12 or ola > 1.5 or v_gust > 25: return "bg-yellow", "🟡 KONTUZ / PRECAUCIÓN"
    return "bg-green", "🟢 EGOKIA / IDEAL"

@st.cache_data(ttl=600)
def fetch_data():
    try:
        u_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto&forecast_days=7"
        u_w = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl&timezone=auto&forecast_days=7"
        dm, dw = requests.get(u_m).json(), requests.get(u_w).json()
        df = pd.DataFrame({
            'time': pd.to_datetime(dm['hourly']['time']).dt.tz_localize('UTC').dt.tz_convert(ZONA_HORARIA),
            'wave_h': dm['hourly']['wave_height'], 'wave_d': dm['hourly']['wave_direction'],
            'curr_v': dm['hourly']['ocean_current_velocity'], 'curr_d': dm['hourly']['ocean_current_direction'],
            'sst': dm['hourly']['sea_surface_temperature'],
            'wind_s': dw['hourly']['wind_speed_10m'], 'wind_g': dw['hourly']['wind_gusts_10m'],
            'wind_d': dw['hourly']['wind_direction_10m'], 'pres': dw['hourly']['pressure_msl']
        })
        return df
    except: return None

# --- 3. SIDEBAR Y PESTAÑAS ---
st.sidebar.header("🛠️ AJUSTE TÁCTICO")
f_viento = st.sidebar.slider("Viento (%)", 50, 150, 100) / 100.0
f_ola = st.sidebar.slider("Ola (m)", -1.0, 1.0, 0.0, 0.1)

tab0, tab1, tab2, tab3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

# --- 4. CONTENIDO ---
df_master = fetch_data()

with tab0:
    if df_master is not None:
        idx = (df_master['time'] >= ahora_local).idxmax()
        now = df_master.loc[idx]
        o_cal, v_a, v_g = now['wave_h'] + f_ola, now['wind_s']*3.6*f_viento, now['wind_g']*3.6*f_viento
        p, b, coef = generar_marea(ahora_local)
        c_cls, s_txt = get_semaforo(o_cal, v_a, v_g)

        st.markdown(f"<div class='main-card'><div class='status-bar {c_cls}'></div><h1 style='margin:0;'>MUTRIKU {ahora_local.strftime('%H:%M')}</h1><p style='font-weight:bold; color:#FBBF24;'>{s_txt}</p></div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-card'><h3>🌬️ Viento (M/R)</h3><h2>{v_a:.0f}/{v_g:.0f}</h2><p>{flecha_desde(now['wind_d'])}</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><h3>🌊 Olatua</h3><h2>{o_cal:.1f}</h2><p>{flecha_desde(now['wave_d'])}</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><h3>🌡️ Ura</h3><h2>{now['sst']:.1f}°</h2><p>{now['pres']:.0f} hPa</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-card'><h3>💧 Korr.</h3><h2>{now['curr_v']*3.6:.1f}</h2><p>km/h</p></div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='tide-alert'>⏳ Itsasgora {p} / Itsasbehera {b} (Coef: {coef})</div>", unsafe_allow_html=True)

        st.write("### ⏱️ EVOLUCIÓN 2H")
        html_h = "<div class='scroll-wrapper'>"
        for i in range(idx, min(idx+16, len(df_master)), 2):
            r = df_master.iloc[i]
            html_h += f"<div class='hour-card'><h4>{r['time'].strftime('%H:%M')}</h4><p>🌬️ {r['wind_s']*3.6*f_viento:.0f}/{r['wind_g']*3.6*f_viento:.0f}</p><p>🌊 {r['wave_h']+f_ola:.1f}m</p></div>"
        st.markdown(html_h + "</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Cargando datos del satélite... Si no aparecen, comprueba tu conexión.")

with tab1:
    if df_master is not None:
        hoy = ahora_local.date()
        for i in range(1, 5):
            d_t = hoy + timedelta(days=i)
            p, b, coef = generar_marea(d_t)
            df_day = df_master[df_master['time'].dt.date == d_t]
            if not df_day.empty:
                r12 = df_day.iloc[len(df_day)//2]
                c_cls, s_txt = get_semaforo(r12['wave_h']+f_ola, r12['wind_s']*3.6*f_viento, r12['wind_g']*3.6*f_viento)
                st.markdown(f"<div class='day-forecast-card'><div class='status-bar {c_cls}'></div><div style='padding:15px;'><h3 style='margin:0;'>{d_t.strftime('%A, %b %d')}</h3><p><b>{s_txt}</b> | Coef: {coef}</p><div class='scroll-wrapper'>", unsafe_allow_html=True)
                html_d = ""
                for _, r in df_day.iloc[8:22:2].iterrows():
                    html_d += f"<div class='hour-card'><h4>{r['time'].strftime('%H:%M')}</h4><p>🌬️ {r['wind_s']*3.6*f_viento:.0f}/{r['wind_g']*3.6*f_viento:.0f}</p><p>🌊 {r['wave_h']+f_ola:.1f}m</p></div>"
                st.markdown(html_d + "</div></div></div>", unsafe_allow_html=True)

with tab2:
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    st_folium(m, width="100%", height=500, key="plot_v339")

with tab3:
    st.header("🐟 Espezieak eta Apailuak")
    e_list = [
        ("SARGOA", "Aparretan, 0.8m-1.5m onena.", "Línea 0.35 / Bua 20g / Bajo 0.30mm."),
        ("LUPINA", "Spinning egunsentian.", "Trenzado 0.18 / Bajo 0.40mm."),
        ("TXIPIROIA", "Poterak 2.0 ilunabarrean.", "Trenzado 0.10 / Bajo 0.22mm."),
        ("DENTOIA", "Hondo handiak, zoka.", "Trenzado 0.30 / Bajo 0.70mm.")
    ]
    for name, tip, rig in e_list:
        with st.expander(f"📌 {name}"):
            st.write(tip)
            st.markdown(f"<div class='rig-info'><b>🛠️ APAILUA:</b> {rig}</div>", unsafe_allow_html=True)
