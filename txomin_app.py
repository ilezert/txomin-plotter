import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import math
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ══════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN GLOBAL
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Txomin v3 | Mutriku",
    page_icon="🔱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LAT, LON = 43.315, -2.38
TZ       = ZoneInfo("Europe/Madrid")
ahora    = datetime.now(TZ)

try:    AEMET_KEY      = st.secrets["AEMET_API_KEY"]
except: AEMET_KEY      = ""
try:    ANTHROPIC_KEY  = st.secrets["ANTHROPIC_API_KEY"]
except: ANTHROPIC_KEY  = ""

DIAS_ES  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# ══════════════════════════════════════════════════════════════════════
#  DISEÑO — TEMA MARINO OSCURO (v3)
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root {
  --bg:        #F0F4F8;
  --bg2:       #E8EEF4;
  --bg3:       #DDE5EE;
  --card:      #FFFFFF;
  --card2:     #F8FAFC;
  --border:    rgba(30,58,138,0.10);
  --border2:   rgba(30,58,138,0.22);
  --navy:      #1E3A8A;
  --navy2:     #1D4ED8;
  --cyan:      #0284C7;
  --cyan2:     #0369A1;
  --amber:     #B45309;
  --red:       #DC2626;
  --green:     #059669;
  --violet:    #6D28D9;
  --text:      #0F172A;
  --text2:     #475569;
  --text3:     #94A3B8;
  --shadow:    0 2px 12px rgba(30,58,138,0.08);
  --shadow-lg: 0 8px 32px rgba(30,58,138,0.12);
}

* { box-sizing: border-box; }

.stApp {
  background: var(--bg) !important;
  font-family: 'Manrope', sans-serif;
  color: var(--text);
}

footer, #MainMenu, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 4rem; max-width: 1400px; }

/* ─── SCROLLBAR ─────────────────────────────────────────── */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background: var(--bg2); border-radius:10px; }
::-webkit-scrollbar-thumb { background: var(--navy2); border-radius:10px; }

/* ─── TABS ──────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--navy);
  border-radius: 12px 12px 0 0;
  padding: 6px 10px 0;
  gap: 4px;
  border-bottom: none;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Manrope', sans-serif;
  font-weight: 700; font-size: 0.78rem;
  letter-spacing: 1.2px; text-transform: uppercase;
  color: rgba(255,255,255,0.55) !important;
  border-radius: 8px 8px 0 0;
  padding: 10px 18px;
  transition: all 0.2s;
}
.stTabs [data-baseweb="tab"]:hover { color: rgba(255,255,255,0.9) !important; }
.stTabs [aria-selected="true"] {
  background: #FFFFFF !important;
  color: var(--navy) !important;
  font-weight: 800 !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: transparent;
  border: 1px solid var(--border2);
  border-top: 3px solid var(--navy);
  border-radius: 0 0 12px 12px;
  padding: 0;
}

/* ─── BANNER ────────────────────────────────────────────── */
.banner {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 50%, #1E40AF 100%);
  border-radius: 16px;
  padding: 30px 24px 24px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(30,58,138,0.35);
}
.banner::before {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse 70% 90% at 50% -10%, rgba(255,255,255,0.12) 0%, transparent 60%),
    repeating-linear-gradient(90deg, transparent, transparent 40px,
      rgba(255,255,255,0.02) 40px, rgba(255,255,255,0.02) 41px);
  pointer-events: none;
}
.banner-trident {
  font-size: 2.6rem; display: block;
  margin-bottom: 8px; position: relative;
  filter: drop-shadow(0 2px 8px rgba(0,0,0,0.25));
  animation: float 4s ease-in-out infinite;
}
@keyframes float {
  0%,100% { transform: translateY(0); }
  50%      { transform: translateY(-5px); }
}
.banner-title {
  font-family: 'Syne', sans-serif;
  font-size: 1.9rem; font-weight: 800;
  letter-spacing: 5px; text-transform: uppercase;
  color: #FFFFFF;
  text-shadow: 0 2px 12px rgba(0,0,0,0.2);
  display: block; position: relative; text-align: center;
}
.banner-sub {
  font-size: 0.74rem; font-weight: 600;
  letter-spacing: 2.5px; color: rgba(255,255,255,0.65);
  display: block; margin-top: 6px; text-align: center; position: relative;
}

/* ─── SECTION TITLE ─────────────────────────────────────── */
.sec-title {
  font-family: 'Manrope', sans-serif;
  font-size: 0.66rem; font-weight: 800;
  text-transform: uppercase; letter-spacing: 3px;
  color: var(--navy);
  border-left: 3px solid var(--red);
  padding-left: 10px;
  display: block; margin: 28px 0 14px;
}

/* ─── METRIC CARDS ──────────────────────────────────────── */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px; margin-bottom: 8px;
}
.mbox {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 14px 16px;
  text-align: center;
  position: relative; overflow: hidden;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s;
}
.mbox::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--navy), var(--navy2));
}
.mbox:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}
.micon  { font-size: 1.6rem; display: block; margin-bottom: 8px; }
.mlabel {
  font-size: 0.60rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 1.5px;
  color: var(--text3); display: block; margin-bottom: 8px;
}
.mval {
  font-family: 'Syne', sans-serif;
  font-size: 1.8rem; font-weight: 700;
  color: var(--navy); line-height: 1.1; display: block;
}
.mval-sm { font-size: 1.1rem; color: var(--text2); }
.msub  { font-size: 0.72rem; font-weight: 600; color: var(--red); display: block; margin-top: 5px; }
.msub2 { font-size: 0.66rem; color: var(--text3); display: block; margin-top: 3px; }

/* ─── SPECIES BOX (Tab 1) ───────────────────────────────── */
.species-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(148px, 1fr));
  gap: 10px; margin-top: 4px;
}
.sbox {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 10px;
  text-align: center;
  position: relative; overflow: hidden;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s;
}
.sbox-top {
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: 12px 12px 0 0;
}
.sbox:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.sbox-name  { font-size: 0.78rem; font-weight: 700; color: var(--text);  margin-bottom: 4px; }
.sbox-score { font-family:'Syne',sans-serif; font-size: 0.66rem; font-weight:700; margin-bottom:6px; }
.sbox-cond  { font-size: 0.60rem; color: var(--text2); line-height: 1.45; }

