import streamlit as st
import requests
import pandas as pd
import math
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ══════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN GLOBAL
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Txomin v2.0 | Mutriku",
    page_icon="🔱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LAT, LON = 43.315, -2.38
TZ = ZoneInfo("Europe/Madrid")
ahora = datetime.now(TZ)

try:
    AEMET_KEY = st.secrets["AEMET_API_KEY"]
except Exception:
    AEMET_KEY = ""

DIAS_ES = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# ══════════════════════════════════════════════════════════════════════
#  ESTILOS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;700;900&family=Barlow:wght@400;600;700&display=swap');

* { box-sizing: border-box; }

.stApp {
    background-color: #F5F6FA;
    font-family: 'Barlow', sans-serif;
    color: #1E3A8A;
}

footer, #MainMenu, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 3rem; max-width: 1400px; }

.banner {
    background: linear-gradient(135deg, #7F1D1D 0%, #991B1B 45%, #1E3A8A 100%);
    color: white; text-align: center;
    padding: 26px 20px 22px; border-radius: 16px;
    margin-bottom: 28px;
    box-shadow: 0 8px 32px rgba(153,27,27,0.35);
    position: relative; overflow: hidden;
}
.banner::before {
    content: ''; position: absolute; inset: 0;
    background: repeating-linear-gradient(
        45deg, transparent, transparent 20px,
        rgba(255,255,255,0.03) 20px, rgba(255,255,255,0.03) 40px
    );
}
.banner-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.1rem; font-weight: 900;
    letter-spacing: 6px; text-transform: uppercase;
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    display: block; position: relative;
}
.banner-sub {
    font-size: 0.82rem; font-weight: 600;
    letter-spacing: 3px; opacity: 0.85;
    display: block; margin-top: 4px; position: relative;
}

