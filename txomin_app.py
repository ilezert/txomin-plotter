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
    if s >= 6: return "⭐⭐⭐",