/* ─── SEMÁFORO ──────────────────────────────────────────── */
.sembox {
  border-radius: 16px; padding: 28px 24px;
  text-align: center; margin: 8px 0 16px;
  border: 1px solid; position: relative; overflow: hidden;
  box-shadow: var(--shadow);
}
.sem-verde    { background: #F0FDF4; border-color: rgba(5,150,105,0.35); }
.sem-amarillo { background: #FFFBEB; border-color: rgba(180,83,9,0.35); }
.sem-rojo     { background: #FEF2F2; border-color: rgba(220,38,38,0.35); }
.sem-luz {
  width: 68px; height: 68px; border-radius: 50%;
  margin: 0 auto 14px; position: relative;
}
.sem-luz::after {
  content: ''; position: absolute; inset: -8px;
  border-radius: 50%; animation: pulse 2s infinite;
}
.sem-luz-verde    { background: #10B981; box-shadow: 0 0 20px rgba(16,185,129,0.45); }
.sem-luz-verde::after    { background: rgba(16,185,129,0.25); }
.sem-luz-amarillo { background: #F59E0B; box-shadow: 0 0 20px rgba(245,158,11,0.45); }
.sem-luz-amarillo::after { background: rgba(245,158,11,0.25); }
.sem-luz-rojo     { background: #EF4444; box-shadow: 0 0 20px rgba(239,68,68,0.45); }
.sem-luz-rojo::after     { background: rgba(239,68,68,0.25); }
@keyframes pulse {
  0%   { transform: scale(1);   opacity: 0.5; }
  50%  { transform: scale(1.5); opacity: 0; }
  100% { transform: scale(1);   opacity: 0.5; }
}
.sem-titulo {
  font-family: 'Syne', sans-serif;
  font-size: 1.4rem; font-weight: 900; letter-spacing: 2px;
  margin-bottom: 6px; display: block;
}
.sem-sub { font-size: 0.82rem; font-weight: 600; margin-bottom: 12px; color: var(--text2); display: block; }
.sem-razones { font-size: 0.80rem; color: var(--text2); line-height: 1.8; }
.sem-verde .sem-titulo    { color: #065F46; }
.sem-amarillo .sem-titulo { color: #92400E; }
.sem-rojo .sem-titulo     { color: #991B1B; }

/* ─── ALERTAS ───────────────────────────────────────────── */
.alerta {
  background: #FEF2F2; color: var(--text);
  padding: 12px 16px; border-radius: 10px;
  border-left: 4px solid var(--red); margin: 6px 0;
  font-size: 0.84rem; line-height: 1.5; font-weight: 600;
}
.alerta-warn { border-left-color: var(--red);  background: #FEF2F2; }
.alerta-info { border-left-color: var(--cyan2); background: #EFF6FF; }
.alerta small { font-weight: 400; color: var(--text2); }

/* ─── 3-DAY FORECAST ────────────────────────────────────── */
.day-section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 16px 12px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}
.day-header {
  font-family: 'Syne', sans-serif;
  font-size: 0.82rem; font-weight: 800;
  color: var(--navy); letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 14px; display: flex;
  align-items: center; gap: 10px;
}
.day-header::after {
  content: ''; flex: 1; height: 1px;
  background: linear-gradient(90deg, var(--border2), transparent);
}

/* ─── FISH TIPS ─────────────────────────────────────────── */
.fish-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px; margin-top: 4px;
}
.fish-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  position: relative; overflow: hidden;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s;
}
.fish-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
.fish-card-accent {
  position: absolute; top: 0; left: 0; right: 0; height: 4px; border-radius: 16px 16px 0 0;
}
.fish-name {
  font-family: 'Syne', sans-serif;
  font-size: 0.85rem; font-weight: 900;
  color: var(--text); margin-bottom: 2px; letter-spacing: 1px;
}
.fish-latin { font-size: 0.68rem; color: var(--text3); font-style: italic; margin-bottom: 12px; display: block; }
.fish-section-title {
  font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.5px; margin: 10px 0 5px;
  display: flex; align-items: center; gap: 6px; color: var(--navy);
}
.fish-body { font-size: 0.78rem; color: var(--text2); line-height: 1.6; }
.tackle-item {
  background: var(--bg2);
  border-radius: 8px; padding: 8px 10px;
  font-size: 0.75rem; color: var(--text2);
  margin-bottom: 6px; line-height: 1.5;
  border-left: 3px solid var(--navy2);
}
.tackle-item b { color: var(--text); }

/* ─── AI TIP BOX ────────────────────────────────────────── */
.ai-box {
  background: #EFF6FF;
  border: 1px solid rgba(30,58,138,0.2);
  border-radius: 16px; padding: 20px 22px;
  margin: 8px 0; position: relative;
}
.ai-box::before {
  content: '🤖 IA';
  position: absolute; top: -10px; left: 18px;
  background: linear-gradient(90deg, #1E3A8A, #1D4ED8);
  color: white; font-size: 0.6rem; font-weight: 900;
  letter-spacing: 2px; padding: 2px 10px; border-radius: 20px;
}
.ai-content { font-size: 0.84rem; color: var(--text); line-height: 1.75; }
.ai-content b { color: var(--navy); }
.ai-content em { color: var(--amber); font-style: normal; }

/* ─── PIE ────────────────────────────────────────────────── */
.pie {
  text-align: center; color: var(--text3);
  font-size: 0.66rem; margin-top: 32px;
  padding-top: 16px; border-top: 1px solid var(--border2);
  line-height: 1.9;
}
.pie b { color: var(--text2); }

/* ─── TIDE BOX ──────────────────────────────────────────── */
.tide-box {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: var(--shadow);
  margin-bottom: 8px;
}
.tide-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px; margin-top: 12px;
}
.tide-event {
  background: var(--bg2);
  border-radius: 10px; padding: 12px 10px;
  text-align: center; border: 1px solid var(--border);
}
.tide-event-type {
  font-size: 0.60rem; font-weight: 800; text-transform: uppercase;
  letter-spacing: 1.5px; margin-bottom: 4px; display: block;
}
.tide-event-time {
  font-family: 'Syne', sans-serif;
  font-size: 1.3rem; font-weight: 700;
  color: var(--navy); display: block; margin-bottom: 3px;
}
.tide-event-h {
  font-size: 0.78rem; font-weight: 700; color: var(--text2); display: block;
}
.coef-badge {
  display: inline-flex; align-items: center; gap: 8px;
  border-radius: 8px; padding: 8px 14px;
  margin-top: 14px; border: 1px solid currentColor;
}
.coef-num {
  font-family: 'Syne', sans-serif;
  font-size: 2rem; font-weight: 800; line-height: 1;
}
.coef-info { text-align: left; }
.coef-title { font-size: 0.62rem; font-weight: 800; text-transform: uppercase;
              letter-spacing: 1.5px; display: block; }
.coef-sub   { font-size: 0.68rem; font-weight: 600; color: var(--text2);
              display: block; margin-top: 2px; }

/* ─── SPINNER STREAMLIT ─────────────────────────────────── */
.stSpinner > div { border-top-color: var(--navy) !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════════════
def deg_to_compass(deg):
    if deg is None or (isinstance(deg, float) and math.isnan(deg)): return "—"
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSO","SO","OSO","O","ONO","NO","NNO"]
    return dirs[round(float(deg) / 22.5) % 16]

def dir_arrow(deg):
    if deg is None or (isinstance(deg, float) and math.isnan(deg)): return ""
    return ["↓","↙","←","↖","↑","↗","→","↘"][round(float(deg) / 45) % 8]

def safe(val, dec=1, default="—"):
    try:
        if val is None or (isinstance(val, float) and math.isnan(val)): return default
        return f"{float(val):.{dec}f}"
    except Exception: return default

def fv(v):
    try:
        f = float(v); return None if math.isnan(f) else f
    except Exception: return None

def tide_info(dt):
    t=dt.timestamp(); AMP=1.76; PERIOD=44714.0; PHASE=5.4
    h=AMP*math.cos(2*math.pi*t/PERIOD-PHASE)
    h_next=AMP*math.cos(2*math.pi*(t+1800)/PERIOD-PHASE)
    rising=h_next>h; height=round(h+AMP+0.3,2)
    if h>AMP*0.80:    label,emoji="PLEAMAR","🌊"
    elif h<-AMP*0.80: label,emoji="BAJAMAR","🏖️"
    elif rising:       label,emoji="SUBIENDO","↗️"
    else:              label,emoji="BAJANDO","↘️"
    return height,label,emoji,rising

def daily_tide_events(target_dt):
    """
    Calcula pleamares y bajamares de un día dado mediante modelo M2.
    Escanea cada 5 min para detectar máximos y mínimos locales.
    Devuelve (lista_eventos, coeficiente_marea).
    Coeficiente según escala atlántica: 20 (aguas muertas) → 120 (vivas equinocciales).
    """
    AMP = 1.76; PERIOD = 44714.0; PHASE = 5.4
    base = target_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    day_date = target_dt.date()
    events = []
    prev_h = prev_t = None

    for minutes in range(0, 24*60 + 11, 5):
        t  = base + timedelta(minutes=minutes)
        ts = t.timestamp()
        h  = AMP * math.cos(2 * math.pi * ts / PERIOD - PHASE)
        if prev_h is not None and minutes >= 10:
            t_bb  = base + timedelta(minutes=minutes - 10)
            h_bb  = AMP * math.cos(2 * math.pi * t_bb.timestamp() / PERIOD - PHASE)
            if h_bb < prev_h > h and prev_t.date() == day_date:
                events.append({'type':'PLEAMAR','emoji':'🌊',
                                'time':prev_t,
                                'height':round(prev_h + AMP + 0.3, 2)})
            elif h_bb > prev_h < h and prev_t.date() == day_date:
                events.append({'type':'BAJAMAR','emoji':'🏖️',
                                'time':prev_t,
                                'height':round(prev_h + AMP + 0.3, 2)})
        prev_h, prev_t = h, t

    # Coeficiente: rango del día → escala 10–120
    pl = [e['height'] for e in events if e['type'] == 'PLEAMAR']
    bj = [e['height'] for e in events if e['type'] == 'BAJAMAR']
    if pl and bj:
        rango = max(pl) - min(bj)
        # Bilbao: aguas muertas ~1.4 m → coef 20 | vivas ~3.8 m → coef 95
        coef  = int((rango - 1.4) / 2.4 * 75 + 20)
        coef  = max(10, min(120, coef))
    else:
        coef = 50

    return events, coef

def coef_label(c):
    if c >= 95: return "VIVAS EQUINOCCIALES", "#DC2626"
    if c >= 70: return "MAREAS VIVAS",        "#EA580C"
    if c >= 45: return "COEFICIENTE MEDIO",   "#CA8A04"
    return              "AGUAS MUERTAS",       "#16A34A"

def render_tide_box(target_dt, compact=False):
    """Renderiza el cuadro de mareas del día: pleamares, bajamares y coeficiente."""
    events, coef = daily_tide_events(target_dt)
    c_label, c_color = coef_label(coef)

    # Ordenar por hora
    events_sorted = sorted(events, key=lambda e: e['time'])

    events_html = ""
    for ev in events_sorted:
        is_high = ev['type'] == 'PLEAMAR'
        ev_color = "#0369A1" if is_high else "#059669"
        events_html += f"""
        <div class='tide-event'>
          <span class='tide-event-type' style='color:{ev_color}'>{ev['emoji']} {ev['type']}</span>
          <span class='tide-event-time'>{ev['time'].strftime('%H:%M')}</span>
          <span class='tide-event-h'>{ev['height']:.2f} m</span>
        </div>"""

    if not events_html:
        events_html = "<div style='color:#94A3B8;font-size:0.8rem;'>Sin datos de marea para este día</div>"

    coef_bg = f"rgba({int(c_color[1:3],16)},{int(c_color[3:5],16)},{int(c_color[5:7],16)},0.08)"

    return f"""
    <div class='tide-box'>
      <div style='display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px'>
        <div>
          <div style='font-size:0.66rem;font-weight:800;text-transform:uppercase;
                      letter-spacing:2px;color:var(--text3,#94A3B8);margin-bottom:4px'>
            🌊 MAREAS DEL DÍA — {target_dt.strftime('%A %d %B').upper()}
          </div>
          <div class='tide-grid'>{events_html}</div>
        </div>
        <div class='coef-badge' style='color:{c_color};background:{coef_bg}'>
          <span class='coef-num' style='color:{c_color}'>{coef}</span>
          <div class='coef-info'>
            <span class='coef-title' style='color:{c_color}'>{c_label}</span>
            <span class='coef-sub'>Coeficiente de marea</span>
          </div>
        </div>
      </div>
    </div>"""
    s=0
    def ok(v): return v is not None and not(isinstance(v,float) and math.isnan(v))
    if ok(wind_kmh):
        if wind_kmh<12: s+=2
        elif wind_kmh<22: s+=1
    if ok(wave_m):
        if wave_m<0.7: s+=2
        elif wave_m<1.3: s+=1
    if rising: s+=2
    if ok(temp):
        if 14<=temp<=20: s+=2
        elif 11<=temp<=23: s+=1
    if ok(pressure):
        if pressure>1015: s+=2
        elif pressure>1005: s+=1
    return min(s,10)

def score_ui(s):
    if s>=8: return "⭐⭐⭐⭐","EXCELENTE","#10B981"
    if s>=6: return "⭐⭐⭐","BUENA","#38BDF8"
    if s>=4: return "⭐⭐","MODERADA","#FBBF24"
    return "⭐","ESCASA","#F43F5E"

def semaforo(v_racha,ola,presion,alerts):
    nivel="verde"; razones=[]
    def ok(v): return v is not None and not(isinstance(v,float) and math.isnan(v))
    for a in alerts:
        sev=a.get("severity","")
        if sev in("Extreme","Severe"):
            nivel="rojo"; razones.append(f"🚨 AEMET [{sev.upper()}]: {a.get('event','—')}")
        elif sev=="Moderate" and nivel!="rojo":
            nivel="amarillo"; razones.append(f"⚠️ AEMET [MODERADO]: {a.get('event','—')}")
    if ok(v_racha):
        if v_racha>55 and nivel!="rojo": nivel="rojo"; razones.append(f"Racha extrema: {v_racha:.0f} km/h")
        elif v_racha>35 and nivel=="verde": nivel="amarillo"; razones.append(f"Racha fuerte: {v_racha:.0f} km/h")
    if ok(ola):
        if ola>2.5 and nivel!="rojo": nivel="rojo"; razones.append(f"Oleaje peligroso: {ola:.1f} m")
        elif ola>1.5 and nivel=="verde": nivel="amarillo"; razones.append(f"Oleaje elevado: {ola:.1f} m")
    if ok(presion) and presion<995 and nivel=="verde":
        nivel="amarillo"; razones.append(f"Presión muy baja: {presion:.0f} hPa")
    if not razones: razones=["✅ Sin alertas activas — condiciones favorables"]
    return nivel,razones


# ── SCORING POR ESPECIE ──────────────────────────────────────────────
def species_scores(wind_kmh, wave_m, rising, temp, pressure, hora):
    """Evalúa condiciones actuales para cada especie del Cantábrico."""
    def ok(v): return v is not None and not(isinstance(v,float) and math.isnan(v))
    results = []

    # ── 1. TXITXARRO (Jurel) ──
    s=0; r=[]
    if ok(wind_kmh):
        if wind_kmh<20: s+=2; r.append("viento suave ✓")
        elif wind_kmh<30: s+=1
    if ok(wave_m):
        if wave_m<1.2: s+=2; r.append("mar aceptable ✓")
        elif wave_m<1.8: s+=1
    if ok(temp) and 14<=temp<=22: s+=2; r.append("temperatura óptima ✓")
    if rising: s+=1; r.append("marea entrante ✓")
    if 6<=hora<=10 or 18<=hora<=22: s+=2; r.append("hora pico alba/ocaso ✓")
    results.append(("Txitxarro","🐟",min(s,9),", ".join(r) if r else "condiciones regulares","#38BDF8"))

    # ── 2. TXIPIRON (Calamar) ──
    s=0; r=[]
    if ok(wind_kmh) and wind_kmh<15: s+=3; r.append("mar en calma ✓")
    elif ok(wind_kmh) and wind_kmh<22: s+=1
    if ok(wave_m) and wave_m<0.8: s+=3; r.append("oleaje mínimo ✓")
    elif ok(wave_m) and wave_m<1.2: s+=1
    if hora>=20 or hora<=5: s+=3; r.append("horario nocturno ideal ✓")
    elif 17<=hora<20: s+=1; r.append("atardecer ✓")
    if ok(temp) and temp>16: s+=1; r.append("agua cálida ✓")
    results.append(("Txipiron","🦑",min(s,9),", ".join(r) if r else "mejor de noche","#818CF8"))

    # ── 3. MUXARRA / BRECA / SARGO ──
    s=0; r=[]
    if ok(wave_m) and wave_m<1.0: s+=3; r.append("mar tranquila ✓")
    elif ok(wave_m) and wave_m<1.5: s+=1
    if ok(wind_kmh) and wind_kmh<18: s+=2; r.append("viento flojo ✓")
    if ok(temp) and 16<=temp<=24: s+=2; r.append("temperatura óptima ✓")
    if 8<=hora<=13 or 16<=hora<=20: s+=2; r.append("hora diurna ✓")
    if ok(pressure) and pressure>1012: s+=1; r.append("presión alta ✓")
    results.append(("Muxarra/Sargo","🐠",min(s,9),", ".join(r) if r else "condiciones regulares","#FBBF24"))

    # ── 4. FANECA ──
    s=0; r=[]
    if ok(wave_m):
        if wave_m<1.5: s+=2; r.append("oleaje aceptable ✓")
        elif wave_m<2.0: s+=1
    if ok(wind_kmh) and wind_kmh<25: s+=2; r.append("viento manejable ✓")
    if not rising: s+=2; r.append("marea vaciante ✓")  # Faneca prefiere vaciante
    if ok(temp) and 10<=temp<=18: s+=2; r.append("agua fresca ✓")
    if hora>=18 or hora<=8: s+=1; r.append("tarde/noche ✓")
    results.append(("Faneca","🐡",min(s,8),", ".join(r) if r else "válida todo el año","#F59E0B"))

    # ── 5. LUBINA (Sea Bass) ──
    s=0; r=[]
    if ok(wave_m) and 0.3<=wave_m<=1.5: s+=3; r.append("oleaje activo ideal ✓")
    elif ok(wave_m) and wave_m<2.0: s+=1
    if ok(wind_kmh) and 8<=wind_kmh<=22: s+=2; r.append("algo de viento ✓")
    if rising: s+=2; r.append("marea entrante ✓")
    if ok(temp) and 14<=temp<=20: s+=1; r.append("temperatura ✓")
    if 5<=hora<=9 or 19<=hora<=23: s+=2; r.append("alba/ocaso ✓")
    results.append(("Lubina","🎣",min(s,9),", ".join(r) if r else "necesita algo de marejada","#10B981"))

    # ── 6. BERDEL (Caballa) ──
    s=0; r=[]
    if ok(temp) and temp>=16: s+=3; r.append("agua cálida ✓")
    elif ok(temp) and temp>=13: s+=1
    if ok(wave_m) and wave_m<1.5: s+=2; r.append("mar aceptable ✓")
    if ok(wind_kmh) and wind_kmh<25: s+=2; r.append("viento suave ✓")
    if 6<=hora<=11 or 17<=hora<=21: s+=2; r.append("horas activas ✓")
    results.append(("Berdel","🐟",min(s,9),", ".join(r) if r else "estacional (primavera-verano)","#06B6D4"))

    # ── 7. BESUGO ──
    s=0; r=[]
    if ok(wave_m) and wave_m<1.0: s+=3; r.append("mar en calma ✓")
    elif ok(wave_m) and wave_m<1.5: s+=2
    if ok(temp) and 10<=temp<=16: s+=3; r.append("agua fría ✓")  # Besugo prefiere aguas frescas
    elif ok(temp) and temp<18: s+=1
    if not rising: s+=2; r.append("vaciante ✓")
    if ok(pressure) and pressure>1010: s+=1; r.append("alta presión ✓")
    results.append(("Besugo","🐟",min(s,9),", ".join(r) if r else "mejor en otoño-invierno","#F43F5E"))

    # ── 8. MERLUZÓN (Merluza) ──
    s=0; r=[]
    if ok(wave_m) and wave_m<1.2: s+=2; r.append("mar tranquila ✓")
    if ok(wind_kmh) and wind_kmh<20: s+=2; r.append("viento flojo ✓")
    if hora>=19 or hora<=6: s+=3; r.append("nocturno ✓")
    elif 6<=hora<=9: s+=1
    if ok(temp) and 10<=temp<=17: s+=2; r.append("aguas templadas ✓")
    results.append(("Merluzón","🐟",min(s,9),", ".join(r) if r else "mejor de noche en fondos arenosos","#A78BFA"))

    # Ordenar por puntuación desc
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:6]  # Top 6


# ══════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=600)
def fetch_meteo():
    errors=[]
    url_w=(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
           f"&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl"
           f"&wind_speed_unit=kmh&timezone=Europe%2FMadrid&forecast_days=5")
    url_m=(f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT}&longitude={LON}"
           f"&hourly=wave_height,wave_period,wave_direction,"
           f"ocean_current_velocity,ocean_current_direction,sea_surface_temperature"
           f"&timezone=Europe%2FMadrid&forecast_days=5")
    try:
        rw=requests.get(url_w,timeout=9); rw.raise_for_status(); dw=rw.json()
    except requests.exceptions.Timeout:
        errors.append("⏱️ Timeout al obtener datos de viento."); return pd.DataFrame(),errors
    except Exception as e:
        errors.append(f"⛔ Error (viento): {e}"); return pd.DataFrame(),errors
    try:
        rm=requests.get(url_m,timeout=9); rm.raise_for_status(); dm=rm.json()
    except requests.exceptions.Timeout:
        errors.append("⏱️ Timeout al obtener datos marinos."); return pd.DataFrame(),errors
    except Exception as e:
        errors.append(f"⛔ Error (marino): {e}"); return pd.DataFrame(),errors
    try:
        df=pd.DataFrame({
            'time':    pd.to_datetime(dw['hourly']['time']),
            'v_media': dw['hourly']['wind_speed_10m'],
            'v_racha': dw['hourly']['wind_gusts_10m'],
            'v_dir':   dw['hourly']['wind_direction_10m'],
            'presion': dw['hourly']['pressure_msl'],
            'ola':     dm['hourly']['wave_height'],
            'ola_per': dm['hourly']['wave_period'],
            'ola_dir': dm['hourly']['wave_direction'],
            'corr_vel':dm['hourly']['ocean_current_velocity'],
            'corr_dir':dm['hourly']['ocean_current_direction'],
            'temp':    dm['hourly']['sea_surface_temperature'],
        })
        try:
            df['time']=df['time'].dt.tz_localize('Europe/Madrid',ambiguous='infer',nonexistent='shift_forward')
        except Exception:
            df['time']=df['time'].dt.tz_localize('UTC').dt.tz_convert('Europe/Madrid')
        return df,errors
    except Exception as e:
        errors.append(f"⛔ Error construyendo datos: {e}"); return pd.DataFrame(),errors


@st.cache_data(ttl=3600)
def fetch_aemet(api_key):
    if not api_key: return [],None
    try:
        headers={"api_key":api_key,"Accept":"application/json"}
        r=requests.get("https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/61",
                       headers=headers,timeout=10)
        r.raise_for_status(); meta=r.json()
        if meta.get("estado")!=200: return[],f"AEMET: {meta.get('descripcion','error')}"
        r2=requests.get(meta["datos"],headers=headers,timeout=12); r2.raise_for_status()
        root=ET.fromstring(r2.text); ns={'c':'urn:oasis:names:tc:emergency:cap:1.2'}; alerts=[]
        for info in root.findall('.//c:info',ns):
            lang=info.findtext('c:language','',ns)
            if lang and not lang.lower().startswith('es'): continue
            alerts.append({'event':info.findtext('c:event','—',ns),
                           'severity':info.findtext('c:severity','—',ns),
                           'headline':info.findtext('c:headline','—',ns),
                           'expires':info.findtext('c:expires','—',ns)})
        return alerts,None
    except requests.exceptions.HTTPError as e:
        return[],f"AEMET HTTP {e.response.status_code}"
    except ET.ParseError:
        return[],"AEMET: error XML"
    except Exception as e:
        return[],f"AEMET: {e}"


def call_anthropic(prompt, api_key, max_tokens=900):
    """Llamada al API de Anthropic para consejos de pesca IA."""
    if not api_key: return None
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514",
                  "max_tokens": max_tokens,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        return data["content"][0]["text"]
    except Exception as e:
        return f"Error IA: {e}"


# ══════════════════════════════════════════════════════════════════════
#  RENDER HELPER — TARJETA DE HORA (horizontal scroll)
# ══════════════════════════════════════════════════════════════════════
def render_hour_card(r_row, color_top="#38BDF8"):
    _,t_lbl,t_em,_ = tide_info(r_row['time'])
    rv   = fv(r_row['v_media']); rvc = fv(r_row['v_racha'])
    ro   = fv(r_row['ola']);     rc  = fv(r_row['corr_vel'])
    rc_k = round(rc*3.6,1) if rc is not None else None
    rt   = fv(r_row['temp']);    rd  = fv(r_row['v_dir'])
    hora_str = r_row['time'].strftime('%H:%M')
    fecha_str = r_row['time'].strftime('%a %d')
    return f"""
    <div style="flex:0 0 auto;width:134px;background:#FFFFFF;
                border:1px solid rgba(30,58,138,0.12);
                border-top:3px solid {color_top};border-radius:10px;
                padding:10px 8px;text-align:center;
                font-family:'Manrope',sans-serif;font-size:0.76rem;color:#0F172A;
                box-shadow:0 2px 8px rgba(30,58,138,0.07);">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:0.63rem;color:#94A3B8;margin-bottom:2px;">{fecha_str}</div>
      <div style="font-size:1.0rem;font-weight:900;color:{color_top};margin-bottom:8px;">{hora_str}</div>
      <div style="padding:2px 0;font-weight:600;color:#1E3A8A;">
        &#127783; <b style="color:{color_top};">{safe(rv,0)}/{safe(rvc,0)}</b> km/h</div>
      <div style="padding:1px 0;color:#94A3B8;font-size:0.68rem;">
        {dir_arrow(rd)} {deg_to_compass(rd)}</div>
      <div style="padding:2px 0;font-weight:600;color:#1E3A8A;">
        &#127754; <b style="color:{color_top};">{safe(ro)} m</b></div>
      <div style="padding:2px 0;font-weight:600;color:#1E3A8A;">
        &#128256; <b style="color:{color_top};">{safe(rc_k)} km/h</b></div>
      <div style="padding:2px 0;font-weight:600;color:#1E3A8A;">
        {t_em} <b style="color:{color_top};">{t_lbl}</b></div>
      <div style="padding:2px 0;font-weight:600;color:#1E3A8A;">
        &#127777; <b style="color:{color_top};">{safe(rt)}°C</b></div>
    </div>"""


# ══════════════════════════════════════════════════════════════════════
#  BANNER
# ══════════════════════════════════════════════════════════════════════
fecha_str = f"{DIAS_ES[ahora.weekday()]} {ahora.day} {MESES_ES[ahora.month-1].upper()} {ahora.year}"
st.markdown(f"""
<div class='banner'>
  <span class='banner-trident'>🔱</span>
  <span class='banner-title'>TXOMIN — MUTRIKU</span>
  <span class='banner-sub'>{fecha_str} &nbsp;·&nbsp; {ahora.strftime('%H:%M')} &nbsp;·&nbsp; CONTROL TÁCTICO MARÍTIMO v3</span>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS (una sola vez, fuera de tabs)
# ══════════════════════════════════════════════════════════════════════
with st.spinner("Sincronizando datos…"):
    df, data_errors = fetch_meteo()
    aemet_alerts, aemet_error = fetch_aemet(AEMET_KEY)

for e in data_errors: st.error(e)
if df.empty:
    st.error("📡 Sin datos. Comprueba la conexión."); st.stop()

df['_diff'] = (df['time'] - ahora).abs()
idx = df['_diff'].idxmin()
now = df.loc[idx]
df.drop(columns=['_diff'], inplace=True)

v_media  = fv(now['v_media']); v_racha = fv(now['v_racha']); v_dir   = fv(now['v_dir'])
presion  = fv(now['presion']); ola     = fv(now['ola']);      ola_dir = fv(now['ola_dir'])
corr_vel = fv(now['corr_vel']); corr_dir= fv(now['corr_dir']); temp  = fv(now['temp'])

tide_h, tide_label, tide_emoji, tide_rising = tide_info(ahora)
gen_score = fish_score_general(v_media,ola,tide_rising,temp,presion)
ola_max   = round(ola*1.8,1) if ola else None
corr_kmh  = round(corr_vel*3.6,1) if corr_vel is not None else None
nivel, razones = semaforo(v_racha,ola,presion,aemet_alerts)


# ══════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📡  ESTADO HOY",
    "🗺️  CARTA NÁUTICA",
    "📅  PREVISIÓN 3 DÍAS",
    "🐟  ESPECIES & TÉCNICAS"
])


# ════════════════════════════════════════════════════════════════════
#  TAB 1 — ESTADO DE LA MAR HOY
# ════════════════════════════════════════════════════════════════════
with tab1:

    # ── MÉTRICAS ACTUALES ───────────────────────────────────────────
    st.markdown("<span class='sec-title'>📡 CONDICIONES ACTUALES</span>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='metric-grid'>
      <div class='mbox'>
        <div class='micon'>🌬️</div>
        <span class='mlabel'>Viento</span>
        <span class='mval'>{safe(v_media,0)}<span class='mval-sm'> / {safe(v_racha,0)}</span></span>
        <span class='msub'>Media / Racha km/h</span>
        <span class='msub2'>{dir_arrow(v_dir)} {deg_to_compass(v_dir)}</span>
      </div>
      <div class='mbox'>
        <div class='micon'>🌊</div>
        <span class='mlabel'>Oleaje</span>
        <span class='mval'>{safe(ola)}<span class='mval-sm'> m</span></span>
        <span class='msub'>Significativa</span>
        <span class='msub2'>Máx ~{safe(ola_max)} m · {deg_to_compass(ola_dir)}</span>
      </div>
      <div class='mbox'>
        <div class='micon'>🌀</div>
        <span class='mlabel'>Corriente</span>
        <span class='mval'>{safe(corr_kmh)}<span class='mval-sm'> km/h</span></span>
        <span class='msub'>{dir_arrow(corr_dir)} {deg_to_compass(corr_dir)}</span>
        <span class='msub2'>{safe(corr_vel,2)} m/s</span>
      </div>
      <div class='mbox'>
        <div class='micon'>{tide_emoji}</div>
        <span class='mlabel'>Marea</span>
        <span class='mval'>{tide_h}<span class='mval-sm'> m</span></span>
        <span class='msub'>{tide_label}</span>
        <span class='msub2'>Modelo M2 ±30 min</span>
      </div>
      <div class='mbox'>
        <div class='micon'>🌡️</div>
        <span class='mlabel'>Agua / Presión</span>
        <span class='mval'>{safe(temp)}°<span class='mval-sm'>C</span></span>
        <span class='msub'>{safe(presion,0)} hPa</span>
        <span class='msub2'>Temperatura superficial</span>
      </div>
      <div class='mbox'>
        <div class='micon'>🎯</div>
        <span class='mlabel'>Condición general</span>
        <span class='mval' style='font-size:1.2rem;line-height:1.4'>{"⭐"*min(gen_score//2+1,4)}</span>
        <span class='msub'>{["MALA","ESCASA","ESCASA","MODERADA","MODERADA","BUENA","BUENA","MUY BUENA","MUY BUENA","EXCELENTE","EXCELENTE"][gen_score]}</span>
        <span class='msub2'>Puntuación: {gen_score}/10</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CUADRO DE MAREAS HOY ────────────────────────────────────────
    st.markdown("<span class='sec-title'>🌊 MAREAS HOY</span>", unsafe_allow_html=True)
    st.markdown(render_tide_box(ahora), unsafe_allow_html=True)

    # ── SCROLL 16 HORAS (8 tarjetas c/2h) ──────────────────────────
    st.markdown("<span class='sec-title'>⏱️ PRÓXIMAS 16 HORAS — CADA 2 HORAS</span>",
                unsafe_allow_html=True)

    future_16 = df[df['time'] > ahora].head(20)   # ~20 filas → tomamos cada 2
    horas_16  = future_16.iloc[::2].head(8)        # exactamente 8 tarjetas

    if horas_16.empty:
        st.info("Sin datos de previsión disponibles.")
    else:
        cards = "".join(render_hour_card(r, "#1D4ED8") for _, r in horas_16.iterrows())
        components.html(f"""
        <div style="background:#FFFFFF;border:1px solid rgba(30,58,138,0.12);
                    border-radius:12px;padding:16px;
                    box-shadow:0 2px 12px rgba(30,58,138,0.07);">
          <div style="display:flex;overflow-x:auto;gap:10px;padding-bottom:8px;
                      scrollbar-width:thin;scrollbar-color:#1D4ED8 #E8EEF4;">
            {cards}
          </div>
        </div>""", height=215, scrolling=False)

    # ── ESPECIES RECOMENDADAS HOY ───────────────────────────────────
    st.markdown("<span class='sec-title'>🐟 MEJORES ESPECIES PARA HOY</span>", unsafe_allow_html=True)
    top_species = species_scores(v_media, ola, tide_rising, temp, presion, ahora.hour)

    sp_html = "<div class='species-grid'>"
    for name, icon, score, reasons, color in top_species:
        bar = min(score/9*100, 100)
        sp_html += f"""
        <div class='sbox'>
          <div class='sbox-top' style='background:linear-gradient(90deg,{color},transparent)'></div>
          <div style='font-size:1.6rem;margin-bottom:4px'>{icon}</div>
          <div class='sbox-name'>{name}</div>
          <div style='width:100%;background:rgba(30,58,138,0.08);border-radius:4px;height:4px;margin:6px 0 4px'>
            <div style='width:{bar:.0f}%;background:{color};height:4px;border-radius:4px;
                        transition:width 1s ease'></div>
          </div>
          <div class='sbox-score' style='color:{color}'>{score}/9</div>
          <div class='sbox-cond'>{reasons}</div>
        </div>"""
    sp_html += "</div>"
    st.markdown(sp_html, unsafe_allow_html=True)

    # ── SEMÁFORO ────────────────────────────────────────────────────
    st.markdown("<span class='sec-title'>🚦 SEMÁFORO DE SEGURIDAD</span>", unsafe_allow_html=True)
    SEM = {
        "verde":    {"box":"sem-verde",    "luz":"sem-luz-verde",
                     "titulo":"✅ RECOMENDABLE",    "sub":"CONDICIONES FAVORABLES PARA SALIR"},
        "amarillo": {"box":"sem-amarillo", "luz":"sem-luz-amarillo",
                     "titulo":"⚠️ PRECAUCIÓN",      "sub":"SALIR CON PRECAUCIÓN Y EQUIPO COMPLETO"},
        "rojo":     {"box":"sem-rojo",     "luz":"sem-luz-rojo",
                     "titulo":"🚫 NO RECOMENDABLE", "sub":"CONDICIONES ADVERSAS — NO SALIR"},
    }
    s = SEM[nivel]
    razones_html = "".join(f"<div>▸ {r}</div>" for r in razones)
    st.markdown(f"""
    <div class='sembox {s["box"]}'>
      <div class='sem-luz {s["luz"]}'></div>
      <span class='sem-titulo'>{s["titulo"]}</span>
      <span class='sem-sub'>{s["sub"]}</span>
      <div class='sem-razones'>{razones_html}</div>
    </div>""", unsafe_allow_html=True)

    # ── ALERTAS AEMET ───────────────────────────────────────────────
    if aemet_alerts:
        st.markdown("<span class='sec-title'>🚨 AVISOS AEMET ACTIVOS</span>",
                    unsafe_allow_html=True)
        for a in aemet_alerts:
            sev = a.get("severity","—")
            cls = "alerta-warn" if sev in("Extreme","Severe") else "alerta-info"
            st.markdown(f"""
            <div class='alerta {cls}'>
              🔔 <b>[{sev.upper()}]</b> {a.get('event','—')} — {a.get('headline','—')}<br>
              <small>⏱️ Válido hasta: {a.get('expires','—')}</small>
            </div>""", unsafe_allow_html=True)
    elif aemet_error:
        st.markdown(f"<div class='alerta alerta-info'>ℹ️ {aemet_error}</div>",
                    unsafe_allow_html=True)
    if not AEMET_KEY:
        st.markdown("""
        <div class='alerta alerta-info'>
          ℹ️ <b>Alertas AEMET no activadas.</b>
          Solicita tu clave gratuita en
          <a href='https://opendata.aemet.es/centrodedescargas/inicio'
             style='color:#38BDF8' target='_blank'>opendata.aemet.es</a>
          y añádela en <code>.streamlit/secrets.toml</code>:
          <code>AEMET_API_KEY = "tu_clave"</code>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='pie'>
      🔱 TXOMIN v3.0 &nbsp;·&nbsp; <b>Open-Meteo</b> (viento · oleaje · corriente) &nbsp;·&nbsp;
      <b>AEMET OpenData</b> (alertas) &nbsp;·&nbsp; <b>Modelo M2</b> (marea ±30 min)<br>
      Actualizado: {ahora.strftime('%H:%M')} &nbsp;·&nbsp; Refresco: cada 10 min
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  TAB 2 — CARTA NÁUTICA (unchanged logic, updated CSS colors)
# ════════════════════════════════════════════════════════════════════
with tab2:

    CHART_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Manrope:wght@500;600;700&family=IBM+Plex+Mono:wght@500&display=swap');
  *{margin:0;padding:0;box-sizing:border-box;}
  body{background:#050E1F;font-family:'Manrope',sans-serif;}
  #toolbar{
    background:linear-gradient(90deg,#0A1628,#0D1B33);
    padding:10px 14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;
    border-bottom:2px solid rgba(56,189,248,0.3);
  }
  .tbtn{
    background:rgba(56,189,248,0.1);color:#93C5FD;
    border:1px solid rgba(56,189,248,0.25);border-radius:7px;
    padding:7px 14px;cursor:pointer;font-family:'Manrope',sans-serif;
    font-size:0.75rem;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;
    transition:all 0.18s;white-space:nowrap;
  }
  .tbtn:hover{background:rgba(244,63,94,0.2);border-color:#F43F5E;color:white;}
  .tbtn.active{background:rgba(244,63,94,0.25);border-color:#F43F5E;color:#FCA5A5;
               box-shadow:0 0 12px rgba(244,63,94,0.3);}
  #result-panel{
    background:rgba(10,22,40,0.9);color:#38BDF8;
    border:1px solid rgba(56,189,248,0.2);border-radius:7px;
    padding:6px 14px;font-size:0.75rem;font-weight:700;
    flex:1;max-width:620px;
  }
  #result-panel b{color:#FBBF24;}
  #map{height:630px;width:100%;cursor:default;}
  #legend{
    background:linear-gradient(90deg,#0A1628,#0D1B33);
    padding:9px 14px;display:flex;gap:16px;align-items:center;flex-wrap:wrap;
    font-size:0.68rem;color:#94A3B8;font-weight:700;
    border-top:1px solid rgba(56,189,248,0.2);
  }
  .leg-item{display:flex;align-items:center;gap:6px;}
  .leg-dot {width:12px;height:12px;border-radius:50%;flex-shrink:0;}
  .leg-line{width:20px;height:4px;border-radius:2px;flex-shrink:0;}
  .leg-src {margin-left:auto;color:#334155;font-size:0.62rem;}
  .mtip{background:#0D1B33!important;color:#FBBF24!important;
        border:1px solid #38BDF8!important;border-radius:4px!important;
        font-weight:900!important;font-size:0.68rem!important;padding:2px 7px!important;}
  .mtip::before{display:none!important;}
  .leaflet-popup-content-wrapper{background:#0D1B33!important;color:#E2E8F0!important;
    border:1px solid rgba(56,189,248,0.3)!important;border-radius:10px!important;
    box-shadow:0 8px 24px rgba(0,0,0,0.6)!important;}
  .leaflet-popup-tip{background:#0D1B33!important;}
  .leaflet-control-layers-expanded{background:#0D1B33!important;color:#E2E8F0!important;
    border:1px solid rgba(56,189,248,0.2)!important;border-radius:8px!important;}
  .leaflet-control-scale-line{background:rgba(10,22,40,0.9)!important;color:#38BDF8!important;
    border:1px solid rgba(56,189,248,0.3)!important;border-radius:4px!important;}

  /* ── WAYPOINT PANEL ─────────────────────────────────── */
  #wp-panel {
    position:absolute; top:0; right:0; width:280px; height:100%;
    background:#050E1F; border-left:1px solid rgba(56,189,248,0.2);
    display:flex; flex-direction:column; z-index:1000;
    transform:translateX(100%); transition:transform 0.28s ease;
    font-family:'Manrope',sans-serif;
  }
  #wp-panel.open { transform:translateX(0); }
  #wp-panel-head {
    background:linear-gradient(90deg,#0A1628,#0D1B33);
    padding:12px 14px; display:flex; align-items:center;
    justify-content:space-between; border-bottom:1px solid rgba(56,189,248,0.15);
  }
  #wp-panel-head span {
    font-size:0.72rem; font-weight:800; letter-spacing:2px;
    text-transform:uppercase; color:#38BDF8;
  }
  #wp-close {
    background:none; border:none; color:#64748B; cursor:pointer;
    font-size:1.1rem; line-height:1; padding:0;
    transition:color 0.15s;
  }
  #wp-close:hover { color:#F43F5E; }
  #wp-list {
    flex:1; overflow-y:auto; padding:10px;
    scrollbar-width:thin; scrollbar-color:#38BDF8 #0A1628;
  }
  #wp-list::-webkit-scrollbar { width:4px; }
  #wp-list::-webkit-scrollbar-thumb { background:#38BDF8; border-radius:4px; }
  .wp-item {
    background:#0D1B33; border:1px solid rgba(56,189,248,0.12);
    border-left:3px solid #38BDF8; border-radius:8px;
    padding:9px 10px; margin-bottom:8px;
    transition:border-color 0.15s;
  }
  .wp-item:hover { border-color:rgba(56,189,248,0.4); }
  .wp-item-top { display:flex; align-items:center; gap:7px; margin-bottom:3px; }
  .wp-item-icon { font-size:1rem; }
  .wp-item-name {
    font-size:0.78rem; font-weight:700; color:#E2E8F0;
    flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  }
  .wp-item-coords { font-size:0.62rem; color:#475569; font-family:'IBM Plex Mono',monospace; }
  .wp-item-note { font-size:0.68rem; color:#64748B; margin-top:4px; font-style:italic; }
  .wp-item-actions { display:flex; gap:5px; margin-top:7px; }
  .wp-btn {
    flex:1; padding:4px 0; border:none; border-radius:5px; cursor:pointer;
    font-size:0.65rem; font-weight:700; letter-spacing:0.5px; transition:all 0.15s;
  }
  .wp-btn-go  { background:rgba(56,189,248,0.15); color:#38BDF8; }
  .wp-btn-go:hover  { background:rgba(56,189,248,0.3); }
  .wp-btn-del { background:rgba(244,63,94,0.12); color:#F43F5E; }
  .wp-btn-del:hover { background:rgba(244,63,94,0.25); }
  #wp-export-btn {
    margin:10px; padding:9px; border:1px solid rgba(56,189,248,0.2);
    background:rgba(56,189,248,0.07); color:#38BDF8; border-radius:7px;
    font-size:0.7rem; font-weight:700; cursor:pointer; letter-spacing:1px;
    text-transform:uppercase; transition:all 0.15s;
  }
  #wp-export-btn:hover { background:rgba(56,189,248,0.15); }
  #wp-empty {
    text-align:center; padding:30px 16px; color:#334155;
    font-size:0.75rem; line-height:1.7;
  }

  /* ── SAVE DIALOG ────────────────────────────────────── */
  #wp-dialog {
    display:none; position:absolute; z-index:2000;
    background:#0D1B33; border:1px solid rgba(56,189,248,0.35);
    border-radius:12px; padding:16px; width:240px;
    box-shadow:0 8px 32px rgba(0,0,0,0.6);
    font-family:'Manrope',sans-serif;
  }
  #wp-dialog h4 {
    font-size:0.72rem; font-weight:800; color:#38BDF8;
    letter-spacing:1.5px; text-transform:uppercase; margin-bottom:12px;
  }
  .dlg-label { font-size:0.65rem; font-weight:700; color:#64748B;
    text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; display:block; }
  .dlg-input {
    width:100%; background:#050E1F; border:1px solid rgba(56,189,248,0.2);
    border-radius:6px; padding:7px 10px; color:#E2E8F0; font-size:0.78rem;
    margin-bottom:10px; outline:none; font-family:'Manrope',sans-serif;
    transition:border-color 0.15s;
  }
  .dlg-input:focus { border-color:#38BDF8; }
  .dlg-select {
    width:100%; background:#050E1F; border:1px solid rgba(56,189,248,0.2);
    border-radius:6px; padding:7px 10px; color:#E2E8F0; font-size:0.78rem;
    margin-bottom:10px; cursor:pointer; font-family:'Manrope',sans-serif;
  }
  .dlg-row { display:flex; gap:8px; }
  .dlg-btn {
    flex:1; padding:8px; border:none; border-radius:7px; cursor:pointer;
    font-size:0.72rem; font-weight:800; letter-spacing:0.5px; transition:all 0.15s;
  }
  .dlg-save { background:#38BDF8; color:#050E1F; }
  .dlg-save:hover { background:#7DD3FC; }
  .dlg-cancel { background:rgba(255,255,255,0.06); color:#94A3B8; }
  .dlg-cancel:hover { background:rgba(255,255,255,0.1); }
</style>
</head>
<body>
<div style="position:relative;overflow:hidden;">
<div id="toolbar">
  <button class="tbtn" id="btn-measure" onclick="setTool('measure')">&#128207; MEDIR DISTANCIA</button>
  <button class="tbtn" id="btn-bearing" onclick="setTool('bearing')">&#129517; CALCULAR DERROTA</button>
  <button class="tbtn" id="btn-wp"      onclick="setTool('waypoint')">&#128205; GUARDAR PUNTO</button>
  <button class="tbtn" onclick="clearAll()">&#128465; LIMPIAR</button>
  <div style="width:1px;height:26px;background:rgba(56,189,248,0.2);margin:0 4px;"></div>
  <div id="result-panel">Selecciona herramienta y haz clic en la carta &nbsp;·&nbsp; doble clic para finalizar</div>
  <div style="margin-left:auto;">
    <button class="tbtn" onclick="toggleWpPanel()" style="background:rgba(251,191,36,0.12);border-color:rgba(251,191,36,0.3);color:#FBBF24;">
      &#128196; MIS PUNTOS (<span id="wp-count">0</span>)
    </button>
  </div>
</div>

<!-- SAVE DIALOG -->
<div id="wp-dialog">
  <h4>&#128205; GUARDAR PUNTO</h4>
  <span class="dlg-label">Nombre</span>
  <input class="dlg-input" id="dlg-name" type="text" placeholder="Ej: Bajo de las Almas...">
  <span class="dlg-label">Categoría</span>
  <select class="dlg-select" id="dlg-type">
    <option value="pesca">🐟 Punto de pesca</option>
    <option value="fondeo">⚓ Fondeo / Ancla</option>
    <option value="peligro">⚠️ Peligro / Bajo</option>
    <option value="referencia">📍 Referencia</option>
    <option value="ruta">🧭 Punto de ruta</option>
  </select>
  <span class="dlg-label">Notas (opcional)</span>
  <input class="dlg-input" id="dlg-note" type="text" placeholder="Profundidad, especie, marea...">
  <div class="dlg-row">
    <button class="dlg-btn dlg-save"   onclick="saveWaypoint()">&#10003; GUARDAR</button>
    <button class="dlg-btn dlg-cancel" onclick="closeDialog()">&#10005; CANCELAR</button>
  </div>
</div>

<div id="map"></div>
<div id="legend">
  <div class="leg-item"><div class="leg-dot" style="background:#F43F5E;"></div> Roca / Bajo</div>
  <div class="leg-item"><div class="leg-dot" style="background:#FBBF24;"></div> Arenal</div>
  <div class="leg-item"><div class="leg-dot" style="background:#10B981;"></div> Puerto</div>
  <div class="leg-item" style="gap:3px">
    <span style="font-size:0.62rem;color:#64748B;margin-right:2px;">Prof:</span>
    <div style="width:10px;height:12px;background:#b3e5fc;border-radius:2px 0 0 2px;"></div>
    <div style="width:10px;height:12px;background:#4fc3f7;"></div>
    <div style="width:10px;height:12px;background:#0288d1;"></div>
    <div style="width:10px;height:12px;background:#01579b;"></div>
    <div style="width:10px;height:12px;background:#002652;"></div>
    <div style="width:10px;height:12px;background:#000e20;border-radius:0 2px 2px 0;"></div>
    <span style="font-size:0.6rem;color:#64748B;"> GEBCO 2024</span>
  </div>
  <div class="leg-item"><div class="leg-line" style="background:#3B82F6;opacity:0.7;"></div> Corriente costera</div>
  <div class="leg-item"><div class="leg-line" style="background:#818CF8;opacity:0.7;"></div> Contracorriente</div>
  <div class="leg-item"><div class="leg-line" style="background:#06B6D4;opacity:0.7;"></div> Cte. marea</div>
  <div class="leg-item"><div class="leg-line" style="border-top:2px dashed #F43F5E;background:none;height:0;width:20px;"></div> Medición</div>
  <div class="leg-item"><div class="leg-line" style="border-top:2px dashed #10B981;background:none;height:0;width:20px;"></div> Derrota</div>
  <span class="leg-src">OpenSeaMap · ESRI Ocean · GEBCO 2024 (BODC) · EMODnet · OSM</span>
</div>

<!-- WAYPOINT PANEL -->
<div id="wp-panel">
  <div id="wp-panel-head">
    <span>&#128205; MIS PUNTOS GUARDADOS</span>
    <button id="wp-close" onclick="toggleWpPanel()">&#10005;</button>
  </div>
  <div id="wp-list">
    <div id="wp-empty">
      &#128205; Sin puntos guardados.<br>
      Activa <b>GUARDAR PUNTO</b> y haz<br>clic en la carta para añadir.
    </div>
  </div>
  <button id="wp-export-btn" onclick="exportWaypoints()">
    &#11123; EXPORTAR COMO TEXTO
  </button>
</div>
</div><!-- /wrapper -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map', {
  center:[43.35,-2.38], zoom:12,
  maxBounds:[[43.05,-2.85],[43.62,-1.90]], maxBoundsViscosity:0.85
});
map.options.minZoom=10; map.options.maxZoom=17;

var osmBase   = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {attribution:'© OSM',maxZoom:19});
var esriOcean = L.tileLayer(
  'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
  {attribution:'ESRI Ocean',maxZoom:16});
var esriRef   = L.tileLayer(
  'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}',
  {attribution:'ESRI Ref',maxZoom:16,opacity:0.9});
var seamark   = L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png',
  {attribution:'© OpenSeaMap',opacity:1.0});

// ── BATIMETRÍA — GEBCO 2024 (British Oceanographic Data Centre) ────────────────
// PROBLEMA ANTERIOR: SLD_BODY en peticiones WMS por tiles se trunca en URLs largas
// SOLUCIÓN: GEBCO WMS oficial con capas pre-coloreadas — sin SLD, siempre funciona
//
//  GEBCO_LATEST_2 = mapa plano coloreado por cota (azules para océano)
//  GEBCO_LATEST   = relieve sombreado hillshade
//  Fuente: wms.gebco.net — BODC / Nippon Foundation-GEBCO Seabed 2030 Project

var gebcoBathy = L.tileLayer.wms('https://wms.gebco.net/mapserv?', {
  layers:     'GEBCO_LATEST_2',
  styles:     '',
  format:     'image/png',
  transparent: true,
  opacity:     0.80,
  version:    '1.3.0',
  attribution:'© GEBCO 2024 / BODC'
});

var gebcoRelief = L.tileLayer.wms('https://wms.gebco.net/mapserv?', {
  layers:     'GEBCO_LATEST',
  styles:     '',
  format:     'image/png',
  transparent: true,
  opacity:     0.65,
  version:    '1.3.0',
  attribution:'© GEBCO 2024 / BODC'
});

// EMODnet isobatas — capa de contornos en su estilo nativo (sin SLD — funciona bien)
var emodCtrs = L.tileLayer.wms('https://ows.emodnet-bathymetry.eu/wms', {
  layers:     'emodnet:contours',
  styles:     '',
  format:     'image/png',
  transparent: true,
  opacity:     1.0,
  attribution:'© EMODnet Bathymetry'
});

// Por defecto: GEBCO color + isobatas EMODnet + marcas OpenSeaMap
esriOcean.addTo(map); esriRef.addTo(map);
gebcoBathy.addTo(map); emodCtrs.addTo(map); seamark.addTo(map);

L.control.layers(
  {
    '&#127754; ESRI Ocean + OpenSeaMap': L.layerGroup([esriOcean, esriRef, seamark]),
    '&#128506; OSM + OpenSeaMap':        L.layerGroup([osmBase, seamark])
  },
  {
    '&#127760; GEBCO 2024 — color por profundidad': gebcoBathy,
    '&#127956; GEBCO 2024 — relieve sombreado':     gebcoRelief,
    '&#10967;  EMODnet — isobatas (líneas)':        emodCtrs
  },
  {position:'topright', collapsed:false}
).addTo(map);

function mkIcon(bg,glyph){
  return L.divIcon({
    html:'<div style="background:'+bg+';color:white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:12px;border:2px solid rgba(255,255,255,0.3);box-shadow:0 0 10px '+bg+'88;">'+glyph+'</div>',
    iconSize:[28,28],iconAnchor:[14,14],popupAnchor:[0,-16],className:''
  });
}
var iRoca=mkIcon('#F43F5E','&#9875;');
var iArena=mkIcon('#D97706','&#128032;');
var iPuerto=mkIcon('#10B981','&#9973;');

var spots=[
  {lat:43.326,lng:-2.390,name:"Bajo de Mutriku",type:"rock",depth:"4-10 m",
   desc:"Bajo rocoso frente a la bocana. Fondo mixto roca-arena. Lubina y muxarra."},
  {lat:43.335,lng:-2.358,name:"Bajos de Saturraran",type:"rock",depth:"6-15 m",
   desc:"Roca al N de la playa. Txitxarro, berdel y faneca en temporada."},
  {lat:43.342,lng:-2.418,name:"Bajo Otoio",type:"rock",depth:"5-14 m",
   desc:"~1 NM al NNO del puerto de Mutriku. Pesca de fondo y curricán de lubina."},
  {lat:43.375,lng:-2.458,name:"Bajo Mendexa",type:"rock",depth:"10-22 m",
   desc:"Entre Mutriku y Lekeitio. Besugo y congrio."},
  {lat:43.398,lng:-2.498,name:"Bajos de Lekeitio",type:"rock",depth:"6-25 m",
   desc:"Al N de Lekeitio. Merluzón y besugo. Precaución con corriente."},
  {lat:43.322,lng:-2.348,name:"Bajo de Deba",type:"rock",depth:"4-12 m",
   desc:"Al N de la ría de Deba. Lubina y dorada en verano."},
  {lat:43.326,lng:-2.268,name:"Flysch de Zumaia",type:"rock",depth:"3-20 m",
   desc:"Zona de acantilado flysch. Gran diversidad bentónica. Excelente para roca."},
  {lat:43.348,lng:-2.428,name:"Bajo Ondarroa",type:"rock",depth:"5-16 m",
   desc:"Al N de Ondarroa. Txitxarro y muxarra. Buen fondo mixto."},
  {lat:43.392,lng:-2.430,name:"Arenal de Ondarroa",type:"sand",depth:"18-35 m",
   desc:"Plataforma arenosa al N de Ondarroa. Lenguado y rodaballo."},
  {lat:43.380,lng:-2.395,name:"Arenal de Mutriku N",type:"sand",depth:"22-42 m",
   desc:"~3 NM al N de Mutriku. Merluzón y congrio en pleamar nocturna."},
  {lat:43.415,lng:-2.462,name:"Arenal del Lea",type:"sand",depth:"28-50 m",
   desc:"Entre Lekeitio y Ondarroa. Besugo y palometa en profundidad."},
  {lat:43.358,lng:-2.348,name:"Arenal de Deba",type:"sand",depth:"20-38 m",
   desc:"Al N de Deba. Lenguado y salmonete en verano."},
  {lat:43.370,lng:-2.499,name:"Puerto de Lekeitio",type:"port",depth:"—",
   desc:"Puerto pesquero y deportivo. Lonja activa. Gasoil, agua, avituallamiento."},
  {lat:43.309,lng:-2.381,name:"Puerto de Mutriku",type:"port",depth:"—",
   desc:"Puerto deportivo y pesquero. Gasoil. Rampa de varada."},
  {lat:43.321,lng:-2.419,name:"Puerto de Ondarroa",type:"port",depth:"—",
   desc:"Mayor puerto pesquero de la zona. Lonja diaria. Grúa disponible."},
  {lat:43.299,lng:-2.258,name:"Puerto de Zumaia",type:"port",depth:"—",
   desc:"Puerto deportivo junto al flysch. Acceso por ría con corriente en llenante."}
];
spots.forEach(function(s){
  var ic=s.type==='rock'?iRoca:(s.type==='sand'?iArena:iPuerto);
  var tipo=s.type==='rock'?'&#128255; Roca / Bajo':s.type==='sand'?'&#127958; Arenal':'&#9875; Puerto';
  var dh=s.depth!=='—'?'<div style="background:rgba(56,189,248,0.1);border-radius:4px;padding:3px 8px;margin-bottom:6px;font-size:0.76rem;font-weight:700;color:#38BDF8;display:inline-block;">Prof: '+s.depth+'</div>':'';
  L.marker([s.lat,s.lng],{icon:ic})
   .bindPopup('<div style="font-family:sans-serif;min-width:190px;max-width:240px;background:#0D1B33;color:#E2E8F0;">'+
              '<div style="font-weight:900;font-size:0.92rem;color:#38BDF8;margin-bottom:4px;">'+s.name+'</div>'+
              '<div style="color:#F43F5E;font-size:0.7rem;font-weight:700;margin-bottom:6px;text-transform:uppercase;">'+tipo+'</div>'+
              dh+'<div style="font-size:0.77rem;color:#94A3B8;line-height:1.55;">'+s.desc+'</div></div>',
              {maxWidth:260}).addTo(map);
});

var currents=[
  {coords:[[43.48,-2.52],[43.38,-2.52],[43.38,-2.25],[43.48,-2.25]],
   name:"Corriente Costera del Cantábrico",dir:"E &#10132; O",speed:"0.3-0.9 kn",
   note:"Predominante otoño-invierno. Se intensifica con ENE.",color:"#3B82F6"},
  {coords:[[43.38,-2.52],[43.34,-2.52],[43.34,-2.25],[43.38,-2.25]],
   name:"Contracorriente de Profundidad",dir:"O &#10132; E (20-80 m)",speed:"0.2-0.5 kn",
   note:"Verano-otoño bajo termoclina. Afecta palangres de fondo.",color:"#818CF8"},
  {coords:[[43.345,-2.408],[43.320,-2.408],[43.320,-2.368],[43.345,-2.368]],
   name:"Corriente de Marea – Mutriku",dir:"Variable con marea",speed:"0.5-1.8 kn",
   note:"Fluye al N en llenante, al S en vaciante.",color:"#06B6D4"},
  {coords:[[43.402,-2.518],[43.372,-2.518],[43.372,-2.480],[43.402,-2.480]],
   name:"Corriente de Marea – Lekeitio",dir:"Variable con marea",speed:"0.4-1.4 kn",
   note:"Marcada en bocana. Precaución en mareas vivas.",color:"#06B6D4"}
];
currents.forEach(function(c){
  L.polygon(c.coords,{color:c.color,fillColor:c.color,fillOpacity:0.12,weight:2,dashArray:'6,5'})
   .bindPopup('<div style="background:#0D1B33;color:#E2E8F0;font-family:sans-serif;min-width:200px;">'+
              '<div style="font-weight:900;font-size:0.88rem;color:#38BDF8;margin-bottom:6px;">&#127754; '+c.name+'</div>'+
              '<div style="font-size:0.78rem;margin-bottom:3px;"><b style="color:#FBBF24">Dir:</b> '+c.dir+'</div>'+
              '<div style="font-size:0.78rem;margin-bottom:5px;"><b style="color:#FBBF24">Vel:</b> '+c.speed+'</div>'+
              '<div style="font-size:0.74rem;color:#64748B;">'+c.note+'</div></div>',
              {maxWidth:280}).addTo(map);
});

var tool=null,mPts=[],mLines=[],mMarkers=[],bPts=[],bLine=null,bMarkers=[];

// ── WAYPOINT SYSTEM ─────────────────────────────────────────────────
var WP_KEY = 'txomin_waypoints_v1';
var wpData  = [];          // array de waypoints en memoria
var wpMapMarkers = {};     // id → Leaflet marker en mapa
var pendingLatLng = null;  // coordenada esperando confirmación

var WP_CFG = {
  pesca:      { icon:'🐟', color:'#10B981', label:'Pesca'      },
  fondeo:     { icon:'⚓', color:'#FBBF24', label:'Fondeo'     },
  peligro:    { icon:'⚠️', color:'#F43F5E', label:'Peligro'    },
  referencia: { icon:'📍', color:'#38BDF8', label:'Referencia' },
  ruta:       { icon:'🧭', color:'#818CF8', label:'Ruta'       }
};

function loadWaypoints() {
  try {
    var raw = localStorage.getItem(WP_KEY);
    wpData = raw ? JSON.parse(raw) : [];
  } catch(e) { wpData = []; }
  wpData.forEach(function(wp){ renderWpMarker(wp); });
  refreshWpPanel();
}

function saveWaypointsLS() {
  try { localStorage.setItem(WP_KEY, JSON.stringify(wpData)); } catch(e) {}
}

function genId() {
  return 'wp_' + Date.now() + '_' + Math.random().toString(36).substr(2,5);
}

function renderWpMarker(wp) {
  var cfg = WP_CFG[wp.type] || WP_CFG.referencia;
  var ic = L.divIcon({
    html: '<div style="background:'+cfg.color+';color:white;border-radius:50%;'
        + 'width:32px;height:32px;display:flex;align-items:center;justify-content:center;'
        + 'font-size:14px;border:2px solid white;'
        + 'box-shadow:0 0 12px '+cfg.color+'99;cursor:pointer;">'
        + cfg.icon + '</div>',
    iconSize:[32,32], iconAnchor:[16,16], popupAnchor:[0,-18], className:''
  });
  var m = L.marker([wp.lat, wp.lng], {icon:ic, draggable:true});
  m.bindPopup(buildWpPopup(wp), {maxWidth:260});

  // Drag para reposicionar
  m.on('dragend', function(ev) {
    var ll = ev.target.getLatLng();
    wp.lat = parseFloat(ll.lat.toFixed(6));
    wp.lng = parseFloat(ll.lng.toFixed(6));
    saveWaypointsLS(); refreshWpPanel();
    m.setPopupContent(buildWpPopup(wp));
  });

  m.addTo(map);
  wpMapMarkers[wp.id] = m;
}

function buildWpPopup(wp) {
  var cfg = WP_CFG[wp.type] || WP_CFG.referencia;
  return '<div style="font-family:Manrope,sans-serif;min-width:180px;">'
    + '<div style="font-size:0.88rem;font-weight:800;color:'+cfg.color+';margin-bottom:3px;">'
    + cfg.icon + ' ' + escHtml(wp.name) + '</div>'
    + '<div style="font-size:0.65rem;color:#64748B;font-weight:700;text-transform:uppercase;'
    + 'letter-spacing:1px;margin-bottom:6px;">'+cfg.label+'</div>'
    + (wp.note ? '<div style="font-size:0.74rem;color:#94A3B8;font-style:italic;margin-bottom:8px;">'
      + escHtml(wp.note) + '</div>' : '')
    + '<div style="font-size:0.62rem;color:#475569;font-family:monospace;margin-bottom:8px;">'
    + wp.lat.toFixed(5)+'° N &nbsp; '+Math.abs(wp.lng).toFixed(5)+'° O</div>'
    + '<div style="display:flex;gap:6px;">'
    + '<button onclick="deleteWp(\''+wp.id+'\')" style="flex:1;padding:5px;background:rgba(244,63,94,0.15);'
    + 'color:#F43F5E;border:1px solid rgba(244,63,94,0.3);border-radius:5px;cursor:pointer;'
    + 'font-size:0.65rem;font-weight:700;">&#128465; BORRAR</button>'
    + '<button onclick="map.closePopup()" style="flex:1;padding:5px;background:rgba(56,189,248,0.1);'
    + 'color:#38BDF8;border:1px solid rgba(56,189,248,0.2);border-radius:5px;cursor:pointer;'
    + 'font-size:0.65rem;font-weight:700;">&#10005; CERRAR</button>'
    + '</div></div>';
}

function escHtml(s) {
  return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                .replace(/"/g,'&quot;');
}

function refreshWpPanel() {
  var list = document.getElementById('wp-list');
  var empty = document.getElementById('wp-empty');
  document.getElementById('wp-count').textContent = wpData.length;
  if (wpData.length === 0) {
    list.innerHTML = '<div id="wp-empty">&#128205; Sin puntos guardados.<br>'
      + 'Activa <b>GUARDAR PUNTO</b> y haz<br>clic en la carta para añadir.</div>';
    return;
  }
  list.innerHTML = '';
  wpData.slice().reverse().forEach(function(wp) {
    var cfg = WP_CFG[wp.type] || WP_CFG.referencia;
    var el = document.createElement('div');
    el.className = 'wp-item';
    el.style.borderLeftColor = cfg.color;
    el.innerHTML =
      '<div class="wp-item-top">'
      + '<span class="wp-item-icon">'+cfg.icon+'</span>'
      + '<span class="wp-item-name">'+escHtml(wp.name)+'</span>'
      + '</div>'
      + '<div class="wp-item-coords">'+wp.lat.toFixed(5)+'°N  '+Math.abs(wp.lng).toFixed(5)+'°O</div>'
      + (wp.note ? '<div class="wp-item-note">'+escHtml(wp.note)+'</div>' : '')
      + '<div class="wp-item-actions">'
      + '<button class="wp-btn wp-btn-go"  onclick="flyToWp(\''+wp.id+'\')">&#127979; IR</button>'
      + '<button class="wp-btn wp-btn-del" onclick="deleteWp(\''+wp.id+'\')">&#128465; BORRAR</button>'
      + '</div>';
    list.appendChild(el);
  });
}

function flyToWp(id) {
  var wp = wpData.find(function(w){ return w.id===id; });
  if (!wp) return;
  map.flyTo([wp.lat, wp.lng], 14, {duration:1.2});
  setTimeout(function(){ if (wpMapMarkers[id]) wpMapMarkers[id].openPopup(); }, 1400);
}

function deleteWp(id) {
  if (wpMapMarkers[id]) { map.removeLayer(wpMapMarkers[id]); delete wpMapMarkers[id]; }
  wpData = wpData.filter(function(w){ return w.id!==id; });
  saveWaypointsLS(); refreshWpPanel();
  map.closePopup();
}

function toggleWpPanel() {
  document.getElementById('wp-panel').classList.toggle('open');
}

function exportWaypoints() {
  if (!wpData.length) { alert('No hay puntos guardados.'); return; }
  var lines = ['TXOMIN — PUNTOS GUARDADOS', '========================', ''];
  wpData.forEach(function(wp, i) {
    var cfg = WP_CFG[wp.type] || WP_CFG.referencia;
    lines.push((i+1)+'. '+cfg.icon+' '+wp.name+' ['+cfg.label+']');
    lines.push('   Coords: '+wp.lat.toFixed(6)+'° N, '+wp.lng.toFixed(6)+'° O');
    if (wp.note) lines.push('   Nota: '+wp.note);
    lines.push('');
  });
  var blob = new Blob([lines.join('\n')], {type:'text/plain'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'txomin_waypoints.txt';
  a.click();
}

// ── DIALOG HELPERS ──────────────────────────────────────────────────
function openDialog(latlng) {
  pendingLatLng = latlng;
  var dlg = document.getElementById('wp-dialog');
  document.getElementById('dlg-name').value = '';
  document.getElementById('dlg-note').value = '';
  document.getElementById('dlg-type').value = 'pesca';
  // Posición: cerca del click pero dentro del mapa
  var pt = map.latLngToContainerPoint(latlng);
  var mapEl = document.getElementById('map');
  var x = Math.min(pt.x + 10, mapEl.offsetWidth  - 260);
  var y = Math.min(pt.y - 10, mapEl.offsetHeight - 260);
  dlg.style.left = (x + mapEl.offsetLeft) + 'px';
  dlg.style.top  = (y + 56) + 'px';   // 56 = toolbar height
  dlg.style.display = 'block';
  setTimeout(function(){ document.getElementById('dlg-name').focus(); }, 50);
}

function closeDialog() {
  document.getElementById('wp-dialog').style.display = 'none';
  pendingLatLng = null;
}

function saveWaypoint() {
  if (!pendingLatLng) return;
  var name = document.getElementById('dlg-name').value.trim();
  if (!name) { document.getElementById('dlg-name').focus(); return; }
  var wp = {
    id:   genId(),
    name: name,
    type: document.getElementById('dlg-type').value,
    note: document.getElementById('dlg-note').value.trim(),
    lat:  parseFloat(pendingLatLng.lat.toFixed(6)),
    lng:  parseFloat(pendingLatLng.lng.toFixed(6)),
    ts:   Date.now()
  };
  wpData.push(wp);
  saveWaypointsLS();
  renderWpMarker(wp);
  refreshWpPanel();
  closeDialog();
  setResult('&#128205; Punto <b>'+escHtml(wp.name)+'</b> guardado — '
    + wp.lat.toFixed(4)+'°N '+Math.abs(wp.lng).toFixed(4)+'°O');
  // Abrir popup del marker recién creado
  setTimeout(function(){
    if (wpMapMarkers[wp.id]) wpMapMarkers[wp.id].openPopup();
  }, 200);
}

// Cerrar dialog con Escape
document.addEventListener('keydown', function(e){
  if (e.key==='Escape') closeDialog();
  if (e.key==='Enter' && document.getElementById('wp-dialog').style.display==='block') saveWaypoint();
});

// ── TOOLS ───────────────────────────────────────────────────────────
function setTool(t){
  clearAll(); tool=t;
  document.getElementById('btn-measure').classList.toggle('active',t==='measure');
  document.getElementById('btn-bearing').classList.toggle('active',t==='bearing');
  document.getElementById('btn-wp').classList.toggle('active',t==='waypoint');
  map.getContainer().style.cursor = t==='waypoint' ? 'crosshair' : 'crosshair';
  if (t==='measure')
    setResult('&#128207; Clic para añadir puntos · <b>doble clic</b> para terminar');
  else if (t==='bearing')
    setResult('&#129517; Clic en punto <b>ORIGEN</b> (A)');
  else if (t==='waypoint')
    setResult('&#128205; Haz clic en la carta para colocar un punto guardado');
}
function clearAll(){
  mPts=[];mLines.forEach(function(l){map.removeLayer(l);});mLines=[];
  mMarkers.forEach(function(m){map.removeLayer(m);});mMarkers=[];
  if(bLine){map.removeLayer(bLine);bLine=null;}
  bPts=[];bMarkers.forEach(function(m){map.removeLayer(m);});bMarkers=[];
  closeDialog();
  if(!tool){setResult('Selecciona herramienta y haz clic en la carta');map.getContainer().style.cursor='';}
  else{setTool(tool);}
}
function setResult(h){document.getElementById('result-panel').innerHTML=h;}
function distNM(a,b){
  var R=3440.065,dLat=(b.lat-a.lat)*Math.PI/180,dLng=(b.lng-a.lng)*Math.PI/180;
  var la1=a.lat*Math.PI/180,la2=b.lat*Math.PI/180;
  var x=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.sin(dLng/2)*Math.sin(dLng/2)*Math.cos(la1)*Math.cos(la2);
  return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));}
function bearing(a,b){
  var dLng=(b.lng-a.lng)*Math.PI/180,la1=a.lat*Math.PI/180,la2=b.lat*Math.PI/180;
  return(Math.atan2(Math.sin(dLng)*Math.cos(la2),Math.cos(la1)*Math.sin(la2)-Math.sin(la1)*Math.cos(la2)*Math.cos(dLng))*180/Math.PI+360)%360;}
function compass(d){return['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSO','SO','OSO','O','ONO','NO','NNO'][Math.round(d/22.5)%16];}
function addMark(ll,lbl,col){
  var m=L.circleMarker(ll,{radius:5,color:col||'#F43F5E',fillColor:col||'#F43F5E',fillOpacity:1,weight:2}).addTo(map);
  if(lbl)m.bindTooltip(lbl,{permanent:true,direction:'top',offset:[0,-7],className:'mtip'});
  return m;}
map.on('click',function(e){
  if(!tool)return;
  if(tool==='waypoint'){
    openDialog(e.latlng);
    return;
  }
  if(tool==='measure'){
    mPts.push(e.latlng);var n=mPts.length;
    mMarkers.push(addMark(e.latlng,String(n)));
    if(n>=2){
      mLines.push(L.polyline([mPts[n-2],mPts[n-1]],{color:'#F43F5E',weight:2.5,dashArray:'9,6',opacity:0.9}).addTo(map));
      var mid=L.latLng((mPts[n-2].lat+mPts[n-1].lat)/2,(mPts[n-2].lng+mPts[n-1].lng)/2);
      var sd=distNM(mPts[n-2],mPts[n-1]).toFixed(2);
      mMarkers.push(L.marker(mid,{icon:L.divIcon({html:'<div style="background:#F43F5E;color:white;padding:2px 6px;border-radius:4px;font-size:0.63rem;font-weight:900;white-space:nowrap;">'+sd+' NM</div>',className:'',iconAnchor:[22,8]})}).addTo(map));}
    var tot=0;for(var i=1;i<mPts.length;i++)tot+=distNM(mPts[i-1],mPts[i]);
    setResult('&#128207; Puntos: <b>'+n+'</b> · Tramo: <b>'+(n>=2?distNM(mPts[n-2],mPts[n-1]).toFixed(2)+' NM':'—')+'</b> · Total: <b>'+tot.toFixed(2)+' NM</b> ('+((tot*1.852).toFixed(1))+' km) · doble clic para fin');
  }else if(tool==='bearing'){
    bPts.push(e.latlng);
    var col2=bPts.length===1?'#10B981':'#F43F5E',lb2=bPts.length===1?'A':'B';
    bMarkers.push(L.marker(e.latlng,{icon:L.divIcon({html:'<div style="background:'+col2+';color:white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:12px;border:2px solid white;">'+lb2+'</div>',iconSize:[24,24],iconAnchor:[12,12],className:''})}).addTo(map));
    if(bPts.length===2){
      var A=bPts[0],B=bPts[1];
      if(bLine)map.removeLayer(bLine);
      bLine=L.polyline([A,B],{color:'#10B981',weight:3,dashArray:'10,7',opacity:0.95}).addTo(map);
      var dist=distNM(A,B),brng=bearing(A,B),brec=(brng+180)%360;
      setResult('&#129517; Rumbo: <b>'+brng.toFixed(1)+'° ('+compass(brng)+')</b> · Recíproco: <b>'+brec.toFixed(1)+'°</b> · Dist: <b>'+dist.toFixed(2)+' NM</b> · ETA@6kn: <b>'+((dist/6*60).toFixed(0))+'min</b> · ETA@10kn: <b>'+((dist/10*60).toFixed(0))+'min</b>');
      var mid2=L.latLng((A.lat+B.lat)/2,(A.lng+B.lng)/2);
      bMarkers.push(L.marker(mid2,{icon:L.divIcon({html:'<div style="transform:rotate('+brng+'deg);font-size:20px;color:#10B981">&#10148;</div>',className:'',iconAnchor:[10,10]})}).addTo(map));
      setTimeout(function(){bPts=[];bMarkers.forEach(function(m){map.removeLayer(m);});bMarkers=[];if(bLine){map.removeLayer(bLine);bLine=null;}setResult('&#129517; Clic en <b>ORIGEN</b> (A) para nueva derrota');},4500);
    }else{setResult('&#129517; Punto A marcado. Clic en <b>DESTINO</b> (B)');}
  }
});
map.on('dblclick',function(e){
  if(tool==='measure'&&mPts.length>=2){
    var tot=0;for(var i=1;i<mPts.length;i++)tot+=distNM(mPts[i-1],mPts[i]);
    setResult('&#9989; Ruta: <b>'+mPts.length+' puntos</b> · Total: <b>'+tot.toFixed(2)+' NM</b> ('+((tot*1.852).toFixed(1))+' km)');
    tool=null;document.getElementById('btn-measure').classList.remove('active');map.getContainer().style.cursor='';}
});
L.control.scale({position:'bottomleft',metric:true,imperial:false,maxWidth:150}).addTo(map);
var cc=L.control({position:'bottomright'});
cc.onAdd=function(){this._div=L.DomUtil.create('div','');
  this._div.style.cssText='background:rgba(10,22,40,0.9);color:#38BDF8;padding:5px 11px;border-radius:6px;font-size:0.7rem;font-weight:700;font-family:monospace;border:1px solid rgba(56,189,248,0.2);';
  this._div.innerHTML='— N  — O';return this._div;};
cc.addTo(map);
map.on('mousemove',function(e){cc._div.innerHTML=e.latlng.lat.toFixed(5)+'° N &nbsp; '+Math.abs(e.latlng.lng).toFixed(5)+'° O';});

// ── INIT: cargar waypoints guardados ────────────────────────────────
loadWaypoints();
</script>
</body>
</html>"""

    components.html(CHART_HTML, height=800, scrolling=False)
    st.markdown("""
    <div class='pie'>
      🗺️ <b>OpenSeaMap</b> (marcas náuticas) · <b>ESRI Ocean</b> (carta base) ·
      <b>EMODnet</b> (batimetría oficial europea) · Puntos de pesca verificados en el mar
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  TAB 3 — PREVISIÓN 3 DÍAS (06:00–23:00, cada 3 horas)
# ════════════════════════════════════════════════════════════════════
with tab3:

    st.markdown("<span class='sec-title'>📅 PREVISIÓN TÁCTICA — PRÓXIMOS 3 DÍAS (06:00 – 23:00, cada 3h)</span>",
                unsafe_allow_html=True)

    DAY_COLORS = ["#1D4ED8", "#B45309", "#6D28D9"]
    HORAS_DIA  = [6, 9, 12, 15, 18, 21, 23]   # franjas horarias a mostrar

    for day_offset in range(1, 4):
        d           = ahora + timedelta(days=day_offset)
        target_date = d.date()

        # Filtrar horas concretas del día
        day_rows = df[
            (df['time'].dt.date == target_date) &
            (df['time'].dt.hour.isin(HORAS_DIA))
        ].copy()

        if day_rows.empty:
            continue

        col       = DAY_COLORS[day_offset - 1]
        day_label = f"{DIAS_ES[d.weekday()].upper()}  {d.day} {MESES_ES[d.month-1].upper()}"

        # Resumen del día
        def _avg(cn):
            vals = [fv(r) for r in day_rows[cn] if fv(r) is not None]
            return sum(vals)/len(vals) if vals else None
        def _mx(cn):
            vals = [fv(r) for r in day_rows[cn] if fv(r) is not None]
            return max(vals) if vals else None

        avg_wind = _avg('v_media'); max_gust = _mx('v_racha')
        avg_wave = _avg('ola');     avg_temp = _avg('temp')
        avg_pres = _avg('presion')

        nivel_dia, _ = semaforo(max_gust, _mx('ola'), avg_pres, [])
        sem_color = {"verde":"#059669","amarillo":"#B45309","rojo":"#DC2626"}[nivel_dia]
        sem_icon  = {"verde":"✅","amarillo":"⚠️","rojo":"🚫"}[nivel_dia]

        # Cabecera del día
        st.markdown(f"""
        <div class='day-section'>
          <div class='day-header' style='color:{col}'>
            {day_label}
            <span style='color:{sem_color};font-family:Manrope,sans-serif;
                         font-size:0.72rem;letter-spacing:1px;margin-left:8px;'>
              {sem_icon} {nivel_dia.upper()}
            </span>
            <span style='color:#94A3B8;font-size:0.65rem;font-family:Manrope,sans-serif;
                         font-weight:600;'>
              Viento medio {safe(avg_wind,0)} km/h &nbsp;·&nbsp;
              Ola {safe(avg_wave)} m &nbsp;·&nbsp;
              Agua {safe(avg_temp)}°C
            </span>
          </div>
        </div>""", unsafe_allow_html=True)

        # Cuadro de mareas del día
        st.markdown(render_tide_box(d), unsafe_allow_html=True)

        # Tarjetas horarias 06–23
        cards = "".join(render_hour_card(r, col) for _, r in day_rows.iterrows())
        components.html(f"""
        <div style="background:#FFFFFF;border:1px solid rgba(30,58,138,0.12);
                    border-radius:10px;padding:14px 14px 6px;margin-bottom:6px;
                    box-shadow:0 2px 8px rgba(30,58,138,0.07);">
          <div style="display:flex;overflow-x:auto;gap:10px;padding-bottom:8px;
                      scrollbar-width:thin;scrollbar-color:{col} #E8EEF4;">
            {cards}
          </div>
        </div>""", height=215, scrolling=False)

    st.markdown("""
    <div class='pie'>
      Previsión: <b>Open-Meteo</b> (actualización cada 10 min) &nbsp;·&nbsp;
      Mareas: <b>Modelo M2 Cantábrico</b> (±30 min) &nbsp;·&nbsp;
      Semáforo diario basado en valores máximos del día
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  TAB 4 — ESPECIES & TÉCNICAS DE PESCA
# ════════════════════════════════════════════════════════════════════
with tab4:

    st.markdown("<span class='sec-title'>🐟 GUÍA DE ESPECIES — CANTÁBRICO ORIENTAL</span>",
                unsafe_allow_html=True)

    # ── DATOS DE CADA ESPECIE ────────────────────────────────────────
    SPECIES_DATA = [
        {
            "name": "TXITXARRO",
            "latin": "Trachurus trachurus · Jurel",
            "icon": "🐟",
            "color": "#38BDF8",
            "temporada": "Todo el año · Máximo marzo-octubre",
            "profundidad": "Superficie a 30 m · Cardúmenes",
            "cuando": [
                "Mejor en **alba y ocaso** (6-10h / 18-22h)",
                "Marea entrante o en calma",
                "Mar con oleaje <1.5 m y viento <25 km/h",
                "Agua entre 14-22°C",
            ],
            "aparejos": [
                ("Plomo viajero", "Línea de 0.35mm. Plomo 60-100g. Brazoladas de 0.25mm con anzuelos n°8-10. Calamar o cebo de gamba. Bajada rápida hasta fondo."),
                ("Curricán de superficie", "Señuelos metálicos 20-40g en colores plateados/azul. Velocidad 4-6 nudos. Efectivo desde junio."),
                ("Jig metálico", "40-80g en colores cromo/fuego. Técnica de jigging suave desde fondos de 15-25m."),
            ],
        },
        {
            "name": "TXIPIRON",
            "latin": "Loligo vulgaris · Calamar común",
            "icon": "🦑",
            "color": "#818CF8",
            "temporada": "Septiembre-Enero (temporada alta)",
            "profundidad": "Columna de agua 5-40 m · Nocturno",
            "cuando": [
                "**Noche cerrada y luna nueva** — primordial",
                "Mar en calma absoluta, oleaje <0.7 m",
                "Agua >15°C favorece la actividad",
                "Buzos de luz para concentrar el cardumen",
            ],
            "aparejos": [
                ("Poteras japonesas (Egi)", "Tallas 2.5-3.5. Colores naranja/rosa en noche sin luna; azul/verde con luna. Caída lenta, pausa de 3-5s y sacudida brusca."),
                ("Txipiron a la bombilla", "Luz sumergible o flotante para atraer krill. Línea multifilamento 0.12mm + fluorocarbono 0.25mm. Potera a 2m de la luz."),
                ("Línea de poteras múltiples", "Tren de 3-5 poteras en cascada. Pesca vertical desde fondos de 15-35m frente a los bajos rocosos."),
            ],
        },
        {
            "name": "MUXARRA · SARGO · BRECA",
            "latin": "Sparidae · Espáridos costeros",
            "icon": "🐠",
            "color": "#FBBF24",
            "temporada": "Muxarra: mayo-oct · Sargo: todo el año",
            "profundidad": "2-20 m · Fondos rocosos litorales",
            "cuando": [
                "Mar tranquila, oleaje <1.0 m",
                "Horas diurnas: 8-13h y 16-20h",
                "Agua >16°C para muxarra · >12°C para sargo",
                "Presión alta y estable favorece",
            ],
            "aparejos": [
                ("Feeder de fondo", "Plomo de cola 50-80g. Brazolada corta 0.22mm anzuelo n°6-8. Cebo: gamba, mejillón o cangrejo ermitaño."),
                ("Pesca a la inglesa", "Flotador de 8-15g. Línea 0.25mm. Anzuelo n°10-12. Cebo de gusano arenicola o quisquilla. Zona de roca y alga."),
                ("Rock fishing ligero", "Señuelos de silicona 1-3\" en jig de 5-15g. Técnica drop-shot en fondos rocosos. Especialmente efectivo para sargo."),
            ],
        },
        {
            "name": "FANECA & OTRAS",
            "latin": "Trisopterus luscus · Brosmius brosme",
            "icon": "🐡",
            "color": "#F59E0B",
            "temporada": "Todo el año · Mejor oct-marzo",
            "profundidad": "10-80 m · Fondo rocoso y mixto",
            "cuando": [
                "Marea vaciante y primeras horas de noche",
                "Agua fría-templada: 8-16°C óptimo",
                "Oleaje <2.0 m · Pesca de fondo desde fondeo",
                "Frentes fríos otoñales activan los cardúmenes",
            ],
            "aparejos": [
                ("Línea de fondo múltiple", "Plomo 100-150g. 3 brazoladas de 0.30mm anzuelos n°6. Cebo: tira de calamar, gusano o sardina. Toca fondo y espera."),
                ("Paternoster", "Brazoladas con posit flotante para separar del fondo. Muy efectivo en fondos con algas y rocas donde emboza."),
                ("Curricán profundo", "Plomo torpedo 80g + señuelo de 10cm. Rastreo a baja velocidad (2-3 kn) sobre fondos de 20-40m."),
            ],
        },
        {
            "name": "LUBINA",
            "latin": "Dicentrarchus labrax · Bass · Legatza",
            "icon": "🎣",
            "color": "#10B981",
            "temporada": "Todo el año · Mejor sept-nov y marzo-mayo",
            "profundidad": "Superficie a 15 m · Zonas de turbulencia",
            "cuando": [
                "**Oleaje activo 0.3-1.5 m** — la lubina ama la espuma",
                "Alba y ocaso con marea entrante",
                "Viento moderado del NNO activa las orillas rocosas",
                "Agua 12-20°C · Busca corrientes y rompientes",
            ],
            "aparejos": [
                ("Spinning ligero", "Caña 10-30g. Señuelos minnow 9-14cm en colores pez de plata. Recuperación errática con pausas en rompientes y bocanas."),
                ("Popper de superficie", "Señuelos de superficie 10-15g. Efectivo al amanecer en calma con algo de corriente."),
                ("Curricán con rapala", "Señuelo flotante/hunidor 9-13cm plata/azul. Velocidad 3-4 kn frente a rompientes y puntas de tierra."),
            ],
        },
        {
            "name": "BERDEL",
            "latin": "Scomber scombrus · Caballa atlántica",
            "icon": "🐟",
            "color": "#06B6D4",
            "temporada": "Abril-septiembre (migración costera)",
            "profundidad": "Superficie a 20 m · Cardúmenes pelágicos",
            "cuando": [
                "Agua >16°C — llegan con el calor",
                "Horas de luz con buen sol",
                "Mar abierta o ligera marejadilla",
                "Busca termoclinas y manchas de cebo",
            ],
            "aparejos": [
                ("Tren de cucharillas", "4-6 cucharillas pequeñas (n°0-1) en serie. Lastre 40-60g. Bajada rápida, recuperación media. Efectivísimo."),
                ("Spinning ultra-ligero", "Señuelos metálicos 5-15g, colores cromo y naranja. Lanzamiento desde proa hacia cardúmenes visibles en superficie."),
                ("Curricán de superficie", "Señuelos pluma o minnow pequeño. Velocidad 5-7 nudos. Deja estela larga. Busca las manchas de gaviotas."),
            ],
        },
        {
            "name": "BESUGO",
            "latin": "Pagellus bogaraveo · Breca del norte",
            "icon": "🐟",
            "color": "#F43F5E",
            "temporada": "Octubre-Febrero (temporada clásica)",
            "profundidad": "30-100 m · Fondos de roca y arena",
            "cuando": [
                "Mar en calma, oleaje <1.0 m ideal",
                "Agua fría: 10-16°C óptimo",
                "Marea vaciante — bajan a alimentarse",
                "Alta presión estable varios días",
            ],
            "aparejos": [
                ("Línea de besugo clásica", "Plomo 200-400g. Brazoladas con posit + anzuelos 2/0. Cebo: gamba entera, calamar o cebo compuesto. Fondos de 40-80m."),
                ("Jigging vertical profundo", "Jig de 150-250g en colores rojo/dorado. Técnica 'slow jig': caída libre y subida lenta. Muy efectivo en bajos conocidos."),
                ("Curricán profundo nocturno", "Plomo torpedo + señuelo de gamba 12cm. Rastreo nocturno en fondos de 50-80m sobre arenales conocidos."),
            ],
        },
        {
            "name": "CONGRIO",
            "latin": "Conger conger · Aingira",
            "icon": "🐍",
            "color": "#A78BFA",
            "temporada": "Todo el año · Mejor verano-otoño",
            "profundidad": "5-60 m · Grietas y fondos rocosos",
            "cuando": [
                "**Noche o crepúsculo** — animal nocturno",
                "Marea vaciante, cuando salen a cazar",
                "Fondos rocosos y zonas de detritus",
                "Mar en calma para localizar grietas",
            ],
            "aparejos": [
                ("Línea de fondo potente", "Línea 0.50mm o hilo multifilamento 50lb. Anzuelo 7/0-10/0 con brazolada de acero 40cm. Cebo: jibia entera, caballa o anguila de río."),
                ("Pesca de noche desde fondeado", "Ancla sobre bajo rocoso conocido. 2 líneas de fondo a distintas profundidades. Espera paciente 1-3 horas."),
                ("Drop-shot pesado", "Plomo 80-120g. Brazolada de acero 30cm + anzuelo 5/0. Cebo vivo o muerto. Bajada vertical sobre grietas."),
            ],
        },
    ]

    # ── RENDER TARJETAS DE ESPECIE ───────────────────────────────────
    fish_html = "<div class='fish-grid'>"
    for sp in SPECIES_DATA:
        cuando_html = "".join(
            f"<li style='padding:2px 0;color:#94A3B8;'>{c.replace('**','<b style=\"color:#E2E8F0\">').replace('**','</b>')}</li>"
            for c in sp["cuando"]
        )
        aparejos_html = "".join(
            f"<div class='tackle-item'><b>{a[0]}</b><br>{a[1]}</div>"
            for a in sp["aparejos"]
        )
        fish_html += f"""
        <div class='fish-card'>
          <div class='fish-card-accent' style='background:linear-gradient(90deg,{sp["color"]},transparent)'></div>
          <div style='font-size:2rem;margin-bottom:6px'>{sp["icon"]}</div>
          <div class='fish-name' style='color:{sp["color"]}'>{sp["name"]}</div>
          <span class='fish-latin'>{sp["latin"]}</span>
          <div style='display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap'>
            <span style='background:rgba(255,255,255,0.05);border-radius:4px;padding:2px 8px;font-size:0.62rem;color:#94A3B8'>
              📅 {sp["temporada"]}</span>
            <span style='background:rgba(255,255,255,0.05);border-radius:4px;padding:2px 8px;font-size:0.62rem;color:#94A3B8'>
              📏 {sp["profundidad"]}</span>
          </div>
          <div class='fish-section-title' style='color:{sp["color"]}'>
            <span>⏰</span> CUÁNDO PESCAR
          </div>
          <ul style='margin:0;padding-left:14px;font-size:0.78rem;color:#94A3B8;line-height:1.7'>
            {cuando_html}
          </ul>
          <div class='fish-section-title' style='color:{sp["color"]};margin-top:12px'>
            <span>🪝</span> APAREJOS Y TÉCNICA
          </div>
          {aparejos_html}
        </div>"""
    fish_html += "</div>"
    st.markdown(fish_html, unsafe_allow_html=True)

    # ── ANÁLISIS IA PARA HOY ─────────────────────────────────────────
    st.markdown("<span class='sec-title'>🤖 ANÁLISIS IA — CONSEJOS PARA LAS CONDICIONES DE HOY</span>",
                unsafe_allow_html=True)

    condiciones_str = (
        f"Viento: {safe(v_media,0)}/{safe(v_racha,0)} km/h dirección {deg_to_compass(v_dir)}, "
        f"Oleaje: {safe(ola)} m significativa, "
        f"Corriente: {safe(corr_kmh)} km/h dirección {deg_to_compass(corr_dir)}, "
        f"Marea: {tide_label} ({tide_h}m), "
        f"Temperatura agua: {safe(temp)}°C, "
        f"Presión: {safe(presion,0)} hPa, "
        f"Hora: {ahora.strftime('%H:%M')}, "
        f"Fecha: {fecha_str}"
    )

    if ANTHROPIC_KEY:
        if st.button("🤖 Obtener análisis personalizado para HOY", type="primary"):
            prompt = f"""Eres un experto patrón de pesca del Cantábrico, concretamente de la costa de Mutriku (Gipuzkoa, País Vasco). 
Analiza las siguientes condiciones marítimas actuales y da consejos CONCRETOS y PRÁCTICOS para hoy:

CONDICIONES ACTUALES: {condiciones_str}

Estructura tu respuesta así (en español, tono de marinero experto, informal pero preciso):
1. **DIAGNÓSTICO RÁPIDO** (2-3 frases sobre si es buen día para salir y por qué)
2. **TOP 3 ESPECIES PARA HOY** con razonamiento específico a las condiciones
3. **CONSEJO TÁCTICO DEL DÍA** (un consejo concreto sobre aparejo, zona o técnica adaptada a estas condiciones)
4. **ALERTA O ATENCIÓN** (si hay algo que vigilar: marea, viento, corriente...)

Sé específico con las condiciones dadas. Menciona los nombres en euskera cuando sea relevante (txitxarro, txipiron, legatza...). Respuesta máximo 250 palabras."""

            with st.spinner("Consultando al patrón IA…"):
                respuesta = call_anthropic(prompt, ANTHROPIC_KEY, max_tokens=600)

            if respuesta and not respuesta.startswith("Error"):
                # Formateo básico markdown → HTML
                resp_html = respuesta.replace("\n", "<br>")
                resp_html = resp_html.replace("**", "<b>", 1)
                while "**" in resp_html:
                    resp_html = resp_html.replace("**", "</b>", 1).replace("**", "<b>", 1)
                st.markdown(f"""
                <div class='ai-box'>
                  <div class='ai-content' style='margin-top:8px'>{resp_html}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.error(f"No se pudo obtener el análisis: {respuesta}")
    else:
        st.markdown(f"""
        <div class='ai-box'>
          <div class='ai-content' style='margin-top:8px'>
            <b>Condiciones actuales para el análisis IA:</b><br>
            {condiciones_str}<br><br>
            Para activar el análisis personalizado diario, añade tu clave de Anthropic en
            <code>.streamlit/secrets.toml</code>:<br>
            <code>ANTHROPIC_API_KEY = "sk-ant-..."</code><br><br>
            <em>Sin la clave, usa los tips estáticos de cada especie combinados con las condiciones actuales mostradas arriba.</em>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class='pie'>
      🐟 Tips basados en conocimiento local del Cantábrico Oriental ·
      Análisis IA: Claude Sonnet (Anthropic) · Datos en tiempo real de Open-Meteo
    </div>""", unsafe_allow_html=True)
