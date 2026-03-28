import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
import folium
from folium import plugins
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN Y CONSTANTES ---
st.set_page_config(page_title="Txomin v.27.1 - Mutriku Pro", page_icon="🔱", layout="wide")

# ⚠️ RECUERDA: SUSTITUYE POR TU API KEY REAL DE OPENWEATHER 
API_KEY_WEATHER = st.secrets["OPENWEATHER_API_KEY"]
LAT_MUTRIKU, LON_MUTRIKU = 43.315, -2.38
ARCHIVO_MARCAS = "marcas_exito.csv"

# Inicializar archivo de bitácora si no existe
if not os.path.exists(ARCHIVO_MARCAS):
    pd.DataFrame(columns=["Nombre", "Lat", "Lon", "Ola", "Viento", "Temp_Agua", "Fecha"]).to_csv(ARCHIVO_MARCAS, index=False)

# Estilos Visuales para Móvil y Desktop
st.markdown("""
    <style>
        .stTabs [data-baseweb="tab"] { background-color: #F0F9FF; border-radius: 8px; padding: 10px; font-weight: bold; }
        .stTabs [aria-selected="true"] { background-color: #0369A1 !important; color: white !important; }
        .hour-block { background-color: white; border: 1px solid #BAE6FD; padding: 10px; border-radius: 12px; text-align: center; min-width: 120px; }
        .day-header { background-color: #0369A1; color: white; padding: 10px; border-radius: 8px; font-weight: bold; margin-top: 15px; }
        .tide-box { background-color: #E0F2FE; padding: 10px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-around; font-weight: bold; color: #0369A1; border: 1px dashed #0369A1; }
        .tip-card { background-color: #F8FAFC; border-left: 6px solid #0369A1; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
        .status-ok { color: #059669; font-weight: bold; font-size: 1.1rem; }
        .status-warn { color: #D97706; font-weight: bold; }
        .status-no { color: #DC2626; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS (MAREAS Y ORIENTACIÓN) ---
# Mareas para Mutriku (Sincronizadas con marzo 2026)
MAREAS_MUTRIKU = {
    "28/03": {"Plea": ["00:39", "13:29"], "Baja": ["06:58", "19:20"]},
    "29/03": {"Plea": ["01:49", "14:26"], "Baja": ["08:02", "20:17"]},
    "30/03": {"Plea": ["02:41", "15:09"], "Baja": ["08:49", "21:05"]}
}

def dir_viento_real(grados):
    # Procedencia: De dónde viene el viento
    dirs = ["N ↓", "NE ↙", "E ←", "SE ↖", "S ↑", "SO ↗", "O →", "NO ↘"]
    return dirs[round(grados / 45) % 8]

def dir_corr_real(grados):
    # Sentido: Hacia dónde fluye el agua
    dirs = ["N ↑", "NE ↗", "E →", "SE ↘", "S ↓", "SO ↙", "O ←", "NO ↖"]
    return dirs[round(grados / 45) % 8]

@st.cache_data(ttl=600)
def fetch_all_data(lat, lon):
    try:
        url_m = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height,ocean_current_velocity,ocean_current_direction,sea_surface_temperature&timezone=auto"
        url_w = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY_WEATHER}&units=metric"
        res_m = requests.get(url_m).json()
        res_w = requests.get(url_w).json()
        return res_m, res_w
    except Exception as e:
        return None, {"message": str(e)}

# --- 3. INTERFAZ Y PESTAÑAS ---
st.title("🔱 Txomin: Inteligencia Naval Mutriku v.27.1")

tab1, tab2, tab3 = st.tabs(["📊 PREVISIÓN Y MAREAS", "🗺️ MAPA Y ENFILACIONES", "🎣 ASESOR TÁCTICO"])

# Obtenemos datos base
dm_m, dw_m = fetch_all_data(LAT_MUTRIKU, LON_MUTRIKU)

# --- PESTAÑA 1: PREVISIÓN (CON BLINDAJE) ---
with tab1:
    if dw_m and 'list' in dw_m:
        dias = []
        for item in dw_m['list']:
            d = datetime.fromtimestamp(item['dt']).strftime('%d/%m')
            if d not in dias: dias.append(d)
        
        for d_key in dias[:3]:
            # Cabecera Día y Mareas
            st.markdown(f"<div class='day-header'>📅 DÍA {d_key}</div>", unsafe_allow_html=True)
            if d_key in MAREAS_MUTRIKU:
                m = MAREAS_MUTRIKU[d_key]
                st.markdown(f"<div class='tide-box'>🔼 PLEAMAR: {m['Plea'][0]} | {m['Plea'][1]} &nbsp;&nbsp; 🔽 BAJAMAR: {m['Baja'][0]} | {m['Baja'][1]}</div>", unsafe_allow_html=True)
            
            # Bloques Horarios
            items_dia = [x for x in dw_m['list'] if datetime.fromtimestamp(x['dt']).strftime('%d/%m') == d_key]
            cols = st.columns(len(items_dia))
            for idx, item in enumerate(items_dia):
                with cols[idx]:
                    m_idx = dw_m['list'].index(item) * 3
                    # Verificación de datos marinos para evitar crash
                    if dm_m and 'hourly' in dm_m and m_idx < len(dm_m['hourly']['wave_height']):
                        ola_h = dm_m['hourly']['wave_height'][m_idx]
                        v_corr = dm_m['hourly']['ocean_current_velocity'][m_idx] * 3.6
                        d_corr = dir_corr_real(dm_m['hourly']['ocean_current_direction'][m_idx])
                    else:
                        ola_h, v_corr, d_corr = 0.0, 0.0, "N/A"

                    st.markdown(f"""<div class='hour-block'>
                        <b style='color:#0369A1;'>{datetime.fromtimestamp(item['dt']).strftime('%H:%M')}</b><br>
                        🌬️ {item['wind']['speed']*3.6:.1f} {dir_viento_real(item['wind']['deg'])}<br>
                        🌊 {ola_h:.1f}m<br>
                        💧 {v_corr:.1f} {d_corr}
                    </div>""", unsafe_allow_html=True)
    else:
        st.error("❌ ERROR DE CONEXIÓN: Revisa tu API KEY de OpenWeather.")
        if dw_m and 'message' in dw_m: st.warning(f"Detalle: {dw_m['message']}")

# --- PESTAÑA 2: MAPA (ENFILACIONES Y IHM) ---
with tab2:
    st.subheader("🗺️ Plotter Táctico (Usa la regla para rumbos)")
    c_m, c_i = st.columns([3, 1])
    with c_m:
        m = folium.Map(location=[LAT_MUTRIKU, LON_MUTRIKU], zoom_start=15)
        # Capa IHM (Instituto Hidrográfico de la Marina)
        folium.WmsTileLayer(url='https://ideihm.covam.es/wms/cartografia_espanola?', layers='relieve,isobatas', name='IHM Batimetría', fmt='image/png', transparent=True, overlay=True).add_to(m)
        folium.TileLayer(tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        
        # Herramientas de Dibujo para Enfilaciones
        plugins.Draw(position='topleft', draw_options={'polyline':{'shapeOptions':{'color':'#FF0000'}}, 'polygon':False, 'circle':False, 'marker':True}).add_to(m)
        plugins.MeasureControl(position='topright', primary_length_unit='meters').add_to(m)
        
        # Marcas de éxito guardadas
        df_m = pd.read_csv(ARCHIVO_MARCAS)
        for _, r in df_m.iterrows():
            folium.Marker([r['Lat'], r['Lon']], popup=r['Nombre'], icon=folium.Icon(color='orange', icon='star')).add_to(m)

        out = st_folium(m, width="100%", height=500, key="plotter_v27_1")

    with c_i:
        if out["last_clicked"]:
            lat_c, lon_c = out["last_clicked"]["lat"], out["last_clicked"]["lng"]
            st.success("📍 Posición Seleccionada")
            st.code(f"{lat_c:.5f}, {lon_c:.5f}")
            with st.form("guardar_punto"):
                nombre = st.text_input("Nombre de la marca:")
                if st.form_submit_button("💾 GUARDAR MARCA"):
                    dm_p, dw_p = fetch_all_data(lat_c, lon_c)
                    nueva = pd.DataFrame([[nombre, lat_c, lon_c, dm_p['hourly']['wave_height'][0], dw_p['list'][0]['wind']['speed']*3.6, dm_p['hourly']['sea_surface_temperature'][0], datetime.now().strftime("%Y-%m-%d")]], columns=["Nombre", "Lat", "Lon", "Ola", "Viento", "Temp_Agua", "Fecha"])
                    nueva.to_csv(ARCHIVO_MARCAS, mode='a', header=False, index=False)
                    st.rerun()
        else:
            st.info("Traza líneas de costa y clica en el cruce.")

# --- PESTAÑA 3: ASESOR DINÁMICO ---
with tab3:
    st.header("🎣 Recomendaciones Tácticas")
    if dm_m and 'hourly' in dm_m:
        ola = dm_m['hourly']['wave_height'][0]
        viento = dw_m['list'][0]['wind']['speed'] * 3.6 if 'list' in dw_m else 0

        # SARGO
        st.subheader("🐟 SARGO")
        if 0.8 <= ola <= 1.7:
            st.markdown("<span class='status-ok'>🌊 ¡BUENA MAR PARA SARGO!</span>", unsafe_allow_html=True)
            txt_s = "Condiciones perfectas de espuma. El sargo estará en la piedra."
        else:
            st.markdown("<span class='status-no'>💤 MAR INADECUADA</span>", unsafe_allow_html=True)
            txt_s = "Agua muy parada o muy brava. Pesca fino o busca resguardo."
        st.markdown(f"<div class='tip-card'><b>Tip:</b> {txt_s}<br>Braza 2m Fluorocarbono. Cebo: Gamba o masilla.</div>", unsafe_allow_html=True)

        # CHIPIRÓN (Separado)
        st.subheader("🦑 CHIPIRÓN")
        if ola < 0.7 and viento < 15:
            st.markdown("<span class='status-ok'>🦑 ¡BUENA MAR PARA CHIPIRÓN!</span>", unsafe_allow_html=True)
            txt_ch = "Agua plato. Poteras (Egis) navegarán perfectas."
        else:
            st.markdown("<span class='status-no'>❌ DEMASIADO MOVIMIENTO</span>", unsafe_allow_html=True)
            txt_ch = "El chipi no atacará bien. Busca una cala de arena resguardada."
        st.markdown(f"<div class='tip-card'><b>Tip:</b> {txt_ch}<br>Colores naturales. Movimientos lentos cerca del fondo.</div>", unsafe_allow_html=True)

        # CHICHARRO (Nueva sección)
        st.subheader("🐠 CHICHARRO")
        if viento > 10:
            st.markdown("<span class='status-ok'>🏎️ ¡BUEN DÍA PARA CACEA!</span>", unsafe_allow_html=True)
            txt_chi = "El viento riza el agua, ideal para esconder el aparejo."
        else:
            st.markdown("<span class='status-warn'>⚖️ MAR PARADA</span>", unsafe_allow_html=True)
            txt_chi = "Busca los bandos de pájaros y cortes de corriente."
        st.markdown(f"<div class='tip-card'><b>Tip:</b> {txt_chi}<br>Cacea ligera (3.5 nudos). Plumillas blancas o vinilos.</div>", unsafe_allow_html=True)

        # CABRARROCA
        st.subheader("🦂 CABRARROCA")
        st.markdown("<span class='status-ok'>✅ SIEMPRE DISPONIBLE</span>", unsafe_allow_html=True)
        st.markdown(f"<div class='tip-card'>Fondo de piedra pura. Plomo 120g vertical. Braza corta (40cm). Cebo: Chipirón o sardina.</div>", unsafe_allow_html=True)

st.divider()
st.info("⚖️ Respeta siempre las tallas mínimas (R.D. 1615/2011). ¡Buena proa, patrón!")