.sec-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.78rem; font-weight: 900;
    text-transform: uppercase; letter-spacing: 3px;
    color: #1E3A8A; border-left: 4px solid #991B1B;
    padding-left: 10px; display: block; margin: 24px 0 16px;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 14px; margin-bottom: 8px;
}
.mbox {
    background: #FFFFFF; border: 1px solid #E2E8F0;
    border-bottom: 4px solid #991B1B; border-radius: 14px;
    padding: 20px 14px 16px; text-align: center;
    box-shadow: 0 2px 8px rgba(30,58,138,0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.mbox:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(30,58,138,0.12); }
.micon { font-size: 1.7rem; display: block; margin-bottom: 6px; }
.mlabel {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.12em;
    color: #64748B; display: block; margin-bottom: 6px;
}
.mval {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.0rem; font-weight: 900;
    color: #1E3A8A; line-height: 1.1; display: block;
}
.mval-sm { font-size: 1.2rem; }
.msub { font-size: 0.78rem; font-weight: 700; color: #991B1B; display: block; margin-top: 3px; }
.msub2 { font-size: 0.72rem; font-weight: 600; color: #64748B; display: block; margin-top: 2px; }

.scroll-sec {
    background: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 14px; padding: 18px 16px; margin-bottom: 8px;
    box-shadow: 0 2px 8px rgba(30,58,138,0.05);
}
.scroll-outer {
    display: flex; overflow-x: auto; gap: 10px;
    padding: 4px 2px 10px;
    scrollbar-width: thin; scrollbar-color: #991B1B #F1F5F9;
}
.scroll-outer::-webkit-scrollbar { height: 5px; }
.scroll-outer::-webkit-scrollbar-track { background: #F1F5F9; border-radius: 10px; }
.scroll-outer::-webkit-scrollbar-thumb { background: #991B1B; border-radius: 10px; }

.hcard {
    flex: 0 0 auto; width: 136px;
    background: #F8FAFC; border: 1px solid #E2E8F0;
    border-top: 4px solid #1E3A8A; border-radius: 10px;
    padding: 11px 9px; text-align: center;
    font-size: 0.78rem; color: #1E3A8A;
    transition: border-top-color 0.2s;
}
.hcard:hover { border-top-color: #991B1B; }
.htime {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.05rem; font-weight: 900;
    color: #991B1B; margin-bottom: 8px; display: block;
}
.hrow { padding: 2px 0; color: #1E3A8A; font-weight: 600; }
.hrow b { color: #991B1B; }
.hrow-sub { padding: 1px 0; color: #64748B; font-size: 0.7rem; }

.sembox {
    border-radius: 16px; padding: 32px 24px;
    text-align: center; margin: 8px 0 16px;
    border: 2px solid transparent;
}
.sem-verde    { background: #F0FDF4; border-color: #10B981; }
.sem-amarillo { background: #FFFBEB; border-color: #F59E0B; }
.sem-rojo     { background: #FEF2F2; border-color: #EF4444; }

.sem-luz {
    width: 76px; height: 76px; border-radius: 50%;
    margin: 0 auto 16px; position: relative;
}
.sem-luz::after {
    content: ''; position: absolute; inset: -6px;
    border-radius: 50%; opacity: 0.35;
    animation: pulse 2s infinite;
}
.sem-luz-verde    { background: #10B981; }
.sem-luz-verde::after    { background: #10B981; }
.sem-luz-amarillo { background: #F59E0B; }
.sem-luz-amarillo::after { background: #F59E0B; }
.sem-luz-rojo     { background: #EF4444; }
.sem-luz-rojo::after     { background: #EF4444; }

@keyframes pulse {
    0%   { transform: scale(1);   opacity: 0.4; }
    50%  { transform: scale(1.3); opacity: 0.1; }
    100% { transform: scale(1);   opacity: 0.4; }
}

.sem-titulo {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.7rem; font-weight: 900;
    letter-spacing: 2px; margin-bottom: 6px; display: block;
}
.sem-sub { font-size: 0.9rem; font-weight: 700; margin-bottom: 10px; color: #374151; display: block; }
.sem-razones { font-size: 0.84rem; color: #374151; line-height: 1.7; }
.sem-verde .sem-titulo    { color: #065F46; }
.sem-amarillo .sem-titulo { color: #92400E; }
.sem-rojo .sem-titulo     { color: #991B1B; }

.alerta {
    background: #1E3A8A; color: white;
    padding: 14px 18px; border-radius: 10px;
    border-left: 7px solid #991B1B;
    margin: 6px 0; font-weight: 700;
    font-size: 0.88rem; line-height: 1.5;
}
.alerta-warn { background: #7F1D1D; }
.alerta-info { background: #1E3A8A; border-left-color: #60A5FA; }
.alerta small { font-weight: 400; opacity: 0.85; }

.pie {
    text-align: center; color: #94A3B8;
    font-size: 0.7rem; margin-top: 30px;
    padding-top: 14px; border-top: 1px solid #E2E8F0;
    line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════════════
def deg_to_compass(deg):
    if deg is None or (isinstance(deg, float) and math.isnan(deg)):
        return "—"
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSO","SO","OSO","O","ONO","NO","NNO"]
    return dirs[round(float(deg) / 22.5) % 16]

def dir_arrow(deg):
    if deg is None or (isinstance(deg, float) and math.isnan(deg)):
        return ""
    arrows = ["↓","↙","←","↖","↑","↗","→","↘"]
    return arrows[round(float(deg) / 45) % 8]

def safe(val, dec=1, default="—"):
    try:
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return default
        return f"{float(val):.{dec}f}"
    except Exception:
        return default

def tide_info(dt):
    """
    Modelo armónico M2 calibrado para Mutriku/Bilbao.
    Amplitud M2: 1.76 m · Periodo: 44714 s · Fase empírica Gipuzkoa.
    Precisión: ±30 min. Para datos exactos: Puertos del Estado.
    """
    t      = dt.timestamp()
    AMP    = 1.76
    PERIOD = 44714.0
    PHASE  = 5.4

    h      = AMP * math.cos(2 * math.pi * t / PERIOD - PHASE)
    h_next = AMP * math.cos(2 * math.pi * (t + 1800) / PERIOD - PHASE)
    rising = h_next > h
    height = round(h + AMP + 0.3, 2)

    if h > AMP * 0.80:   label, emoji = "PLEAMAR",  "🌊"
    elif h < -AMP * 0.80: label, emoji = "BAJAMAR",  "🏖️"
    elif rising:           label, emoji = "SUBIENDO", "↗️"
    else:                  label, emoji = "BAJANDO",  "↘️"

    return height, label, emoji, rising

def fish_score(wind_kmh, wave_m, rising, temp, pressure):
    """Heurística de actividad pesquera (0–10) para el Cantábrico."""
    s = 0
    def ok(v): return v is not None and not (isinstance(v, float) and math.isnan(v))

    if ok(wind_kmh):
        if wind_kmh < 12:  s += 2
        elif wind_kmh < 22: s += 1
    if ok(wave_m):
        if wave_m < 0.7:   s += 2
        elif wave_m < 1.3: s += 1
    if rising: s += 2
    if ok(temp):
        if 14 <= temp <= 20: s += 2
        elif 11 <= temp <= 23: s += 1
    if ok(pressure):
        if pressure > 1015: s += 2
        elif pressure > 1005: s += 1

    return min(s, 10)

def score_ui(s):
    if s >= 8: return "⭐⭐⭐⭐", "EXCELENTE", "#065F46"
    if s >= 6: return "⭐⭐⭐",   "BUENA",     "#1D4ED8"
    if s >= 4: return "⭐⭐",     "MODERADA",  "#92400E"
    return            "⭐",       "ESCASA",    "#991B1B"

def semaforo(v_racha, ola, presion, alerts):
    nivel   = "verde"
    razones = []
    def ok(v): return v is not None and not (isinstance(v, float) and math.isnan(v))

    for a in alerts:
        sev = a.get("severity", "")
        if sev in ("Extreme", "Severe"):
            nivel = "rojo"
            razones.append(f"🚨 AEMET [{sev.upper()}]: {a.get('event','—')}")
        elif sev == "Moderate" and nivel != "rojo":
            nivel = "amarillo"
            razones.append(f"⚠️ AEMET [MODERADO]: {a.get('event','—')}")

    if ok(v_racha):
        if v_racha > 55 and nivel != "rojo":
            nivel = "rojo";    razones.append(f"Racha extrema: {v_racha:.0f} km/h")
        elif v_racha > 35 and nivel == "verde":
            nivel = "amarillo"; razones.append(f"Racha fuerte: {v_racha:.0f} km/h")

    if ok(ola):
        if ola > 2.5 and nivel != "rojo":
            nivel = "rojo";    razones.append(f"Oleaje peligroso: {ola:.1f} m")
        elif ola > 1.5 and nivel == "verde":
            nivel = "amarillo"; razones.append(f"Oleaje elevado: {ola:.1f} m")

    if ok(presion) and presion < 995 and nivel == "verde":
        nivel = "amarillo"; razones.append(f"Presión muy baja: {presion:.0f} hPa")

    if not razones:
        razones = ["✅ Sin alertas activas — condiciones favorables"]

    return nivel, razones


# ══════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=600)
def fetch_meteo():
    errors = []
    url_w = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl"
        f"&wind_speed_unit=kmh&timezone=Europe%2FMadrid&forecast_days=2"
    )
    url_m = (
        f"https://marine-api.open-meteo.com/v1/marine"
        f"?latitude={LAT}&longitude={LON}"
        f"&hourly=wave_height,wave_period,wave_direction,"
        f"ocean_current_velocity,ocean_current_direction,sea_surface_temperature"
        f"&timezone=Europe%2FMadrid&forecast_days=2"
    )

    try:
        rw = requests.get(url_w, timeout=9); rw.raise_for_status(); dw = rw.json()
    except requests.exceptions.Timeout:
        errors.append("⏱️ Timeout al obtener datos de viento."); return pd.DataFrame(), errors
    except requests.exceptions.HTTPError as e:
        errors.append(f"⛔ Error HTTP (viento): {e}"); return pd.DataFrame(), errors
    except Exception as e:
        errors.append(f"⛔ Error inesperado (viento): {e}"); return pd.DataFrame(), errors

    try:
        rm = requests.get(url_m, timeout=9); rm.raise_for_status(); dm = rm.json()
    except requests.exceptions.Timeout:
        errors.append("⏱️ Timeout al obtener datos marinos."); return pd.DataFrame(), errors
    except requests.exceptions.HTTPError as e:
        errors.append(f"⛔ Error HTTP (marino): {e}"); return pd.DataFrame(), errors
    except Exception as e:
        errors.append(f"⛔ Error inesperado (marino): {e}"); return pd.DataFrame(), errors

    try:
        df = pd.DataFrame({
            'time':     pd.to_datetime(dw['hourly']['time']),
            'v_media':  dw['hourly']['wind_speed_10m'],
            'v_racha':  dw['hourly']['wind_gusts_10m'],
            'v_dir':    dw['hourly']['wind_direction_10m'],
            'presion':  dw['hourly']['pressure_msl'],
            'ola':      dm['hourly']['wave_height'],
            'ola_per':  dm['hourly']['wave_period'],
            'ola_dir':  dm['hourly']['wave_direction'],
            'corr_vel': dm['hourly']['ocean_current_velocity'],
            'corr_dir': dm['hourly']['ocean_current_direction'],
            'temp':     dm['hourly']['sea_surface_temperature'],
        })
        try:
            df['time'] = df['time'].dt.tz_localize(
                'Europe/Madrid', ambiguous='infer', nonexistent='shift_forward'
            )
        except Exception:
            df['time'] = df['time'].dt.tz_localize('UTC').dt.tz_convert('Europe/Madrid')
        return df, errors
    except Exception as e:
        errors.append(f"⛔ Error construyendo DataFrame: {e}")
        return pd.DataFrame(), errors


@st.cache_data(ttl=3600)
def fetch_aemet(api_key):
    if not api_key:
        return [], None
    try:
        headers = {"api_key": api_key, "Accept": "application/json"}
        r = requests.get(
            "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/61",
            headers=headers, timeout=10
        )
        r.raise_for_status()
        meta = r.json()
        if meta.get("estado") != 200:
            return [], f"AEMET: {meta.get('descripcion','error desconocido')}"

        r2 = requests.get(meta["datos"], headers=headers, timeout=12)
        r2.raise_for_status()

        root = ET.fromstring(r2.text)
        ns   = {'c': 'urn:oasis:names:tc:emergency:cap:1.2'}
        alerts = []
        for info in root.findall('.//c:info', ns):
            lang = info.findtext('c:language', '', ns)
            if lang and not lang.lower().startswith('es'):
                continue
            alerts.append({
                'event':    info.findtext('c:event',    '—', ns),
                'severity': info.findtext('c:severity', '—', ns),
                'urgency':  info.findtext('c:urgency',  '—', ns),
                'headline': info.findtext('c:headline', '—', ns),
                'expires':  info.findtext('c:expires',  '—', ns),
            })
        return alerts, None

    except requests.exceptions.HTTPError as e:
        return [], f"AEMET HTTP {e.response.status_code} — comprueba tu API key"
    except ET.ParseError:
        return [], "AEMET: error al parsear XML CAP"
    except Exception as e:
        return [], f"AEMET no disponible: {e}"


# ══════════════════════════════════════════════════════════════════════
#  BANNER
# ══════════════════════════════════════════════════════════════════════
fecha_str = f"{DIAS_ES[ahora.weekday()]}, {ahora.day} de {MESES_ES[ahora.month-1]} de {ahora.year}"
st.markdown(f"""
<div class='banner'>
    <span class='banner-title'>🔱 TXOMIN — CONTROL TÁCTICO MUTRIKU</span>
    <span class='banner-sub'>{fecha_str} &nbsp;·&nbsp; {ahora.strftime('%H:%M')}</span>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  CARGA Y VALIDACIÓN
# ══════════════════════════════════════════════════════════════════════
with st.spinner("Sincronizando datos meteorológicos y marinos…"):
    df, data_errors = fetch_meteo()
    aemet_alerts, aemet_error = fetch_aemet(AEMET_KEY)

for e in data_errors:
    st.error(e)

if df.empty:
    st.error("📡 Sin datos disponibles. Comprueba la conexión e intenta de nuevo.")
    st.stop()

df['_diff'] = (df['time'] - ahora).abs()
idx = df['_diff'].idxmin()
now = df.loc[idx]
df.drop(columns=['_diff'], inplace=True)

def fv(v):
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except Exception:
        return None

v_media  = fv(now['v_media'])
v_racha  = fv(now['v_racha'])
v_dir    = fv(now['v_dir'])
presion  = fv(now['presion'])
ola      = fv(now['ola'])
ola_dir  = fv(now['ola_dir'])
corr_vel = fv(now['corr_vel'])
corr_dir = fv(now['corr_dir'])
temp     = fv(now['temp'])

tide_h, tide_label, tide_emoji, tide_rising = tide_info(ahora)
score = fish_score(v_media, ola, tide_rising, temp, presion)
stars, act_label, act_color = score_ui(score)
ola_max  = round(ola * 1.8, 1) if ola else None
corr_kmh = round(corr_vel * 3.6, 1) if corr_vel is not None else None


# ══════════════════════════════════════════════════════════════════════
#  ESTADO ACTUAL
# ══════════════════════════════════════════════════════════════════════
st.markdown("<span class='sec-title'>📡 ESTADO ACTUAL DE LA MAR</span>", unsafe_allow_html=True)

st.markdown(f"""
<div class='metric-grid'>
    <div class='mbox'>
        <div class='micon'>🌬️</div>
        <span class='mlabel'>Viento</span>
        <span class='mval'>{safe(v_media,0)}<span class='mval-sm'> / {safe(v_racha,0)}</span></span>
        <span class='msub'>Media / Racha &nbsp; km/h</span>
        <span class='msub2'>{dir_arrow(v_dir)} {deg_to_compass(v_dir)}</span>
    </div>
    <div class='mbox'>
        <div class='micon'>🌊</div>
        <span class='mlabel'>Oleaje</span>
        <span class='mval'>{safe(ola)}<span class='mval-sm'> m</span></span>
        <span class='msub'>Significativa</span>
        <span class='msub2'>Máx est. {safe(ola_max)} m &nbsp;·&nbsp; {deg_to_compass(ola_dir)}</span>
    </div>
    <div class='mbox'>
        <div class='micon'>🌀</div>
        <span class='mlabel'>Corriente</span>
        <span class='mval'>{safe(corr_kmh)}<span class='mval-sm'> km/h</span></span>
        <span class='msub'>{dir_arrow(corr_dir)} {deg_to_compass(corr_dir)}</span>
        <span class='msub2'>({safe(corr_vel, 2)} m/s)</span>
    </div>
    <div class='mbox'>
        <div class='micon'>{tide_emoji}</div>
        <span class='mlabel'>Marea</span>
        <span class='mval'>{tide_h}<span class='mval-sm'> m</span></span>
        <span class='msub'>{tide_label}</span>
        <span class='msub2'>Modelo M2 (±30 min)</span>
    </div>
    <div class='mbox'>
        <div class='micon'>🌡️</div>
        <span class='mlabel'>Agua / Presión</span>
        <span class='mval'>{safe(temp)}°<span class='mval-sm'>C</span></span>
        <span class='msub'>{safe(presion, 0)} hPa</span>
        <span class='msub2'>Temperatura superficial</span>
    </div>
    <div class='mbox'>
        <div class='micon'>🐟</div>
        <span class='mlabel'>Actividad Peces</span>
        <span class='mval' style='font-size:1.3rem; line-height:1.4'>{stars}</span>
        <span class='msub' style='color:{act_color}'>{act_label}</span>
        <span class='msub2'>Puntuación: {score}/10</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  PREVISIÓN CADA 2 HORAS HASTA LAS 00:00
# ══════════════════════════════════════════════════════════════════════
st.markdown("<span class='sec-title'>⏱️ PREVISIÓN TÁCTICA — CADA 2 HORAS (hasta las 00:00)</span>",
            unsafe_allow_html=True)

medianoche = ahora.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
future     = df[(df['time'] > ahora) & (df['time'] <= medianoche)].copy()
horas_scroll = future.iloc[::2]

if horas_scroll.empty:
    st.info("No hay datos de previsión para el resto del día.")
else:
    scroll_html = "<div class='scroll-sec'><div class='scroll-outer'>"
    for _, r in horas_scroll.iterrows():
        _, t_lbl, t_em, _ = tide_info(r['time'])
        rv     = fv(r['v_media'])
        rvc    = fv(r['v_racha'])
        ro     = fv(r['ola'])
        rc     = fv(r['corr_vel'])
        rc_kmh = round(rc * 3.6, 1) if rc is not None else None
        rt     = fv(r['temp'])
        rd     = fv(r['v_dir'])

        scroll_html += f"""
        <div class='hcard'>
            <span class='htime'>{r['time'].strftime('%H:%M')}</span>
            <div class='hrow'>🌬️ <b>{safe(rv,0)}/{safe(rvc,0)}</b> km/h</div>
            <div class='hrow-sub'>{dir_arrow(rd)} {deg_to_compass(rd)}</div>
            <div class='hrow'>🌊 <b>{safe(ro)} m</b></div>
            <div class='hrow'>🌀 <b>{safe(rc_kmh)} km/h</b></div>
            <div class='hrow'>{t_em} <b>{t_lbl}</b></div>
            <div class='hrow'>🌡️ <b>{safe(rt)}°C</b></div>
        </div>
        """
    st.markdown(scroll_html + "</div></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  SEMÁFORO DE SEGURIDAD
# ══════════════════════════════════════════════════════════════════════
st.markdown("<span class='sec-title'>🚦 SEMÁFORO DE SEGURIDAD MARÍTIMA</span>", unsafe_allow_html=True)

nivel, razones = semaforo(v_racha, ola, presion, aemet_alerts)

SEM = {
    "verde":    {"box":"sem-verde",    "luz":"sem-luz-verde",
                 "titulo":"✅ RECOMENDABLE",    "sub":"CONDICIONES FAVORABLES"},
    "amarillo": {"box":"sem-amarillo", "luz":"sem-luz-amarillo",
                 "titulo":"⚠️ PRECAUCIÓN",      "sub":"SALIR CON PRECAUCIÓN Y EQUIPO COMPLETO"},
    "rojo":     {"box":"sem-rojo",     "luz":"sem-luz-rojo",
                 "titulo":"🚫 NO RECOMENDABLE", "sub":"CONDICIONES ADVERSAS — NO SALIR"},
}
s = SEM[nivel]
razones_html = "".join(f"<div>• {r}</div>" for r in razones)

st.markdown(f"""
<div class='sembox {s["box"]}'>
    <div class='sem-luz {s["luz"]}'></div>
    <span class='sem-titulo'>{s["titulo"]}</span>
    <span class='sem-sub'>{s["sub"]}</span>
    <div class='sem-razones'>{razones_html}</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  ALERTAS AEMET
# ══════════════════════════════════════════════════════════════════════
if aemet_alerts:
    st.markdown("<span class='sec-title'>🚨 AVISOS METEOROLÓGICOS AEMET ACTIVOS</span>",
                unsafe_allow_html=True)
    for a in aemet_alerts:
        sev = a.get("severity","—")
        cls = "alerta-warn" if sev in ("Extreme","Severe") else "alerta-info"
        st.markdown(f"""
        <div class='alerta {cls}'>
            🔔 <b>[{sev.upper()}]</b> {a.get('event','—')} — {a.get('headline','—')}<br>
            <small>⏱️ Válido hasta: {a.get('expires','—')}</small>
        </div>
        """, unsafe_allow_html=True)
elif aemet_error:
    st.markdown(f"<div class='alerta alerta-info'>ℹ️ {aemet_error}</div>",
                unsafe_allow_html=True)

if not AEMET_KEY:
    st.markdown("""
    <div class='alerta alerta-info' style='margin-top:14px;'>
        ℹ️ <b>Alertas AEMET no activadas.</b>
        Solicita tu clave gratis en
        <a href='https://opendata.aemet.es/centrodedescargas/inicio'
           style='color:#93C5FD' target='_blank'>opendata.aemet.es</a>
        y añádela en <code>.streamlit/secrets.toml</code>:<br>
        <code>AEMET_API_KEY = "tu_clave_aqui"</code>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  PIE DE PÁGINA
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class='pie'>
    🔱 TXOMIN v2.0 &nbsp;·&nbsp;
    Datos: <b>Open-Meteo</b> (viento · oleaje · corriente) &nbsp;·&nbsp;
    <b>AEMET OpenData</b> (alertas oficiales) &nbsp;·&nbsp;
    <b>Modelo M2</b> (marea estimada ±30 min)<br>
    Última actualización: {ahora.strftime('%H:%M')} &nbsp;·&nbsp;
    Refresco automático cada 10 minutos
</div>
""", unsafe_allow_html=True)
