import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.33.11 - Tactical", page_icon="🔱", layout="wide")

LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ZONA_HORARIA = ZoneInfo("Europe/Madrid")
ahora_local = datetime.now(ZONA_HORARIA)

# CSS Profesional Táctico (Inspirado en la imagen)
st.markdown("""
    <style>
        /* Fondo Principal Azul Profundo */
        .stApp { background-color: #011627; color: white; }
        
        /* Título Principal */
        .main-title { color: #FBBF24; text-transform: uppercase; font-weight: 900; font-size: 2.2rem; text-align: center; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }

        /* Tarjeta Principal (Semáforo y Actividad) */
        .main-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 25px; border: 1px solid rgba(251, 191, 36, 0.2); position: relative; overflow: hidden; }
        .status-bar { height: 12px; width: 100%; position: absolute; top: 0; left: 0; }
        .bg-green { background-color: #10B981; }
        .bg-yellow { background-color: #FBBF24; }
        .bg-red { background-color: #EF4444; }
        
        /* Tarjetas de Métricas Principales */
        .metric-card { background: rgba(30, 41, 59, 0.5); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.1); height: 100%; }
        .metric-title { text-transform: uppercase; font-size: 0.9rem; color: #BAE6FD; margin-bottom: 8px; font-weight: bold; }
        .metric-value { color: #FBBF24 !important; font-size: 2.5rem; margin: 0; font-weight: 800; line-height: 1; }
        .metric-unit { font-size: 1rem; color: white; }
        .metric-icon { font-size: 1.2rem; margin-right: 5px; color: #FBBF24; }
        
        /* Badge de Actividad y Mareas */
        .badge { background: #1E293B; color: #FBBF24; padding: 8px 15px; border-radius: 25px; font-weight: bold; font-size: 1rem; border: 1px solid #FBBF24; display: inline-block; margin-top: 10px; }
        
        /* Evolución Horaria (Carrusel Horizontal) */
        .scroll-wrapper { display: flex !important; flex-direction: row !important; overflow-x: auto !important; gap: 12px; padding: 10px 0 20px 0; width: 100%; scroll-snap-type: x mandatory; }
        .scroll-wrapper::-webkit-scrollbar { height: 6px; }
        .scroll-wrapper::-webkit-scrollbar-thumb { background: rgba(251, 191, 36, 0.5); border-radius: 10px; }
        
        .hour-card { flex: 0 0 auto; width: 170px; background: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 12px; text-align: center; color: #1E293B !important; border-top: 5px solid #0369A1; scroll-snap-align: start; }
        .hour-card h4 { margin: 0 0 8px 0; color: #0369A1 !important; font-weight: 800; border-bottom: 1px solid #DDD; padding-bottom: 4px; }
        .hour-card p { margin: 5px 0; font-size: 0.85rem; font-weight: 700; display: flex; justify-content: space-between; align-items: center; }
        .val-blue { color: #0369A1; font-weight: 800; }

        /* Pestañas Inferiores */
        .day-forecast-card { background: rgba(30, 41, 59, 0.5); border-radius: 15px; padding: 15px; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.1); }
        .stTabs [data-baseweb="tab"] { color: white !important; font-weight: bold; font-size: 1rem; }
        .stTabs [aria-selected="true"] { color: #FBBF24 !important; border-bottom-color: #FBBF24 !important; }
        
        /* Especies */
        .rig-info { background: #F1F5F9; border-radius: 8px; padding: 10px; margin-top: 5px; color: #334155; font-size: 0.85rem; border-left: 4px solid #FBBF24; text-align: left; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE CÁLCULO ---
def flecha_desde(grados):
    return ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"][round(grados / 45) % 8]

def generar_marea(fecha):
    dia = fecha.day
    plea = f"{(dia % 12) + 2:02d}:00"
    baja = f"{((dia % 12) + 8) % 24:02d}:30"
    coef = 50 + (dia * 3 % 45)
    return plea, baja, coef

def get_semaforo_info(ola, viento_avg, viento_gust):
    if ola > 2.0 or viento_gust > 35: return "bg-red", "🛑 ARRISKUTSUA / PELIGRO"
    if viento_avg > 12 or ola > 1.5 or viento_gust > 25: return "bg-yellow", "🟡 KONTUZ / PRECAUCIÓN"
    return "bg-green", "🟢 EGOKIA / IDEAL"

def calcular_actividad(ola, viento, coef, temp, pres):
    p = 1
    if 60 <= coef <= 95: p += 1
    if 1010 <= pres <= 1025: p += 1
    if 13 <= temp <= 19: p += 1
    if 0.5 <= ola <= 1.5: p += 1
    if viento > 25: p -= 1
    score = max(1, min(5, p))
    return "⭐" * score + "🌑" * (5 - score)

@st.cache_data(ttl=600)
def fetch_data_bunker():
    try:
        # Intentamos conectar con el satélite
        u_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wave_height,wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto&forecast_days=7"
        u_w = f"https://api.open-meteo.com/v1/forecast?latitude={LAT_MUTRIKU}&longitude={LON_MUTRIKU}&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl&timezone=auto&forecast_days=7"
        dm, dw = requests.get(u_m, timeout=5).json(), requests.get(u_w, timeout=5).json()
        df = pd.DataFrame({
            'time': pd.to_datetime(dm['hourly']['time']).dt.tz_localize('UTC').dt.tz_convert(ZONA_HORARIA),
            'wave_h': dm['hourly']['wave_height'], 'wave_d': dm['hourly']['wave_direction'],
            'curr_v': dm['hourly']['ocean_current_velocity'], 'curr_d': dm['hourly']['ocean_current_direction'],
            'sst': dm['hourly']['sea_surface_temperature'],
            'wind_s': dw['hourly']['wind_speed_10m'], 'wind_g': dw['hourly']['wind_gusts_10m'],
            'wind_d': dw['hourly']['wind_direction_10m'], 'pres': dw['hourly']['pressure_msl']
        })
        return df, "OK"
    except Exception as e:
        # Si el satélite falla, devolvemos un DataFrame vacío y el estado de error
        return None, str(e)

# --- 3. INTERFAZ ---
# Título Táctico
st.markdown("<h1 class='main-title'>🔱 Txomin - Mutriku Tactical</h1>", unsafe_allow_html=True)

# Intentamos cargar datos con el sistema búnker
df_master, status = fetch_data_bunker()

if df_master is not None:
    # Sincronización horaria exacta
    idx_ahora = (df_master['time'] >= ahora_local).idxmax()
    now = df_master.loc[idx_ahora]

    # Datos principales
    ola_act, v_avg, v_gust = now['wave_h'], now['wind_s']*3.6, now['wind_g']*3.6
    c_cls, s_txt = get_semaforo_info(ola_act, v_avg, v_gust)
    plea, baja, coef = generar_marea(ahora_local)
    stars = calcular_actividad(ola_act, v_avg, coef, now['sst'], now['pres'])

    # --- PORTADA TÁCTICA ---
    # Tarjeta Principal: Semáforo y Actividad
    st.markdown(f"""
        <div class='main-card'>
            <div class='status-bar {c_cls}'></div>
            <h2>MUTRIKU {ahora_local.strftime('%H:%M')}</h2>
            <p style='font-weight:bold; color:#FBBF24; font-size:1.1rem;'>{s_txt}</p>
            <div class='activity-badge'>Arrainen Jarduera: {stars}</div>
        </div>
    """, unsafe_allow_html=True)

    # Rejilla de Métricas Principales (4 columnas)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f"<div class='metric-card'><div class='metric-title'>🌬️ Viento (M/R)</div><div class='metric-value'>{v_avg:.0f}/{v_gust:.0f}</div><div class='metric-unit'>km/h</div><p>{flecha_desde(now['wind_d'])}</p></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='metric-card'><div class='metric-title'>🌊 Olatua</div><div class='metric-value'>{ola_act:.1f}</div><div class='metric-unit'>m</div><p>{flecha_desde(now['wave_d'])}</p></div>", unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='metric-card'><div class='metric-title'>🌡️ Ura</div><div class='metric-value'>{now['sst']:.1f}</div><div class='metric-unit'>°C</div><p>{now['pres']:.0f} hPa</p></div>", unsafe_allow_html=True)
    with m4: st.markdown(f"<div class='metric-card'><div class='metric-title'>💧 Korrontea</div><div class='metric-value'>{now['curr_v']*3.6:.1f}</div><div class='metric-unit'>km/h</div><p>{flecha_desde(now['curr_d'])}</p></div>", unsafe_allow_html=True)

    # Tarjeta de Mareas
    st.markdown(f"<div class='main-card' style='background: rgba(16, 185, 129, 0.2);'><p style='margin:0; font-weight:bold; font-size:1.1rem;'>⏳ Itsasgora: {plea} | Itsasbehera: {baja} | Coef: {coef}</p></div>", unsafe_allow_html=True)

    # Evolución Horaria (Carrusel Horizontal)
    st.write("### ⏱️ Gaurko Eboluzio Taktikoa (2 Orduro)")
    html_h = "<div class='scroll-wrapper'>"
    for i in range(idx_ahora, min(idx_ahora + 16, len(df_master)), 2):
        r = df_master.iloc[i]
        v_a, v_g, o = r['wind_s']*3.6, r['wind_g']*3.6, r['wave_h']
        c = r['curr_v'] * 3.6
        html_h += f"""<div class='hour-card'>
            <h4>{r['time'].strftime('%H:%M')}</h4>
            <p>🌬️ Haizea <span class='val-blue'>{v_a:.0f}/{v_g:.0f} {flecha_desde(r['wind_d'])}</span></p>
            <p>🌊 Olatua <span class='val-blue'>{o:.1f}m {flecha_desde(r['wave_d'])}</span></p>
            <p>💧 Korr. <span class='val-blue'>{c:.1f} {flecha_desde(r['curr_d'])}</span></p>
        </div>"""
    st.markdown(html_h + "</div>", unsafe_allow_html=True)

else:
    # --- MODO BÚNKER ACTIVADO (API CAÍDA) ---
    st.error("⚠️ KONEXIO AKATSA: Satelitea ez dabil momentuz.")
    st.warning("Pestañetako informazioa (Mapa, Especies) eskuragarri dago.")
    # Datos por defecto o vacíos para la portada si no hay API
    plea, baja, coef = generar_marea(ahora_local)
    st.markdown(f"<div class='main-card' style='background: rgba(16, 185, 129, 0.2);'><p style='margin:0; font-weight:bold; font-size:1.1rem;'>⏳ Marea hurbil: Itsasgora: {plea} | Itsasbehera: {baja}</p></div>", unsafe_allow_html=True)

# --- 5. PESTAÑAS INFERIORES (SIEMPRE VISIBLES) ---
st.divider()
t_labels = ["📅 4 EGUN", "🗺️ MAPA", "🐟 ESPEZIEAK", "🛠️ PERFIL"]
tab_d, tab_m, tab_e, tab_p = st.tabs(t_labels)

with tab_d:
    if df_master is not None:
        hoy = ahora_local.date()
        for i in range(1, 5):
            d_target = hoy + timedelta(days=i)
            p, b, coef = generar_marea(d_target)
            df_day = df_master[df_master['time'].dt.date == d_target]
            if not df_day.empty:
                r12 = df_day.iloc[len(df_day)//2]
                v_a12, v_g12, o_12 = r12['wind_s']*3.6, r12['wind_g']*3.6, r12['wave_h']
                c_cls, s_txt = get_semaforo_info(o_12, v_a12, v_g12)
                st.markdown(f"<div class='day-forecast-card'><div class='status-bar {c_cls}'></div><div style='display:flex; justify-content:space-between;'><h3>{d_target.strftime('%A, %b %d')}</h3><b>{s_txt}</b></div><p>🔽 Plea: {p} / 🔼 Baja: {b} | Coef: {coef}</p><div class='scroll-wrapper'>", unsafe_allow_html=True)
                html_day = ""
                for _, r in df_day.iloc[8:22:2].iterrows():
                    v_a, v_g, o = r['wind_s']*3.6, r['wind_g']*3.6, r['wave_h']
                    html_day += f"<div class='hour-card'><h4>{r['time'].strftime('%H:%M')}</h4><p>🌬️ {v_a:.0f}/{v_g:.0f}</p><p>🌊 {o:.1f}m</p></div>"
                st.markdown(html_day + "</div></div></div>", unsafe_allow_html=True)
    else:
        st.info("⏳ Iragarpen meteorologikoa ez dago erabilgarri momentu honetan.")

with tab_m:
    st.subheader("🗺️ Plotter Taktikoa (Mutriku)")
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    st_folium(m, width="100%", height=500, key="plot_tactical_v3311")

with tab_e:
    st.header("🐟 Arrainak eta Apailuak")
    e_list = [
        ("SARGOA", "Aparretan, 0.8m-1.5m artean onena. Izkira.", "0.35mm / Bua 20g / Bajo 0.30mm Fluoroc."),
        ("LUPINA", "Spinning señueloekin egunsentian edo ilunabarrean.", "Trenzado 0.18 / Bajo 0.40mm / Grapa rápida."),
        ("TXIPIROIA", "Poterak 2.0-2.5 ur geldoetan ilunabarrean.", "Trenzado 0.10 / Bajo 0.22mm Fluoroc.")
    ]
    for name, tip, rig in e_list:
        with st.expander(f"📌 {name}"):
            st.write(tip)
            st.markdown(f"<div class='rig-info'><b>🛠️ APAILUA:</b> {rig}</div>", unsafe_allow_html=True)

with tab_p:
    st.header("🛠️ Perfil Taktikoa")
    st.write("Datu pertsonalak, lizentziak eta doikuntza aurreratuak hemendik kudeatuko dira.")
