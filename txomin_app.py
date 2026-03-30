import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# CSS Estilo Windfinder (Oscuro, Técnico, Azul/Ámbar)
st.markdown("""
    <style>
        .stApp { background-color: #0B121E; color: #E2E8F0; }
        .main-title { color: #FBBF24; text-align: center; font-weight: 900; text-transform: uppercase; font-size: 2rem; margin-bottom: 20px; border-bottom: 2px solid #1E293B; padding-bottom: 10px; }
        
        /* Tarjetas Estilo Windfinder */
        .main-card { background: #161E2E; padding: 20px; border-radius: 12px; border: 1px solid #1E293B; margin-bottom: 20px; position: relative; }
        .status-bar { height: 8px; width: 100%; position: absolute; top: 0; left: 0; border-radius: 12px 12px 0 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }

        .metric-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 15px; }
        .metric-box { background: #1F2937; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #374151; }
        .m-label { color: #9CA3AF; font-size: 0.75rem; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 5px; }
        .m-val { color: #FBBF24; font-size: 1.8rem; font-weight: 800; display: block; line-height: 1.2; }
        .m-unit { font-size: 0.8rem; color: #9CA3AF; }

        /* Tabla de Previsión */
        .scroll-wrapper { display: flex; overflow-x: auto; gap: 8px; padding: 10px 0; }
        .hour-card { flex: 0 0 auto; width: 130px; background: #1F2937; border-radius: 8px; padding: 10px; text-align: center; border-bottom: 4px solid #3B82F6; }
        .hour-card h4 { margin: 0 0 5px 0; color: #3B82F6; font-size: 1rem; border-bottom: 1px solid #374151; }
        .hour-card p { margin: 4px 0; font-size: 0.8rem; font-weight: 600; display: flex; justify-content: space-between; }
        .val-pro { color: #FBBF24; }

        .stTabs [data-baseweb="tab"] { color: #9CA3AF !important; font-weight: bold; }
        .stTabs [aria-selected="true"] { color: #FBBF24 !important; border-bottom-color: #FBBF24 !important; }
        
        .rig-info { background: #0F172A; border-radius: 6px; padding: 10px; border-left: 4px solid #FBBF24; font-size: 0.85rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
def flecha(deg):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(deg / 45) % 8]

def get_marea(f):
    d = f.day
    return f"{(d % 12) + 2:02d}:00", f"{((d % 12) + 8) % 24:02d}:30", 50 + (d * 3 % 45)

@st.cache_data(ttl=600)
def fetch_all_data():
    try:
        # Satélite 1: Marine (Olas y Corrientes)
        u_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto&forecast_days=6"
        # Satélite 2: Viento y Presión
        u_w = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl&timezone=auto&forecast_days=6"
        dm, dw = requests.get(u_m).json(), requests.get(u_w).json()
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

# --- 3. INTERFAZ TÁCTICA ---
st.markdown("<h1 class='main-title'>🔱 Mutriku Tactical Dashboard</h1>", unsafe_allow_html=True)

df = fetch_all_data()
tab1, tab2, tab3, tab4 = st.tabs(["⚓ ORAIN", "📅 PREVISIÓN 4 EGUN", "🗺️ MAPA TÁCTICO", "🐟 APAILUAK"])

if df is not None:
    idx_now = (df['time'] >= ahora_local).idxmax()
    now = df.loc[idx_now]
    
    with tab1:
        p, b, c = get_marea(ahora_local)
        color = "bg-green" if now['wave_h'] < 1.5 else "bg-yellow"
        if now['wind_g'] > 30: color = "bg-red"

        st.markdown(f"<div class='main-card'><div class='status-bar {color}'></div><h2 style='margin:0;'>{ahora_local.strftime('%H:%M')} - MUTRIKU</h2><p style='color:#3B82F6; font-weight:bold; margin-top:5px;'>Marea: Plea {p} / Baja {b} (Coef: {c})</p></div>", unsafe_allow_html=True)
        
        # Grid de métricas
        m_html = f"""
        <div class='metric-container'>
            <div class='metric-box'><span class='m-label'>🌬️ Viento (M/R)</span><span class='m-val'>{now['wind_s']*3.6:.0f}/{now['wind_g']*3.6:.0f}</span><span class='m-unit'>km/h {flecha(now['wind_d'])}</span></div>
            <div class='metric-box'><span class='m-label'>🌊 Olatua</span><span class='m-val'>{now['wave_h']:.1f}</span><span class='m-unit'>metros {flecha(now['wave_d'])}</span></div>
            <div class='metric-box'><span class='m-label'>💧 Korrontea</span><span class='m-val'>{now['curr_v']*3.6:.1f}</span><span class='m-unit'>km/h {flecha(now['curr_d'])}</span></div>
            <div class='metric-box'><span class='m-label'>🌡️ Ura / Pres.</span><span class='m-val'>{now['sst']:.1f}°</span><span class='m-unit'>{now['pres']:.0f} hPa</span></div>
        </div>
        """
        st.markdown(m_html, unsafe_allow_html=True)
        
        st.write("### ⏱️ Evolución Próximas 12 Horas (Cada 2h)")
        h_html = "<div class='scroll-wrapper'>"
        for i in range(idx_now, idx_now + 13, 2):
            r = df.iloc[i]
            h_html += f"<div class='hour-card'><h4>{r['time'].strftime('%H:%M')}</h4><p>🌬️ <span class='val-pro'>{r['wind_s']*3.6:.0f}/{r['wind_g']*3.6:.0f}</span></p><p>🌊 <span class='val-pro'>{r['wave_h']:.1f}m</span></p><p>💧 <span class='val-pro'>{r['curr_v']*3.6:.1f}</span></p></div>"
        st.markdown(h_html + "</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("📅 Previsión Detallada (Marítima y Viento)")
        hoy = ahora_local.date()
        for i in range(1, 5):
            d_t = hoy + timedelta(days=i)
            p_d, b_d, c_d = get_marea(d_t)
            st.markdown(f"<div class='main-card'><h4>{d_t.strftime('%A, %d %B')} | Plea: {p_d} | Coef: {c_d}</h4><div class='scroll-wrapper'>", unsafe_allow_html=True)
            day_html = ""
            df_day = df[df['time'].dt.date == d_t].iloc[6:22:3] # Mañana, Mediodía, Tarde, Noche
            for _, r in df_day.iterrows():
                day_html += f"<div class='hour-card'><h4>{r['time'].strftime('%H:%M')}</h4><p>🌬️ <span class='val-pro'>{r['wind_s']*3.6:.0f}/{r['wind_g']*3.6:.0f}</span></p><p>🌊 <span class='val-pro'>{r['wave_h']:.1f}m</span></p></div>"
            st.markdown(day_html + "</div></div>", unsafe_allow_html=True)

with tab3:
    st.subheader("🗺️ Plotter con Herramientas Tácticas")
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    
    # HERRAMIENTAS DE MAPA
    plugins.MeasureControl(position='topright', primary_length_unit='nauticalmiles', secondary_length_unit='meters').add_to(m)
    plugins.Draw(export=True, position='topleft').add_to(m)
    plugins.Fullscreen(position='topright').add_to(m)
    
    st_folium(m, width="100%", height=600, key="mapa_pro_v19")

with tab4:
    st.header("🐟 Manual de Pesca y Aparejos")
    e_list = [
        ("SARGOA", "Buscando la espuma en las rocas.", "Línea 0.35mm / Boya 20g / Bajo 0.30mm Fluorocarbono."),
        ("LUBINA", "Spinning con señuelos en el amanecer.", "Trenzado 0.18mm / Bajo 0.40mm / Grapa rápida."),
        ("DENTOIA", "Zoka con cebo vivo en profundidad.", "Trenzado 0.30mm / Bajo 0.70mm / Tándem hooks.")
    ]
    for name, desc, rig in e_list:
        with st.expander(f"📌 {name}"):
            st.write(desc)
            st.markdown(f"<div class='rig-info'><b>🛠️ MONTAJE:</b> {rig}</div>", unsafe_allow_html=True)
