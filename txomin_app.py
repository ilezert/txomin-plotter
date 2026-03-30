import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.40.4", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# --- ESTILO WINDFINDER ROJO/BLANCO ---
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #1E293B; }
        .main-title { color: #DC2626; text-align: center; font-weight: 900; text-transform: uppercase; border-bottom: 3px solid #DC2626; padding-bottom: 10px; }
        .main-card { background: #FFFFFF; padding: 20px; border-radius: 15px; border: 2px solid #DC2626; text-align: center; margin-bottom: 20px; position: relative; }
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; border-radius: 15px 15px 0 0; }
        .bg-green { background-color: #10B981; } .bg-yellow { background-color: #FBBF24; } .bg-red { background-color: #EF4444; }
        .metric-box { background: #F8FAFC; padding: 12px; border-radius: 10px; border: 1px solid #E2E8F0; text-align: center; }
        .m-label { color: #64748B; font-size: 0.75rem; text-transform: uppercase; font-weight: bold; }
        .m-val { color: #DC2626; font-size: 2rem; font-weight: 900; display: block; }
        .tide-timer { background: #FEF2F2; border: 2px dashed #DC2626; border-radius: 10px; padding: 10px; margin: 15px 0; font-weight: 900; color: #DC2626; font-size: 1.2rem; }
        .scroll-wrapper { display: flex; overflow-x: auto; gap: 12px; padding: 10px 0 20px 0; width: 100%; }
        .hour-card { flex: 0 0 auto; width: 200px; background: #FFFFFF; border-radius: 12px; padding: 15px; border: 1px solid #DC2626; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .hour-card h4 { margin: 0 0 10px 0; color: #FFFFFF; background: #DC2626; border-radius: 5px; padding: 5px; text-align: center; }
        .data-row { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.85rem; font-weight: 700; border-bottom: 1px solid #F1F5F9; }
        .rig-info { background: #F8FAFC; border-radius: 8px; padding: 10px; border-left: 4px solid #DC2626; font-size: 0.85rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA ---
def flecha(deg):
    return ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"][round(deg / 45) % 8]

def get_marea_info(f):
    dia = f.day
    p_hora, b_hora = (dia % 12) + 2, ((dia % 12) + 8) % 24
    plea_dt = f.replace(hour=p_hora, minute=0, second=0)
    baja_dt = f.replace(hour=b_hora, minute=30, second=0)
    if f < plea_dt: return "PLEAMAR", plea_dt, 50 + (dia * 3 % 45)
    elif f < baja_dt: return "BAJAMAR", baja_dt, 50 + (dia * 3 % 45)
    else: return "PLEAMAR", plea_dt + timedelta(hours=12), 50 + (dia * 3 % 45)

@st.cache_data(ttl=600)
def fetch_all_data():
    try:
        u_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,wave_period,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto&forecast_days=6"
        u_w = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl&timezone=auto&forecast_days=6"
        dm, dw = requests.get(u_m).json(), requests.get(u_w).json()
        return pd.DataFrame({
            'time': pd.to_datetime(dm['hourly']['time']).dt.tz_localize('UTC').dt.tz_convert(ZONA_HORARIA),
            'wave_h': dm['hourly']['wave_height'], 'wave_d': dm['hourly']['wave_direction'], 'wave_p': dm['hourly']['wave_period'],
            'curr_v': dm['hourly']['ocean_current_velocity'], 'curr_d': dm['hourly']['ocean_current_direction'],
            'wind_s': dw['hourly']['wind_speed_10m'], 'wind_g': dw['hourly']['wind_gusts_10m'], 'wind_d': dw['hourly']['wind_direction_10m'],
            'sst': dm['hourly']['sea_surface_temperature'], 'pres': dw['hourly']['pressure_msl']
        })
    except: return None

# --- 3. INTERFAZ ---
st.markdown("<h1 class='main-title'>🔱 TXOMIN - MUTRIKU TACTICAL</h1>", unsafe_allow_html=True)
t0, t1, t2, t3 = st.tabs(["⚓ ORAIN", "📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK"])

df = fetch_all_data()

with t0:
    if df is not None:
        idx = (df['time'] >= ahora_local).idxmax()
        now = df.loc[idx]
        tipo, m_dt, coef = get_marea_info(ahora_local)
        faltan = m_dt - ahora_local
        color = "bg-green" if now['wave_h'] < 1.4 else "bg-yellow"
        if now['wind_g'] > 30: color = "bg-red"

        st.markdown(f"<div class='main-card'><div class='status-bar {color}'></div><h2>{ahora_local.strftime('%H:%M')}</h2><div class='tide-timer'>⏳ {tipo} en {faltan.seconds//3600}h {(faltan.seconds//60)%60}min (Coef: {coef})</div></div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='metric-box'><span class='m-label'>🌬️ Viento</span><span class='m-val'>{now['wind_s']*3.6:.0f}/{now['wind_g']*3.6:.0f}</span><p>{flecha(now['wind_d'])} km/h</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-box'><span class='m-label'>🌊 Olatua</span><span class='m-val'>{now['wave_h']:.1f}m</span><p>T: {now['wave_p']:.0f}s</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-box'><span class='m-label'>🌡️ Ura</span><span class='m-val'>{now['sst']:.1f}°</span><p>{now['pres']:.0f} hPa</p></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='metric-box'><span class='m-label'>💧 Korrontea</span><span class='m-val'>{now['curr_v']*3.6:.1f}</span><p>{flecha(now['curr_d'])} km/h</p></div>", unsafe_allow_html=True)

        st.write("### ⏱️ PRÓXIMAS 12 HORAS")
        h_html = "<div class='scroll-wrapper'>"
        for i in range(idx, idx + 13, 2):
            r = df.iloc[i]
            stars = "⭐" * (3 if r['wave_h'] < 1.5 else 1)
            h_html += f"""<div class='hour-card'><h4>{r['time'].strftime('%H:%M')}</h4>
            <div class='data-row'><span>🌬️ Viento</span><span style='color:#DC2626;'>{r['wind_s']*3.6:.0f}/{r['wind_g']*3.6:.0f}</span></div>
            <div class='data-row'><span>🌊 Ola/T</span><span>{r['wave_h']:.1f}m/{r['wave_p']:.0f}s</span></div>
            <div class='data-row'><span>💧 Korr.</span><span>{r['curr_v']*3.6:.1f} {flecha(r['curr_d'])}</span></div>
            <div class='data-row' style='border:none;'><span>🐟 Peces</span><span>{stars}</span></div></div>"""
        st.markdown(h_html + "</div>", unsafe_allow_html=True)

with t1:
    if df is not None:
        hoy = ahora_local.date()
        for i in range(1, 5):
            d_t = hoy + timedelta(days=i)
            p_t, b_t, c_t = get_marea_info(ahora_local.replace(day=d_t.day))
            st.markdown(f"<div class='main-card' style='text-align:left;'><h4>{d_t.strftime('%A, %d %B')} | Coef: {c_t}</h4><p>Plea: {p_t} | Baja: {b_t}</p></div>", unsafe_allow_html=True)

with t2:
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    plugins.MeasureControl(position='topright').add_to(m)
    plugins.Draw(position='topleft').add_to(m)
    plugins.Fullscreen().add_to(m)
    st_folium(m, width="100%", height=600, key="mapa_v404")

with t3:
    st.header("🐟 ESPEZIEAK ETA APAILUAK")
    esp = [("SARGOA", "Aparretan, 0.8m-1.5m onena.", "Línea 0.35 / Bua 20g / Bajo 0.30mm.", "Tip: Izkira bizia erabili."),
           ("LUPINA", "Spinning egunsentian.", "Trenzado 0.18 / Bajo 0.40mm.", "Tip: Señuelo mugikorrak aparretan."),
           ("TXIPIROIA", "Poterak 2.0-2.5 ilunabarrean.", "Trenzado 0.10 / Bajo 0.22mm.", "Tip: Mugimendu leunak."),
           ("DENTOIA", "Hondo handiak, zoka.", "Trenzado 0.30 / Bajo 0.70mm.", "Tip: Txibia bizia da onena."),
           ("URRABURUA", "Hondarrezko hondoetan.", "Corredizo / Bajo 3m.", "Tip: Karramarroa beita gisa."),
           ("TXITXARROA", "Portuetan gauez.", "Sabiki / Bajo 0.30mm.", "Tip: Argi fokuetatik hurbil."),
           ("MOXARRA", "Harri inguruetan.", "0.30mm / Bua ligera.", "Tip: Zizare korearra erabili."),
           ("BARBINA", "Hondarretan.", "Chambel / Amuak Nº 12.", "Tip: Beita hondo-hondoan."),
           ("KABRARROKA", "Harri puruan.", "Paternoster / Madre 0.45.", "Tip: Kontuz arantzekin!"),
           ("BOGA", "Portuan.", "0.18mm / Bua pluma.", "Tip: Ogi apurrak erabili.")]
    c1, c2 = st.columns(2)
    for i, (n, d, r, t) in enumerate(esp):
        with (c1 if i < 5 else c2):
            with st.expander(f"📌 {n}"):
                st.write(d)
                st.markdown(f"<div class='rig-info'><b>🛠️ APAILUA:</b> {r}</div>", unsafe_allow_html=True)
                st.info(t)
