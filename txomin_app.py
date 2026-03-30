import streamlit as st
import streamlit.components.v1 as components
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
    page_title="Txomin v2.1 | Mutriku",
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

DIAS_ES  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# ══════════════════════════════════════════════════════════════════════
#  ESTILOS GLOBALES
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;700;900&family=Barlow:wght@400;600;700&display=swap');

* { box-sizing: border-box; }
.stApp { background-color: #F5F6FA; font-family: 'Barlow', sans-serif; color: #1E3A8A; }
footer, #MainMenu, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 3rem; max-width: 1400px; }

.stTabs [data-baseweb="tab-list"] {
    background: #1E3A8A; border-radius: 10px 10px 0 0; padding: 4px 8px 0; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Barlow Condensed', sans-serif; font-weight: 900;
    font-size: 0.85rem; letter-spacing: 2px; text-transform: uppercase;
    color: #93C5FD !important; border-radius: 6px 6px 0 0; padding: 10px 20px;
}
.stTabs [aria-selected="true"] { background: #991B1B !important; color: white !important; }
.stTabs [data-baseweb="tab-panel"] { background: #F5F6FA; border-radius: 0 0 10px 10px; padding: 0; border: none; }

.banner {
    background: linear-gradient(135deg, #7F1D1D 0%, #991B1B 45%, #1E3A8A 100%);
    color: white; text-align: center; padding: 26px 20px 22px; border-radius: 16px;
    margin-bottom: 28px; box-shadow: 0 8px 32px rgba(153,27,27,0.35);
    position: relative; overflow: hidden;
}
.banner::before {
    content: ''; position: absolute; inset: 0;
    background: repeating-linear-gradient(45deg,transparent,transparent 20px,rgba(255,255,255,0.03) 20px,rgba(255,255,255,0.03) 40px);
}
.banner-title { font-family:'Barlow Condensed',sans-serif; font-size:2.1rem; font-weight:900; letter-spacing:6px; text-transform:uppercase; text-shadow:0 2px 8px rgba(0,0,0,0.3); display:block; position:relative; }
.banner-sub   { font-size:0.82rem; font-weight:600; letter-spacing:3px; opacity:0.85; display:block; margin-top:4px; position:relative; }

.sec-title { font-family:'Barlow Condensed',sans-serif; font-size:0.78rem; font-weight:900; text-transform:uppercase; letter-spacing:3px; color:#1E3A8A; border-left:4px solid #991B1B; padding-left:10px; display:block; margin:24px 0 16px; }

.metric-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px; margin-bottom:8px; }
.mbox { background:#FFFFFF; border:1px solid #E2E8F0; border-bottom:4px solid #991B1B; border-radius:14px; padding:20px 14px 16px; text-align:center; box-shadow:0 2px 8px rgba(30,58,138,0.06); transition:transform 0.2s ease,box-shadow 0.2s ease; }
.mbox:hover { transform:translateY(-2px); box-shadow:0 6px 18px rgba(30,58,138,0.12); }
.micon  { font-size:1.7rem; display:block; margin-bottom:6px; }
.mlabel { font-family:'Barlow Condensed',sans-serif; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:#64748B; display:block; margin-bottom:6px; }
.mval   { font-family:'Barlow Condensed',sans-serif; font-size:2.0rem; font-weight:900; color:#1E3A8A; line-height:1.1; display:block; }
.mval-sm{ font-size:1.2rem; }
.msub   { font-size:0.78rem; font-weight:700; color:#991B1B; display:block; margin-top:3px; }
.msub2  { font-size:0.72rem; font-weight:600; color:#64748B; display:block; margin-top:2px; }

.sembox    { border-radius:16px; padding:32px 24px; text-align:center; margin:8px 0 16px; border:2px solid transparent; }
.sem-verde    { background:#F0FDF4; border-color:#10B981; }
.sem-amarillo { background:#FFFBEB; border-color:#F59E0B; }
.sem-rojo     { background:#FEF2F2; border-color:#EF4444; }
.sem-luz { width:76px; height:76px; border-radius:50%; margin:0 auto 16px; position:relative; }
.sem-luz::after { content:''; position:absolute; inset:-6px; border-radius:50%; opacity:0.35; animation:pulse 2s infinite; }
.sem-luz-verde    { background:#10B981; } .sem-luz-verde::after    { background:#10B981; }
.sem-luz-amarillo { background:#F59E0B; } .sem-luz-amarillo::after { background:#F59E0B; }
.sem-luz-rojo     { background:#EF4444; } .sem-luz-rojo::after     { background:#EF4444; }
@keyframes pulse { 0%{transform:scale(1);opacity:0.4;} 50%{transform:scale(1.3);opacity:0.1;} 100%{transform:scale(1);opacity:0.4;} }
.sem-titulo { font-family:'Barlow Condensed',sans-serif; font-size:1.7rem; font-weight:900; letter-spacing:2px; margin-bottom:6px; display:block; }
.sem-sub    { font-size:0.9rem; font-weight:700; margin-bottom:10px; color:#374151; display:block; }
.sem-razones{ font-size:0.84rem; color:#374151; line-height:1.7; }
.sem-verde .sem-titulo    { color:#065F46; }
.sem-amarillo .sem-titulo { color:#92400E; }
.sem-rojo .sem-titulo     { color:#991B1B; }

.alerta { background:#1E3A8A; color:white; padding:14px 18px; border-radius:10px; border-left:7px solid #991B1B; margin:6px 0; font-weight:700; font-size:0.88rem; line-height:1.5; }
.alerta-warn { background:#7F1D1D; }
.alerta-info { background:#1E3A8A; border-left-color:#60A5FA; }
.alerta small { font-weight:400; opacity:0.85; }

.pie { text-align:center; color:#94A3B8; font-size:0.7rem; margin-top:30px; padding-top:14px; border-top:1px solid #E2E8F0; line-height:1.8; }
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
    t=dt.timestamp(); AMP=1.76; PERIOD=44714.0; PHASE=5.4
    h=AMP*math.cos(2*math.pi*t/PERIOD-PHASE)
    h_next=AMP*math.cos(2*math.pi*(t+1800)/PERIOD-PHASE)
    rising=h_next>h; height=round(h+AMP+0.3,2)
    if h>AMP*0.80:    label,emoji="PLEAMAR","🌊"
    elif h<-AMP*0.80: label,emoji="BAJAMAR","🏖️"
    elif rising:       label,emoji="SUBIENDO","↗️"
    else:              label,emoji="BAJANDO","↘️"
    return height,label,emoji,rising

def fish_score(wind_kmh,wave_m,rising,temp,pressure):
    s=0
    def ok(v): return v is not None and not(isinstance(v,float) and math.isnan(v))
    if ok(wind_kmh):
        if wind_kmh<12:  s+=2
        elif wind_kmh<22:s+=1
    if ok(wave_m):
        if wave_m<0.7:   s+=2
        elif wave_m<1.3: s+=1
    if rising: s+=2
    if ok(temp):
        if 14<=temp<=20: s+=2
        elif 11<=temp<=23:s+=1
    if ok(pressure):
        if pressure>1015:s+=2
        elif pressure>1005:s+=1
    return min(s,10)

def score_ui(s):
    if s>=8: return "⭐⭐⭐⭐","EXCELENTE","#065F46"
    if s>=6: return "⭐⭐⭐","BUENA","#1D4ED8"
    if s>=4: return "⭐⭐","MODERADA","#92400E"
    return "⭐","ESCASA","#991B1B"

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
        if v_racha>55 and nivel!="rojo":
            nivel="rojo"; razones.append(f"Racha extrema: {v_racha:.0f} km/h")
        elif v_racha>35 and nivel=="verde":
            nivel="amarillo"; razones.append(f"Racha fuerte: {v_racha:.0f} km/h")
    if ok(ola):
        if ola>2.5 and nivel!="rojo":
            nivel="rojo"; razones.append(f"Oleaje peligroso: {ola:.1f} m")
        elif ola>1.5 and nivel=="verde":
            nivel="amarillo"; razones.append(f"Oleaje elevado: {ola:.1f} m")
    if ok(presion) and presion<995 and nivel=="verde":
        nivel="amarillo"; razones.append(f"Presión muy baja: {presion:.0f} hPa")
    if not razones:
        razones=["✅ Sin alertas activas — condiciones favorables"]
    return nivel,razones


# ══════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=600)
def fetch_meteo():
    errors=[]
    url_w=(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
           f"&hourly=wind_speed_10m,wind_gusts_10m,wind_direction_10m,pressure_msl"
           f"&wind_speed_unit=kmh&timezone=Europe%2FMadrid&forecast_days=2")
    url_m=(f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT}&longitude={LON}"
           f"&hourly=wave_height,wave_period,wave_direction,"
           f"ocean_current_velocity,ocean_current_direction,sea_surface_temperature"
           f"&timezone=Europe%2FMadrid&forecast_days=2")
    try:
        rw=requests.get(url_w,timeout=9); rw.raise_for_status(); dw=rw.json()
    except requests.exceptions.Timeout:
        errors.append("⏱️ Timeout al obtener datos de viento."); return pd.DataFrame(),errors
    except requests.exceptions.HTTPError as e:
        errors.append(f"⛔ Error HTTP (viento): {e}"); return pd.DataFrame(),errors
    except Exception as e:
        errors.append(f"⛔ Error inesperado (viento): {e}"); return pd.DataFrame(),errors
    try:
        rm=requests.get(url_m,timeout=9); rm.raise_for_status(); dm=rm.json()
    except requests.exceptions.Timeout:
        errors.append("⏱️ Timeout al obtener datos marinos."); return pd.DataFrame(),errors
    except requests.exceptions.HTTPError as e:
        errors.append(f"⛔ Error HTTP (marino): {e}"); return pd.DataFrame(),errors
    except Exception as e:
        errors.append(f"⛔ Error inesperado (marino): {e}"); return pd.DataFrame(),errors
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
        errors.append(f"⛔ Error construyendo DataFrame: {e}")
        return pd.DataFrame(),errors

@st.cache_data(ttl=3600)
def fetch_aemet(api_key):
    if not api_key: return [],None
    try:
        headers={"api_key":api_key,"Accept":"application/json"}
        r=requests.get("https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/61",headers=headers,timeout=10)
        r.raise_for_status(); meta=r.json()
        if meta.get("estado")!=200: return[],f"AEMET: {meta.get('descripcion','error desconocido')}"
        r2=requests.get(meta["datos"],headers=headers,timeout=12); r2.raise_for_status()
        root=ET.fromstring(r2.text); ns={'c':'urn:oasis:names:tc:emergency:cap:1.2'}; alerts=[]
        for info in root.findall('.//c:info',ns):
            lang=info.findtext('c:language','',ns)
            if lang and not lang.lower().startswith('es'): continue
            alerts.append({'event':info.findtext('c:event','—',ns),'severity':info.findtext('c:severity','—',ns),
                           'urgency':info.findtext('c:urgency','—',ns),'headline':info.findtext('c:headline','—',ns),
                           'expires':info.findtext('c:expires','—',ns)})
        return alerts,None
    except requests.exceptions.HTTPError as e:
        return[],f"AEMET HTTP {e.response.status_code} — comprueba tu API key"
    except ET.ParseError:
        return[],"AEMET: error al parsear XML CAP"
    except Exception as e:
        return[],f"AEMET no disponible: {e}"


# ══════════════════════════════════════════════════════════════════════
#  BANNER
# ══════════════════════════════════════════════════════════════════════
fecha_str=f"{DIAS_ES[ahora.weekday()]}, {ahora.day} de {MESES_ES[ahora.month-1]} de {ahora.year}"
st.markdown(f"""
<div class='banner'>
    <span class='banner-title'>🔱 TXOMIN — CONTROL TÁCTICO MUTRIKU</span>
    <span class='banner-sub'>{fecha_str} &nbsp;·&nbsp; {ahora.strftime('%H:%M')}</span>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["📡  ESTADO DE LA MAR", "🗺️  CARTA NÁUTICA"])


# ════════════════════════════════════════════════════════════════════
#  TAB 1 — ESTADO DE LA MAR
# ════════════════════════════════════════════════════════════════════
with tab1:
    with st.spinner("Sincronizando datos meteorológicos y marinos…"):
        df, data_errors = fetch_meteo()
        aemet_alerts, aemet_error = fetch_aemet(AEMET_KEY)

    for e in data_errors:
        st.error(e)

    if df.empty:
        st.error("📡 Sin datos disponibles. Comprueba la conexión e intenta de nuevo.")
        st.stop()

    df['_diff']=(df['time']-ahora).abs()
    idx=df['_diff'].idxmin(); now=df.loc[idx]
    df.drop(columns=['_diff'],inplace=True)

    def fv(v):
        try:
            f=float(v); return None if math.isnan(f) else f
        except Exception: return None

    v_media=fv(now['v_media']); v_racha=fv(now['v_racha']); v_dir=fv(now['v_dir'])
    presion=fv(now['presion']); ola=fv(now['ola']); ola_dir=fv(now['ola_dir'])
    corr_vel=fv(now['corr_vel']); corr_dir=fv(now['corr_dir']); temp=fv(now['temp'])

    tide_h,tide_label,tide_emoji,tide_rising=tide_info(ahora)
    score=fish_score(v_media,ola,tide_rising,temp,presion)
    stars,act_label,act_color=score_ui(score)
    ola_max=round(ola*1.8,1) if ola else None
    corr_kmh=round(corr_vel*3.6,1) if corr_vel is not None else None

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
            <span class='msub2'>({safe(corr_vel,2)} m/s)</span>
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
            <span class='msub'>{safe(presion,0)} hPa</span>
            <span class='msub2'>Temperatura superficial</span>
        </div>
        <div class='mbox'>
            <div class='micon'>🐟</div>
            <span class='mlabel'>Actividad Peces</span>
            <span class='mval' style='font-size:1.3rem;line-height:1.4'>{stars}</span>
            <span class='msub' style='color:{act_color}'>{act_label}</span>
            <span class='msub2'>Puntuación: {score}/10</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SCROLL HORARIO ─────────────────────────────────────────────
    st.markdown("<span class='sec-title'>⏱️ PREVISIÓN TÁCTICA — CADA 2 HORAS (hasta las 00:00)</span>",
                unsafe_allow_html=True)
    medianoche=ahora.replace(hour=0,minute=0,second=0,microsecond=0)+timedelta(days=1)
    future=df[(df['time']>ahora)&(df['time']<=medianoche)].copy()
    horas_scroll=future.iloc[::2]

    if horas_scroll.empty:
        st.info("No hay datos de previsión para el resto del día.")
    else:
        cards_html=""
        for _,r in horas_scroll.iterrows():
            _,t_lbl,t_em,_=tide_info(r['time'])
            rv=fv(r['v_media']); rvc=fv(r['v_racha'])
            ro=fv(r['ola']); rc=fv(r['corr_vel'])
            rc_kmh=round(rc*3.6,1) if rc is not None else None
            rt=fv(r['temp']); rd=fv(r['v_dir'])
            cards_html+=f"""
            <div style="flex:0 0 auto;width:136px;background:#F8FAFC;border:1px solid #E2E8F0;
                        border-top:4px solid #1E3A8A;border-radius:10px;padding:11px 9px;
                        text-align:center;font-size:0.78rem;color:#1E3A8A;font-family:sans-serif;">
                <div style="font-size:1.05rem;font-weight:900;color:#991B1B;margin-bottom:8px;">
                    {r['time'].strftime('%H:%M')}</div>
                <div style="padding:2px 0;font-weight:600;">
                    &#127783; <b style="color:#991B1B;">{safe(rv,0)}/{safe(rvc,0)}</b> km/h</div>
                <div style="padding:1px 0;color:#64748B;font-size:0.7rem;">
                    {dir_arrow(rd)} {deg_to_compass(rd)}</div>
                <div style="padding:2px 0;font-weight:600;">
                    &#127754; <b style="color:#991B1B;">{safe(ro)} m</b></div>
                <div style="padding:2px 0;font-weight:600;">
                    &#128256; <b style="color:#991B1B;">{safe(rc_kmh)} km/h</b></div>
                <div style="padding:2px 0;font-weight:600;">
                    {t_em} <b style="color:#991B1B;">{t_lbl}</b></div>
                <div style="padding:2px 0;font-weight:600;">
                    &#127777; <b style="color:#991B1B;">{safe(rt)}°C</b></div>
            </div>
            """
        full_html=f"""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;
                    padding:18px 16px;box-shadow:0 2px 8px rgba(30,58,138,0.05);">
            <div style="display:flex;overflow-x:auto;gap:10px;padding:4px 2px 10px;
                        scrollbar-width:thin;scrollbar-color:#991B1B #F1F5F9;">
                {cards_html}
            </div>
        </div>
        """
        components.html(full_html, height=220, scrolling=False)

    # ── SEMÁFORO ─────────────────────────────────────────────────
    st.markdown("<span class='sec-title'>🚦 SEMÁFORO DE SEGURIDAD MARÍTIMA</span>",
                unsafe_allow_html=True)
    nivel,razones=semaforo(v_racha,ola,presion,aemet_alerts)
    SEM={
        "verde":    {"box":"sem-verde",    "luz":"sem-luz-verde",
                     "titulo":"✅ RECOMENDABLE",    "sub":"CONDICIONES FAVORABLES"},
        "amarillo": {"box":"sem-amarillo", "luz":"sem-luz-amarillo",
                     "titulo":"⚠️ PRECAUCIÓN",      "sub":"SALIR CON PRECAUCIÓN Y EQUIPO COMPLETO"},
        "rojo":     {"box":"sem-rojo",     "luz":"sem-luz-rojo",
                     "titulo":"🚫 NO RECOMENDABLE", "sub":"CONDICIONES ADVERSAS — NO SALIR"},
    }
    s=SEM[nivel]; razones_html="".join(f"<div>• {r}</div>" for r in razones)
    st.markdown(f"""
    <div class='sembox {s["box"]}'>
        <div class='sem-luz {s["luz"]}'></div>
        <span class='sem-titulo'>{s["titulo"]}</span>
        <span class='sem-sub'>{s["sub"]}</span>
        <div class='sem-razones'>{razones_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── ALERTAS AEMET ─────────────────────────────────────────────
    if aemet_alerts:
        st.markdown("<span class='sec-title'>🚨 AVISOS METEOROLÓGICOS AEMET ACTIVOS</span>",
                    unsafe_allow_html=True)
        for a in aemet_alerts:
            sev=a.get("severity","—")
            cls="alerta-warn" if sev in("Extreme","Severe") else "alerta-info"
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

    st.markdown(f"""
    <div class='pie'>
        🔱 TXOMIN v2.1 &nbsp;·&nbsp;
        <b>Open-Meteo</b> (viento · oleaje · corriente) &nbsp;·&nbsp;
        <b>AEMET OpenData</b> (alertas oficiales) &nbsp;·&nbsp;
        <b>Modelo M2</b> (marea estimada ±30 min)<br>
        Última actualización: {ahora.strftime('%H:%M')} &nbsp;·&nbsp; Refresco automático cada 10 min
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  TAB 2 — CARTA NÁUTICA
# ════════════════════════════════════════════════════════════════════
with tab2:

    CHART_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;900&family=Barlow:wght@600;700&display=swap');
  *{margin:0;padding:0;box-sizing:border-box;}
  body{background:#0F172A;font-family:'Barlow',sans-serif;}

  #toolbar{
    background:linear-gradient(90deg,#1E3A8A,#162d6b);
    padding:10px 14px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;
    border-bottom:3px solid #991B1B;
  }
  .t-sep{width:1px;height:28px;background:#2D4E9E;margin:0 4px;}
  .tbtn{
    background:#243E8B;color:#E2E8F0;border:1px solid #3B5EC6;border-radius:6px;
    padding:7px 13px;cursor:pointer;font-family:'Barlow Condensed',sans-serif;
    font-size:0.82rem;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;
    transition:all 0.18s;white-space:nowrap;
  }
  .tbtn:hover{background:#991B1B;border-color:#CC2222;color:white;}
  .tbtn.active{background:#991B1B;border-color:#FF5555;color:white;box-shadow:0 0 8px rgba(153,27,27,0.6);}
  #result-panel{
    background:#0A1628;color:#93C5FD;border:1px solid #1E3A8A;border-radius:6px;
    padding:6px 14px;font-size:0.78rem;font-weight:700;min-width:300px;
    letter-spacing:0.3px;flex:1;max-width:600px;
  }
  #result-panel b{color:#FCD34D;}

  #map{height:640px;width:100%;cursor:default;}

  #legend{
    background:linear-gradient(90deg,#1E3A8A,#162d6b);
    padding:9px 14px;display:flex;gap:18px;align-items:center;flex-wrap:wrap;
    font-size:0.72rem;color:#CBD5E1;font-weight:700;border-top:2px solid #991B1B;
    font-family:'Barlow Condensed',sans-serif;letter-spacing:0.5px;
  }
  .leg-item{display:flex;align-items:center;gap:6px;}
  .leg-dot {width:13px;height:13px;border-radius:50%;flex-shrink:0;border:2px solid rgba(255,255,255,0.3);}
  .leg-line{width:22px;height:5px;border-radius:3px;flex-shrink:0;}
  .leg-src {margin-left:auto;color:#64748B;font-size:0.65rem;}

  .mtip{
    background:#1E3A8A!important;color:#FCD34D!important;
    border:1px solid #991B1B!important;border-radius:4px!important;
    font-weight:900!important;font-size:0.7rem!important;
    padding:2px 6px!important;box-shadow:none!important;
  }
  .mtip::before{display:none!important;}
  .leaflet-popup-content-wrapper{border-radius:10px!important;border:2px solid #1E3A8A!important;box-shadow:0 6px 20px rgba(0,0,0,0.4)!important;}
  .leaflet-popup-tip{background:#1E3A8A!important;}
  .leaflet-control-layers{border:1px solid #1E3A8A!important;border-radius:8px!important;box-shadow:0 4px 12px rgba(0,0,0,0.5)!important;}
  .leaflet-control-layers-expanded{background:#0F172A!important;color:#CBD5E1!important;font-family:'Barlow',sans-serif;font-size:0.8rem;}
  .leaflet-control-scale-line{background:rgba(30,58,138,0.85)!important;color:white!important;border:1px solid #991B1B!important;border-radius:4px!important;font-weight:700!important;}
</style>
</head>
<body>

<div id="toolbar">
  <button class="tbtn" id="btn-measure" onclick="setTool('measure')">&#128207; MEDIR DISTANCIA</button>
  <button class="tbtn" id="btn-bearing" onclick="setTool('bearing')">&#129517; CALCULAR DERROTA</button>
  <button class="tbtn" onclick="clearAll()">&#128465; LIMPIAR</button>
  <div class="t-sep"></div>
  <div id="result-panel">Selecciona una herramienta y haz clic en la carta &nbsp;&#183;&nbsp; doble clic para finalizar medici&#243;n</div>
</div>

<div id="map"></div>

<div id="legend">
  <div class="leg-item"><div class="leg-dot" style="background:#EF4444;"></div> Roca / Bajo</div>
  <div class="leg-item"><div class="leg-dot" style="background:#F59E0B;"></div> Arenal</div>
  <div class="leg-item"><div class="leg-dot" style="background:#10B981;"></div> Puerto</div>
  <div class="leg-item"><div class="leg-line" style="background:#3B82F6;opacity:0.8;"></div> Corriente costera</div>
  <div class="leg-item"><div class="leg-line" style="background:#8B5CF6;opacity:0.8;"></div> Contracorriente</div>
  <div class="leg-item"><div class="leg-line" style="background:#06B6D4;opacity:0.8;"></div> Corriente de marea</div>
  <div class="leg-item"><div class="leg-line" style="background:#FF4444;height:3px;border-top:2px dashed #FF4444;background:none;border-radius:0;"></div> Tramo medido</div>
  <div class="leg-item"><div class="leg-line" style="background:#10B981;height:3px;border-top:2px dashed #10B981;background:none;border-radius:0;"></div> Derrota</div>
  <span class="leg-src">OpenSeaMap &#183; ESRI Ocean &#183; OSM contributors</span>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
// ── MAP ────────────────────────────────────────────────────────────
var map = L.map('map', {
  center:[43.315,-2.38], zoom:12,
  maxBounds:[[43.05,-2.85],[43.62,-1.90]], maxBoundsViscosity:0.85
});
map.options.minZoom=10; map.options.maxZoom=17;

// ── CAPAS BASE ─────────────────────────────────────────────────────
var osmBase  = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {attribution:'© OpenStreetMap', maxZoom:19});
var esriOcean= L.tileLayer(
  'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
  {attribution:'ESRI Ocean', maxZoom:16});
var esriRef  = L.tileLayer(
  'https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{z}/{y}/{x}',
  {attribution:'ESRI Ref', maxZoom:16, opacity:0.9});
var seamark  = L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png',
  {attribution:'© OpenSeaMap', opacity:1.0});

// Por defecto: ESRI Ocean (aspecto de carta náutica) + OpenSeaMap (marcas reales)
esriOcean.addTo(map); esriRef.addTo(map); seamark.addTo(map);

// Control de capas
var osmGrp  = L.layerGroup([osmBase, seamark]);
var esriGrp = L.layerGroup([esriOcean, esriRef, seamark]);
L.control.layers({
  '&#127754; Carta ESRI Ocean + OpenSeaMap': esriGrp,
  '&#128506;  OSM + OpenSeaMap':             osmGrp
}, {}, {position:'topright', collapsed:true}).addTo(map);

// ── ICONOS ─────────────────────────────────────────────────────────
function mkIcon(bg, glyph) {
  return L.divIcon({
    html: '<div style="background:'+bg+';color:white;border-radius:50%;width:28px;height:28px;'+
          'display:flex;align-items:center;justify-content:center;font-size:13px;'+
          'border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.55);">'+glyph+'</div>',
    iconSize:[28,28], iconAnchor:[14,14], popupAnchor:[0,-16], className:''
  });
}
var iRoca  = mkIcon('#DC2626','&#9875;');
var iArena = mkIcon('#D97706','&#128032;');
var iPuerto= mkIcon('#059669','&#9973;');

// ── PUNTOS DE PESCA ────────────────────────────────────────────────
var spots = [
  {lat:43.316,lng:-2.387,name:"Bajo de Mutriku",       type:"rock",depth:"3-8 m",
   desc:"Bajo rocoso frente a la bocana. Fondo mixto roca-arena. Lubina y muxarra."},
  {lat:43.308,lng:-2.372,name:"Bajos de Saturraran",   type:"rock",depth:"6-15 m",
   desc:"Roca frente a la playa de Saturraran. Txitxarro, berdel y faneca en temporada."},
  {lat:43.334,lng:-2.412,name:"Bajo Otoio",            type:"rock",depth:"4-12 m",
   desc:"Media milla al ONO de Mutriku. Zona frecuentada de fondo y curricán."},
  {lat:43.345,lng:-2.450,name:"Bajo Mendexa",          type:"rock",depth:"8-20 m",
   desc:"Entre Mutriku y Lekeitio. Referencia para besugo y congrio."},
  {lat:43.362,lng:-2.477,name:"Bajos de Lekeitio",     type:"rock",depth:"5-22 m",
   desc:"Frente al puerto de Lekeitio. Merluza y besugo en profundidad. Atención a la corriente."},
  {lat:43.298,lng:-2.300,name:"Bajo de Deba",          type:"rock",depth:"4-10 m",
   desc:"Frente a la ría de Deba. Lubina y dorada en verano."},
  {lat:43.316,lng:-2.258,name:"Flysch de Zumaia",      type:"rock",depth:"3-18 m",
   desc:"Zona de acantilado y flysch. Gran diversidad de fondo. Excelente para pesca de roca."},
  {lat:43.323,lng:-2.338,name:"Bajo Ondarroa",         type:"rock",depth:"5-14 m",
   desc:"Frente al puerto de Ondarroa. Zona tradicional de txitxarro y muxarra."},
  {lat:43.283,lng:-2.355,name:"Arenal de Ondarroa",    type:"sand",depth:"15-30 m",
   desc:"Fondo arenoso frente a Ondarroa. Lenguado y rodaballo. Mejor con mar tranquila."},
  {lat:43.272,lng:-2.385,name:"Arenal Mutriku Sur",    type:"sand",depth:"20-40 m",
   desc:"Plataforma arenosa a 3 millas al S. Merluzón y congrio de noche."},
  {lat:43.258,lng:-2.440,name:"Arenal del Lea",        type:"sand",depth:"25-45 m",
   desc:"Entre Lekeitio y Ondarroa. Besugo y palometa en profundidad."},
  {lat:43.265,lng:-2.300,name:"Arenal de Deba",        type:"sand",depth:"18-35 m",
   desc:"Frente a la ría de Deba. Lenguado y salmonete en verano."},
  {lat:43.370,lng:-2.499,name:"Puerto de Lekeitio",    type:"port",depth:"—",
   desc:"Puerto pesquero y deportivo. Lonja activa. Gasoil, agua, avituallamiento. Buen abrigo con S y SO."},
  {lat:43.316,lng:-2.381,name:"Puerto de Mutriku",     type:"port",depth:"—",
   desc:"Puerto deportivo y pesquero. Gasoil disponible. Rampa de varada."},
  {lat:43.303,lng:-2.351,name:"Puerto de Ondarroa",    type:"port",depth:"—",
   desc:"Mayor puerto pesquero de la zona. Lonja con subasta diaria. Grúa disponible."},
  {lat:43.292,lng:-2.258,name:"Puerto de Zumaia",      type:"port",depth:"—",
   desc:"Puerto deportivo junto al flysch. Acceso por ría con corriente en llenante."}
];

spots.forEach(function(s){
  var ic   = s.type==='rock' ? iRoca : (s.type==='sand' ? iArena : iPuerto);
  var tipo = s.type==='rock'  ? '&#128255; Roca / Bajo' :
             s.type==='sand'  ? '&#127958; Arenal'      : '&#9875; Puerto / Abrigo';
  var depHtml = s.depth!=='—'
    ? '<div style="background:#EFF6FF;border-radius:4px;padding:3px 8px;margin-bottom:6px;font-size:0.78rem;font-weight:700;color:#1E3A8A;display:inline-block;">Prof: '+s.depth+'</div>'
    : '';
  L.marker([s.lat,s.lng],{icon:ic})
   .bindPopup(
     '<div style="font-family:sans-serif;min-width:190px;max-width:240px;">'+
     '<div style="font-weight:900;font-size:0.95rem;color:#1E3A8A;margin-bottom:4px;">'+s.name+'</div>'+
     '<div style="color:#991B1B;font-size:0.73rem;font-weight:700;margin-bottom:6px;letter-spacing:1px;text-transform:uppercase;">'+tipo+'</div>'+
     depHtml+
     '<div style="font-size:0.79rem;color:#374151;line-height:1.55;">'+s.desc+'</div></div>',
     {maxWidth:260})
   .addTo(map);
});

// ── CORRIENTES ─────────────────────────────────────────────────────
var currents = [
  {coords:[[43.32,-2.52],[43.27,-2.52],[43.25,-2.36],[43.30,-2.36]],
   name:"Corriente Costera del Cantábrico",dir:"E &#10132; O (Corriente de Labradores)",
   speed:"0.3 – 0.9 kn",note:"Predominante en otoño-invierno. Se intensifica con vientos del ENE.",color:"#3B82F6"},
  {coords:[[43.27,-2.38],[43.21,-2.38],[43.21,-2.24],[43.27,-2.24]],
   name:"Contracorriente de Profundidad",dir:"O &#10132; E (franja 20-80 m)",
   speed:"0.2 – 0.5 kn",note:"Presente en verano-otoño bajo la termoclina. Afecta a palangres de fondo.",color:"#8B5CF6"},
  {coords:[[43.34,-2.42],[43.30,-2.43],[43.29,-2.37],[43.34,-2.36]],
   name:"Corriente de Marea – Mutriku",dir:"Variable con la marea",
   speed:"0.5 – 1.8 kn",note:"Fluye al N en llenante, al S en vaciante. Máxima en cuartos de marea.",color:"#06B6D4"},
  {coords:[[43.37,-2.51],[43.33,-2.52],[43.33,-2.47],[43.37,-2.46]],
   name:"Corriente de Marea – Lekeitio",dir:"Variable con la marea",
   speed:"0.4 – 1.4 kn",note:"Marcada en la bocana. Precaución en mareas vivas con SW.",color:"#06B6D4"}
];

currents.forEach(function(c){
  L.polygon(c.coords,{color:c.color,fillColor:c.color,fillOpacity:0.14,weight:2.5,dashArray:'7,5'})
   .bindPopup(
     '<div style="font-family:sans-serif;min-width:200px;">'+
     '<div style="font-weight:900;font-size:0.9rem;color:#1E3A8A;margin-bottom:5px;">&#127754; '+c.name+'</div>'+
     '<div style="font-size:0.8rem;margin-bottom:3px;"><b>Direcci&#243;n:</b> '+c.dir+'</div>'+
     '<div style="font-size:0.8rem;margin-bottom:3px;"><b>Velocidad:</b> '+c.speed+'</div>'+
     '<div style="font-size:0.77rem;color:#374151;margin-top:5px;">'+c.note+'</div></div>',
     {maxWidth:280})
   .addTo(map);
});

// ── HERRAMIENTAS ───────────────────────────────────────────────────
var tool=null, mPts=[], mLines=[], mMarkers=[], bPts=[], bLine=null, bMarkers=[];

function setTool(t){
  clearAll(); tool=t;
  document.getElementById('btn-measure').classList.toggle('active',t==='measure');
  document.getElementById('btn-bearing').classList.toggle('active',t==='bearing');
  map.getContainer().style.cursor='crosshair';
  setResult(t==='measure'
    ? '&#128207; Haz clic para a&#241;adir puntos de ruta &nbsp;&#183;&nbsp; <b>doble clic</b> para terminar'
    : '&#129517; Haz clic en el punto <b>ORIGEN</b> (A)');
}

function clearAll(){
  mPts=[]; mLines.forEach(function(l){map.removeLayer(l);}); mLines=[];
  mMarkers.forEach(function(m){map.removeLayer(m);}); mMarkers=[];
  if(bLine){map.removeLayer(bLine);bLine=null;}
  bPts=[]; bMarkers.forEach(function(m){map.removeLayer(m);}); bMarkers=[];
  if(!tool){ setResult('Selecciona una herramienta y haz clic en la carta'); map.getContainer().style.cursor=''; }
  else{ setTool(tool); }
}

function setResult(html){ document.getElementById('result-panel').innerHTML=html; }

function distNM(a,b){
  var R=3440.065,dLat=(b.lat-a.lat)*Math.PI/180,dLng=(b.lng-a.lng)*Math.PI/180;
  var la1=a.lat*Math.PI/180,la2=b.lat*Math.PI/180;
  var x=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.sin(dLng/2)*Math.sin(dLng/2)*Math.cos(la1)*Math.cos(la2);
  return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));
}

function bearing(a,b){
  var dLng=(b.lng-a.lng)*Math.PI/180,la1=a.lat*Math.PI/180,la2=b.lat*Math.PI/180;
  var y=Math.sin(dLng)*Math.cos(la2),x=Math.cos(la1)*Math.sin(la2)-Math.sin(la1)*Math.cos(la2)*Math.cos(dLng);
  return(Math.atan2(y,x)*180/Math.PI+360)%360;
}
function compass(d){
  return['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSO','SO','OSO','O','ONO','NO','NNO'][Math.round(d/22.5)%16];
}

function addMark(ll,lbl,col){
  var m=L.circleMarker(ll,{radius:5,color:col||'#991B1B',fillColor:col||'#FF4444',fillOpacity:1,weight:2}).addTo(map);
  if(lbl) m.bindTooltip(lbl,{permanent:true,direction:'top',offset:[0,-7],className:'mtip'});
  return m;
}

map.on('click',function(e){
  if(!tool) return;

  if(tool==='measure'){
    mPts.push(e.latlng); var n=mPts.length;
    mMarkers.push(addMark(e.latlng,String(n)));
    if(n>=2){
      var seg=L.polyline([mPts[n-2],mPts[n-1]],{color:'#FF4444',weight:2.5,dashArray:'9,6',opacity:0.9}).addTo(map);
      mLines.push(seg);
      var mid=L.latLng((mPts[n-2].lat+mPts[n-1].lat)/2,(mPts[n-2].lng+mPts[n-1].lng)/2);
      var sd=distNM(mPts[n-2],mPts[n-1]).toFixed(2);
      var lbl=L.marker(mid,{icon:L.divIcon({html:'<div style="background:#991B1B;color:#FCD34D;padding:2px 5px;border-radius:3px;font-size:0.65rem;font-weight:900;white-space:nowrap;">'+sd+' NM</div>',className:'',iconAnchor:[20,8]})}).addTo(map);
      mMarkers.push(lbl);
    }
    var tot=0; for(var i=1;i<mPts.length;i++) tot+=distNM(mPts[i-1],mPts[i]);
    var last=n>=2?distNM(mPts[n-2],mPts[n-1]).toFixed(2)+' NM':'—';
    setResult('&#128207; Puntos: <b>'+n+'</b> &nbsp;&#183;&nbsp; Tramo: <b>'+last+'</b> &nbsp;&#183;&nbsp; Total: <b>'+tot.toFixed(2)+' NM</b> (<b>'+(tot*1.852).toFixed(1)+' km</b>) &nbsp;&#183;&nbsp; doble clic para finalizar');

  } else if(tool==='bearing'){
    bPts.push(e.latlng);
    var col2=bPts.length===1?'#10B981':'#991B1B', lbl2=bPts.length===1?'A':'B';
    var bm=L.marker(e.latlng,{icon:L.divIcon({html:'<div style="background:'+col2+';color:white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:12px;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.5);">'+lbl2+'</div>',iconSize:[24,24],iconAnchor:[12,12],className:''})}).addTo(map);
    bMarkers.push(bm);

    if(bPts.length===2){
      var A=bPts[0],B=bPts[1];
      if(bLine) map.removeLayer(bLine);
      bLine=L.polyline([A,B],{color:'#10B981',weight:3,dashArray:'10,7',opacity:0.95}).addTo(map);
      var dist=distNM(A,B), brng=bearing(A,B), brec=(brng+180)%360;
      var eta6=(dist/6*60).toFixed(0), eta10=(dist/10*60).toFixed(0);
      setResult('&#129517; Rumbo: <b>'+brng.toFixed(1)+'° ('+compass(brng)+')</b> &nbsp;&#183;&nbsp; Rec&#237;proco: <b>'+brec.toFixed(1)+'°</b> &nbsp;&#183;&nbsp; Distancia: <b>'+dist.toFixed(2)+' NM</b> &nbsp;&#183;&nbsp; ETA@6kn: <b>'+eta6+' min</b> &nbsp; ETA@10kn: <b>'+eta10+' min</b>');
      var mid2=L.latLng((A.lat+B.lat)/2,(A.lng+B.lng)/2);
      var arr=L.marker(mid2,{icon:L.divIcon({html:'<div style="transform:rotate('+brng+'deg);font-size:20px;line-height:1;">&#10148;</div>',className:'',iconAnchor:[10,10]})}).addTo(map);
      bMarkers.push(arr);
      setTimeout(function(){bPts=[];bMarkers.forEach(function(m){map.removeLayer(m);});bMarkers=[];if(bLine){map.removeLayer(bLine);bLine=null;}setResult('&#129517; Haz clic en el punto <b>ORIGEN</b> (A) para una nueva derrota');},4500);
    } else {
      setResult('&#129517; Punto A marcado. Haz clic en el punto <b>DESTINO</b> (B)');
    }
  }
});

map.on('dblclick',function(e){
  if(tool==='measure'&&mPts.length>=2){
    var tot=0; for(var i=1;i<mPts.length;i++) tot+=distNM(mPts[i-1],mPts[i]);
    setResult('&#9989; Ruta finalizada: <b>'+mPts.length+'</b> puntos &nbsp;&#183;&nbsp; Total: <b>'+tot.toFixed(2)+' NM</b> (<b>'+(tot*1.852).toFixed(1)+' km</b>)');
    tool=null; document.getElementById('btn-measure').classList.remove('active');
    map.getContainer().style.cursor='';
  }
});

L.control.scale({position:'bottomleft',metric:true,imperial:false,maxWidth:160}).addTo(map);

var cc=L.control({position:'bottomright'});
cc.onAdd=function(){
  this._div=L.DomUtil.create('div','');
  this._div.style.cssText='background:rgba(15,23,42,0.88);color:#93C5FD;padding:5px 11px;border-radius:6px;font-size:0.72rem;font-weight:700;font-family:monospace;border:1px solid #1E3A8A;letter-spacing:0.5px;';
  this._div.innerHTML='&#8212; N &nbsp; &#8212; O';
  return this._div;
};
cc.addTo(map);
map.on('mousemove',function(e){
  cc._div.innerHTML=e.latlng.lat.toFixed(5)+'&#176; N &nbsp; '+Math.abs(e.latlng.lng).toFixed(5)+'&#176; O';
});
</script>
</body>
</html>"""

    components.html(CHART_HTML, height=800, scrolling=False)

    st.markdown("""
    <div class='pie' style='margin-top:10px;'>
        &#128506; Carta N&#225;utica &nbsp;&#183;&nbsp;
        <b>OpenSeaMap</b> (marcas n&#225;uticas reales: sondas, rocas, boyas) &nbsp;&#183;&nbsp;
        <b>ESRI Ocean</b> (fondo cartogr&#225;fico) &nbsp;&#183;&nbsp;
        Puntos de pesca basados en conocimiento local de la costa de Mutriku &nbsp;&#183;&nbsp;
        Corrientes: modelo emp&#237;rico Cant&#225;brico
    </div>
    """, unsafe_allow_html=True)
