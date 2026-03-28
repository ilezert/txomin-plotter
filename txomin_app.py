import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Txomin v.29 - Coeficientes Mutriku", page_icon="🔱", layout="wide")

API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ARCHIVO_MARCAS = "marcas_exito.csv"

if not os.path.exists(ARCHIVO_MARCAS):
    pd.DataFrame(columns=["Nombre", "Lat", "Lon", "Ola", "Viento", "Temp_Agua", "Fecha"]).to_csv(ARCHIVO_MARCAS, index=False)

# Estilos Visuales Pro
st.markdown("""
    <style>
        .stTabs [data-baseweb="tab"] { background-color: #F0F9FF; border-radius: 8px; padding: 10px; font-weight: bold; }
        .stTabs [aria-selected="true"] { background-color: #0369A1 !important; color: white !important; }
        .hour-block { background-color: white; border: 1px solid #BAE6FD; padding: 10px; border-radius: 12px; text-align: center; min-width: 140px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
        .day-header { background-color: #0369A1; color: white; padding: 10px; border-radius: 8px; font-weight: bold; margin-top: 15px; }
        .tide-box { background-color: #E0F2FE; padding: 10px; border-radius: 8px; margin-bottom: 10px; display: flex; flex-direction: column; align-items: center; font-weight: bold; color: #0369A1; border: 1px dashed #0369A1; }
        .coef-badge { background-color: #0369A1; color: white; padding: 2px 10px; border-radius: 15px; font-size: 0.8rem; margin-top: 5px; }
        .rec-pesca { color: #059669; font-size: 0.85rem; font-weight: bold; margin-top: 5px; border-top: 1px solid #E2E8F0; padding-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE MAREAS Y COEFICIENTES ---
# Datos actualizados con coeficiente (0-120)
MAREAS_MUTRIKU = {
    "28/03": {"Plea": ["00:39", "13:29"], "Baja": ["06:58", "19:20"], "Coef": 85},
    "29/03": {"Plea": ["01:49", "14:26"], "Baja": ["08:02", "20:17"], "Coef": 92},
    "30/03": {"Plea": ["02:41", "15:09"], "Baja": ["08:49", "21:05"], "Coef": 95},
    "31/03": {"Plea": ["03:28", "15:52"], "Baja": ["09:34", "21:50"], "Coef": 88}
}

def get_info_coef(coef):
    if coef >= 80: return "🌊 MAREA VIVA (Corriente fuerte)"
    elif coef <= 40: return "💧 MAREA MUERTA (Agua parada)"
    return "⚓ MAREA MEDIA"

def dir_viento_real(grados):
    dirs = ["N ↓", "NE ↙", "E ←", "SE ↖", "S ↑", "SO ↗", "O →", "NO ↘"]
    return dirs[round(grados / 45) % 8]

def asesor_horario(ola, viento, coef):
    # Lógica combinada con Coeficiente
    if 0.8 <= ola <= 1.8:
        return "🐟 SARGO (Espuma)"
    elif ola < 0.7 and viento < 12 and coef < 70:
        return "🦑 CHIPIRÓN (Calma)"
    elif viento >= 10 and ola < 1.3:
        return "🐠 CHICHARRO (Cacea)"
    else:
        return "🦂 CABRARROCA (Fondo)"

@st.cache_data(ttl=600)
def fetch_all_data(lat, lon):
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height,ocean_current_velocity,ocean_current_direction&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY_WEATHER}&units=metric"
        return requests.get(url_m).json(), requests.get(url_w).json()
    except: return None, None

# --- 3. INTERFAZ ---
st.title("🔱 Txomin v.29.0 - Con Coeficiente de Marea")

tab1, tab2, tab3 = st.tabs(["📊 PREVISIÓN Y COEFICIENTES", "🗺️ MAPA DE MARCAS", "🐟 CONSEJOS"])

dm_m, dw_m = fetch_all_data(LAT_MUTRIKU, LON_MUTRIKU)

with tab1:
    if dw_m and 'list' in dw_m:
        dias = []
        for item in dw_m['list']:
            d = datetime.fromtimestamp(item['dt']).strftime('%d/%m')
            if d not in dias: dias.append(d)
        
        for d_key in dias[:3]:
            st.markdown(f"<div class='day-header'>📅 DÍA {d_key}</div>", unsafe_allow_html=True)
            
            # Bloque de Mareas con Coeficiente
            if d_key in MAREAS_MUTRIKU:
                m = MAREAS_MUTRIKU[d_key]
                info_c = get_info_coef(m['Coef'])
                st.markdown(f"""
                <div class='tide-box'>
                    <div>🔼 PLEA: {m['Plea'][0]} | {m['Plea'][1]} &nbsp;&nbsp; 🔽 BAJA: {m['Baja'][0]} | {m['Baja'][1]}</div>
                    <div class='coef-badge'>COEFICIENTE: {m['Coef']} - {info_c}</div>
                </div>
                """, unsafe_allow_html=True)
            
            items_dia = [x for x in dw_m['list'] if datetime.fromtimestamp(x['dt']).strftime('%d/%m') == d_key]
            cols = st.columns(len(items_dia))
            for idx, item in enumerate(items_dia):
                with cols[idx]:
                    m_idx = dw_m['list'].index(item) * 3
                    if dm_m and 'hourly' in dm_m and m_idx < len(dm_m['hourly']['wave_height']):
                        ola_h = dm_m['hourly']['wave_height'][m_idx]
                        v_viento = item['wind']['speed'] * 3.6
                        coef_hoy = MAREAS_MUTRIKU.get(d_key, {}).get('Coef', 60)
                        rec = asesor_horario(ola_h, v_viento, coef_hoy)
                        
                        st.markdown(f"""<div class='hour-block'>
                            <b style='color:#0369A1;'>{datetime.fromtimestamp(item['dt']).strftime('%H:%M')}</b><br>
                            🌬️ {v_viento:.1f} {dir_viento_real(item['wind']['deg'])}<br>
                            🌊 {ola_h:.1f}m<br>
                            <div class='rec-pesca'>{rec}</div>
                        </div>""", unsafe_allow_html=True)

# (Resto del código de Mapa y Tips igual que v.28)
with tab2:
    st.subheader("🗺️ Plotter de Enfilaciones IHM")
    m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
    folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    folium.WmsTileLayer(url='https://ideihm.covam.es/wms/cartografia_espanola?', layers='relieve,isobatas', name='IHM Fondo', fmt='image/png', transparent=True, overlay=True).add_to(m)
    plugins.Draw(position='topleft').add_to(m)
    st_folium(m, width="100%", height=500)

with tab3:
    st.header("🐟 Consejos de Pesca")
    st.info("💡 Tip de Coeficiente: Con coeficientes mayores a 80 (vivas), busca zonas de abrigo donde el pescado no tenga que luchar tanto contra la corriente.")
