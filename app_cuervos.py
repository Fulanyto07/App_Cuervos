import streamlit as st
import pandas as pd
from supabase import create_client, Client
from PIL import Image
import io
import os


# Intentar cargar las librerías de reportes
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# =============================================================================
# CAPA VISUAL (estilo vidrio, tipografía y bloques HTML).
# =============================================================================
import base64
import html

ACENTO = "#0A6CDB"
VERDE = "#30D158"
AMARILLO = "#FFD60A"
ROJO = "#FF8A84"
ROJO_FUERTE = "#FF6961"
FASES_LIGUILLA = ["Cuartos", "Semifinal", "Final"]
NOMBRE_FASE = {
    "Regular": "Fase regular",
    "Pregunta": "Fase regular",
    "Cuartos": "Cuartos",
    "Semifinal": "Semifinal",
    "Final": "Final",
    "Campeon": "Campeón",
    "Eliminado": "Eliminado",
}


# ---------------------------------------------------------------------------
# Compatibilidad entre versiones de Streamlit
# ---------------------------------------------------------------------------
def _version():
    try:
        partes = st.__version__.split(".")
        return int(partes[0]), int(partes[1])
    except Exception:
        return (1, 40)


_NUEVO_ANCHO = _version() >= (1, 50)


def ancho_completo():
    """kwargs para que un botón/tabla ocupe todo el ancho, sin avisos de deprecación."""
    return {"width": "stretch"} if _NUEVO_ANCHO else {"use_container_width": True}


def panel(clave):
    """Contenedor con estilo de vidrio. Usa key= (CSS por clase) y si no existe, borde."""
    try:
        return st.container(key=f"cvpanel_{clave}")
    except TypeError:
        return st.container(border=True)


def bloque(clave):
    """Contenedor con clave CSS pero sin estilo de panel (p. ej. zona de peligro)."""
    try:
        return st.container(key=clave)
    except TypeError:
        return st.container()


def selector(etiqueta, opciones, key, default=None, oculto=False):
    """Control segmentado (Streamlit >= 1.40) con respaldo a radio horizontal."""
    vis = "collapsed" if oculto else "visible"
    if hasattr(st, "segmented_control"):
        return st.segmented_control(etiqueta, opciones, default=default, key=key, label_visibility=vis)
    idx = opciones.index(default) if default in opciones else None
    return st.radio(etiqueta, opciones, index=idx, horizontal=True, key=key, label_visibility=vis)


def icono_pagina(ruta, respaldo="🐦‍⬛"):
    if os.path.exists(ruta):
        try:
            from PIL import Image
            return Image.open(ruta)
        except Exception:
            pass
    return respaldo


def _html(contenido):
    # Una sola línea: el markdown de Streamlit corta bloques HTML en líneas vacías.
    st.markdown(contenido, unsafe_allow_html=True)


def _e(texto):
    return html.escape(str(texto))


# ---------------------------------------------------------------------------
# CSS global
# ---------------------------------------------------------------------------
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');
:root{
  --cv-bg:#0A0B0D; --cv-text:#F2F2F4; --cv-muted:#A1A1AA; --cv-faint:#8A8D96;
  --cv-accent:#0A6CDB; --cv-win:#30D158; --cv-draw:#FFD60A; --cv-loss:#FF8A84;
  --cv-glass:rgba(26,28,34,.50); --cv-line:rgba(255,255,255,.10);
  --cv-blur:blur(28px) saturate(160%);
  --cv-shadow:inset 0 1px 0 rgba(255,255,255,.08), 0 24px 60px rgba(0,0,0,.35);
  --cv-mono:'Geist Mono', ui-monospace, monospace;
}
html, body, .stApp, [data-testid="stAppViewContainer"], .stMarkdown, button, input, textarea, select{
  font-family:'Geist', system-ui, -apple-system, sans-serif;
}
.stApp{
  background:
    radial-gradient(circle 520px at 4% 0%, rgba(70,110,170,.34), rgba(70,110,170,0) 100%),
    radial-gradient(circle 460px at 100% 48%, rgba(150,60,60,.20), rgba(150,60,60,0) 100%),
    radial-gradient(circle 420px at 52% 104%, rgba(90,140,150,.18), rgba(90,140,150,0) 100%),
    #0A0B0D;
  background-attachment:fixed;
  color:var(--cv-text);
}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stMainBlockContainer"], .main .block-container{padding-top:2rem; max-width:1440px;}

/* ---------- Barra lateral de vidrio ---------- */
section[data-testid="stSidebar"]{background:transparent !important; border-right:0 !important;}
[data-testid="stSidebarContent"]{
  background:var(--cv-glass); backdrop-filter:var(--cv-blur); -webkit-backdrop-filter:var(--cv-blur);
  border:1px solid var(--cv-line); border-radius:22px; box-shadow:var(--cv-shadow);
  margin:12px 0 12px 12px; height:calc(100% - 24px);
}

/* ---------- Paneles ---------- */
[class*="st-key-cvpanel_"]{
  background:var(--cv-glass); backdrop-filter:var(--cv-blur); -webkit-backdrop-filter:var(--cv-blur);
  border:1px solid var(--cv-line) !important; border-radius:22px; box-shadow:var(--cv-shadow);
}
[class*="st-key-cvpanel_"]{padding:22px 24px; gap:14px;}
.cv-glass{
  background:var(--cv-glass); backdrop-filter:var(--cv-blur); -webkit-backdrop-filter:var(--cv-blur);
  border:1px solid var(--cv-line); border-radius:22px; box-shadow:var(--cv-shadow);
}

/* ---------- Tipografía y etiquetas ---------- */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label{color:var(--cv-muted) !important; font-size:13px !important;}
[data-testid="stCaptionContainer"]{color:var(--cv-faint);}

/* ---------- Botones ---------- */
.stButton button, .stDownloadButton button, [data-testid="stFileUploader"] button{
  border-radius:12px; min-height:44px; font-weight:500; transition:transform .12s ease, filter .12s ease, background .12s ease;
}
.stButton button:active, .stDownloadButton button:active{transform:scale(.98);}
button[kind="primary"], [data-testid="stBaseButton-primary"]{
  background:var(--cv-accent) !important; border:0 !important; color:#FFFFFF !important; font-weight:600;
}
button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{filter:brightness(1.08);}
button[kind="primary"]:disabled, [data-testid="stBaseButton-primary"]:disabled{opacity:.45; filter:none;}
button[kind="secondary"], [data-testid="stBaseButton-secondary"]{
  background:rgba(255,255,255,.05) !important; border:1px solid rgba(255,255,255,.14) !important; color:#E4E4E7 !important;
}
button[kind="secondary"]:hover, [data-testid="stBaseButton-secondary"]:hover{background:rgba(255,255,255,.10) !important;}
.st-key-cv_danger button{color:var(--cv-loss) !important; border-color:rgba(255,105,97,.35) !important; background:transparent !important;}
.st-key-cv_danger{border-top:1px solid rgba(255,255,255,.08); padding-top:16px; margin-top:8px;}

/* ---------- Campos ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"]{
  background:rgba(0,0,0,.25) !important; border-radius:12px !important; border-color:rgba(255,255,255,.14) !important;
}
[data-baseweb="input"] input, [data-baseweb="select"] input{background:transparent !important;}
.st-key-cv_marcador [data-testid="stNumberInput"] input{font-family:var(--cv-mono); font-size:30px; font-weight:600; text-align:center; height:58px;}
[data-testid="stNumberInput"] button{border-radius:10px;}
.st-key-cv_marcador [data-testid="InputInstructions"]{display:none !important;}
input:disabled{color:var(--cv-muted) !important; -webkit-text-fill-color:var(--cv-muted) !important;}

/* ---------- Pestañas tipo píldora ---------- */
.stTabs [data-baseweb="tab-list"]{gap:4px; background:rgba(255,255,255,.07); padding:3px; border-radius:999px; width:fit-content;}
.stTabs [data-baseweb="tab"]{height:36px; padding:0 16px; border-radius:999px; background:transparent; color:var(--cv-muted);}
.stTabs [data-baseweb="tab"][aria-selected="true"]{background:rgba(255,255,255,.16); color:#FFFFFF;}
.stTabs [data-baseweb="tab"] p{font-size:13px; font-weight:500;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{display:none;}

/* ---------- Expander, tablas, alertas ---------- */
[data-testid="stExpander"] details{border-radius:12px; border:1px solid rgba(255,255,255,.10); background:rgba(255,255,255,.03);}
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"]{border-radius:14px; overflow:hidden; border:1px solid rgba(255,255,255,.08);}
[data-testid="stAlert"]{border-radius:14px;}

/* ---------- Bloques HTML propios ---------- */
.cv-brand{display:flex; align-items:center; gap:14px; margin:4px 0 22px;}
.cv-brand img{width:52px; height:auto;}
.cv-brand-ph{width:52px; height:52px; border-radius:14px; border:1px dashed rgba(255,255,255,.25); display:flex; align-items:center; justify-content:center; font-size:11px; color:var(--cv-muted);}
.cv-brand-name{display:block; font-weight:600; font-size:18px; letter-spacing:-.01em; color:var(--cv-text);}
.cv-brand-sub{display:block; color:var(--cv-muted); font-size:13px;}
.cv-lbl{color:var(--cv-muted); font-size:13px;}
.cv-steps{display:flex; flex-direction:column; gap:4px; margin:10px 0 18px;}
.cv-step{display:flex; align-items:center; gap:12px; padding:8px 10px; border-radius:12px; font-size:14px; color:var(--cv-faint);}
.cv-step.is-done{color:#C4C4CC;}
.cv-step.is-cur{background:rgba(255,255,255,.08); color:var(--cv-text); font-weight:600;}
.cv-dot{width:10px; height:10px; border-radius:50%; flex-shrink:0; border:1.5px solid rgba(255,255,255,.28); background:transparent;}
.cv-step.is-done .cv-dot{border-color:rgba(255,255,255,.55); background:rgba(255,255,255,.55);}
.cv-step.is-cur .cv-dot{border-color:var(--c); background:var(--c);}

.cv-head{padding:4px 4px 18px;}
.cv-title{margin:0; font-size:40px; line-height:1.1; font-weight:600; letter-spacing:-.025em; color:var(--cv-text);}
.cv-sub{margin:6px 0 0; color:var(--cv-muted); font-size:15px;}

.cv-hero{padding:26px; display:flex; flex-wrap:wrap; gap:28px 36px; margin-bottom:20px;}
.cv-hero-pts{flex:1 1 180px; display:flex; flex-direction:column; justify-content:space-between; gap:12px;}
.cv-big{font-family:var(--cv-mono); font-size:72px; line-height:1; font-weight:600; letter-spacing:-.04em; color:var(--cv-text);}
.cv-unit{color:var(--cv-muted); font-size:15px; margin-left:8px;}
.cv-hero-rec{flex:2 1 320px; display:flex; flex-direction:column; gap:16px; justify-content:center;}
.cv-bar{display:flex; height:12px; border-radius:999px; overflow:hidden; gap:3px; background:transparent;}
.cv-bar span{display:block; height:100%;}
.cv-legend{display:flex; flex-wrap:wrap; gap:8px 22px; font-size:14px; color:var(--cv-text);}
.cv-legend i{display:inline-block; width:8px; height:8px; border-radius:2px; margin-right:8px; vertical-align:middle;}
.cv-streak{display:flex; align-items:center; gap:12px; flex-wrap:wrap;}
.cv-chips{display:flex; gap:6px;}
.cv-chip{width:28px; height:28px; border-radius:8px; display:inline-flex; align-items:center; justify-content:center; font:600 13px var(--cv-mono);}
.cv-hero-grid{flex:1 1 240px; display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:18px 24px; align-content:center;}
.cv-num{display:block; font:600 28px var(--cv-mono); color:var(--cv-text);}

.cv-h2{margin:0; font-size:20px; font-weight:600; letter-spacing:-.01em; color:var(--cv-text);}
.cv-preview{display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 16px; border-radius:14px; font-size:14px; font-weight:500;}
.cv-preview b{font:600 15px var(--cv-mono);}

.cv-status{padding:26px; display:flex; flex-wrap:wrap; align-items:center; gap:18px 26px; margin-bottom:20px;}
.cv-status-ico{width:64px; height:64px; border-radius:18px; display:flex; align-items:center; justify-content:center; flex-shrink:0;}
.cv-status-t{display:block; font-size:26px; font-weight:600; letter-spacing:-.02em; color:var(--cv-text);}
.cv-status-s{display:block; font-size:15px; color:var(--cv-muted);}
.cv-path{flex:1 1 100%; display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:10px; margin-top:6px;}
.cv-path-bar{height:6px; border-radius:999px; margin-bottom:12px;}
.cv-path b{display:block; font-size:14px;}
.cv-path small{display:block; font-size:13px;}
.cv-empty{text-align:center; padding:36px 12px; color:var(--cv-muted); font-size:14px;}
.cv-empty b{display:block; color:var(--cv-text); font-size:16px; margin-bottom:6px;}

@media (max-width: 640px){
  .cv-title{font-size:30px;}
  .cv-big{font-size:56px;}
  .cv-path{grid-template-columns:repeat(2, minmax(0,1fr));}
}
@media (prefers-reduced-transparency: reduce){
  [data-testid="stSidebarContent"], [class*="st-key-cvpanel_"], .cv-glass{
    backdrop-filter:none !important; -webkit-backdrop-filter:none !important; background:#16181D !important;
  }
}
@media (prefers-reduced-motion: reduce){
  .stButton button, .stDownloadButton button{transition:none;}
}
"""


def aplicar_estilo():
    css = "\n".join(l for l in CSS.splitlines() if l.strip())
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Utilidades de resultados
# ---------------------------------------------------------------------------
def _gana(res):
    r = str(res)
    return "Victoria" in r or "G-SO" in r


def _pierde(res):
    r = str(res)
    return "Derrota" in r or "P-SO" in r


def _letra(res):
    r = str(res)
    if "Victoria" in r:
        return "V", VERDE, "rgba(48,209,88,.13)"
    if "Empate" in r:
        return "E", AMARILLO, "rgba(255,214,10,.12)"
    if "Derrota" in r:
        return "D", ROJO, "rgba(255,69,58,.14)"
    return "-", "#C4C4CC", "rgba(255,255,255,.08)"


def _filas_liguilla(df):
    if df is None or df.empty or "Fase" not in df.columns:
        return pd.DataFrame(columns=["Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado"])
    return df[df["Fase"].isin(FASES_LIGUILLA)]


def _marcador(fila):
    def n(v):
        try:
            return int(float(v))
        except Exception:
            return 0
    return f"{n(fila.get('Goles a Favor', 0))} : {n(fila.get('Goles en Contra', 0))}"


def camino_liguilla(estado, df):
    """Estado de cada ronda: won / lost / current / todo."""
    lig = _filas_liguilla(df)
    res = {}
    for f in FASES_LIGUILLA:
        filas = lig[lig["Fase"] == f]
        if not filas.empty and _gana(filas.iloc[-1]["Resultado"]):
            res[f] = "won"
        elif not filas.empty and _pierde(filas.iloc[-1]["Resultado"]):
            res[f] = "lost"
        elif estado == f:
            res[f] = "current"
        else:
            res[f] = "todo"
    return res


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
def bloque_marca(ruta_escudo):
    if os.path.exists(ruta_escudo):
        with open(ruta_escudo, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        img = f'<img src="data:image/png;base64,{b64}" alt="Logo de La Peste Negra">'
    else:
        img = '<div class="cv-brand-ph">Logo</div>'
    _html(f'<div class="cv-brand">{img}<div><span class="cv-brand-name">Cuervos</span><span class="cv-brand-sub">La Peste Negra</span></div></div>')


def pasos_fase(estado, df):
    """Recorrido vertical Regular > Cuartos > Semifinal > Final > Campeón."""
    orden = ["Regular", "Cuartos", "Semifinal", "Final", "Campeon"]
    camino = camino_liguilla(estado, df)
    perdida = next((f for f in FASES_LIGUILLA if camino[f] == "lost"), None)

    if estado in ("Regular", "Pregunta"):
        actual, color = 0, ACENTO
    elif estado in FASES_LIGUILLA:
        actual, color = orden.index(estado), ACENTO
    elif estado == "Campeon":
        actual, color = 4, AMARILLO
    else:  # Eliminado
        actual, color = (orden.index(perdida) if perdida else 0), ROJO_FUERTE

    filas = []
    for i, f in enumerate(orden):
        nombre = NOMBRE_FASE[f]
        if i == actual:
            clase = "cv-step is-cur"
            if estado == "Eliminado":
                nombre += ", eliminados" if perdida else ", no clasificaron"
            elif estado == "Pregunta":
                nombre += ", cerrada"
        elif i < actual:
            clase = "cv-step is-done"
        else:
            clase = "cv-step"
        filas.append(f'<div class="{clase}" style="--c:{color}"><span class="cv-dot"></span><span>{_e(nombre)}</span></div>')
    _html('<div class="cv-lbl">Fase actual</div><div class="cv-steps">' + "".join(filas) + "</div>")


# ---------------------------------------------------------------------------
# Contenido principal
# ---------------------------------------------------------------------------
def encabezado(titulo, subtitulo):
    _html(f'<div class="cv-head"><div class="cv-title" role="heading" aria-level="1">{_e(titulo)}</div><p class="cv-sub">{_e(subtitulo)}</p></div>')


def titulo_panel(texto):
    _html(f'<div class="cv-h2" role="heading" aria-level="2">{_e(texto)}</div>')


def panel_resumen(stats, df_jugados, pendientes=0):
    jj, jg, je, jp = stats["JJ"], stats["JG"], stats["JE"], stats["JP"]
    gf, gc, pts = stats["GF"], stats["GC"], stats["PTS"]
    dif = gf - gc
    dif_txt = f"+{dif}" if dif > 0 else str(dif)
    dif_color = VERDE if dif > 0 else (ROJO if dif < 0 else "var(--cv-text)")
    # Rendimiento: puntos obtenidos sobre los posibles (3 por partido jugado)
    rend = f"{round(pts / (jj * 3) * 100)}%" if jj else "-"

    if jj:
        barra = (
            f'<span style="width:{jg / jj * 100:.1f}%;background:{VERDE}"></span>'
            f'<span style="width:{je / jj * 100:.1f}%;background:{AMARILLO}"></span>'
            f'<span style="width:{jp / jj * 100:.1f}%;background:{ROJO_FUERTE}"></span>'
        )
    else:
        barra = '<span style="width:100%;background:rgba(255,255,255,.08)"></span>'

    chips = ""
    if df_jugados is not None and not df_jugados.empty:
        dj = df_jugados.copy()
        dj["_j"] = pd.to_numeric(dj["Jornada"], errors="coerce")
        dj = dj.sort_values("_j", kind="stable").tail(5)
        for r in dj["Resultado"]:
            l, fg, bg = _letra(r)
            chips += f'<span class="cv-chip" style="color:{fg};background:{bg}">{l}</span>'
    if not chips:
        chips = '<span class="cv-lbl">Sin partidos jugados</span>'

    detalle = f"{jj} jugados" + (f", {pendientes} pendiente" + ("s" if pendientes != 1 else "") if pendientes else "")

    _html(
        '<div class="cv-glass cv-hero">'
        f'<div class="cv-hero-pts"><span class="cv-lbl">Puntos</span><div><span class="cv-big">{pts}</span><span class="cv-unit">pts</span></div><span class="cv-lbl">{_e(detalle)}</span></div>'
        f'<div class="cv-hero-rec"><div class="cv-bar">{barra}</div>'
        f'<div class="cv-legend"><span><i style="background:{VERDE}"></i>{jg} ganados</span><span><i style="background:{AMARILLO}"></i>{je} empatados</span><span><i style="background:{ROJO_FUERTE}"></i>{jp} perdidos</span></div>'
        f'<div class="cv-streak"><span class="cv-lbl">Últimos 5</span><div class="cv-chips">{chips}</div></div></div>'
        '<div class="cv-hero-grid">'
        f'<div><span class="cv-lbl">Goles a favor</span><span class="cv-num">{gf}</span></div>'
        f'<div><span class="cv-lbl">Goles en contra</span><span class="cv-num">{gc}</span></div>'
        f'<div><span class="cv-lbl">Diferencia</span><span class="cv-num" style="color:{dif_color}">{dif_txt}</span></div>'
        f'<div><span class="cv-lbl">Rendimiento</span><span class="cv-num">{rend}</span><span class="cv-lbl">{pts} de {jj * 3} pts</span></div>'
        "</div></div>"
    )


def vista_previa(gf, gc, ganador_so, pendiente=False):
    """Muestra qué se va a guardar. Devuelve True si ya se puede guardar."""
    listo = True
    if pendiente:
        txt, pts, fg, bg = "Se guardará como pendiente", "0 pts", "#D4D4D8", "rgba(255,255,255,.06)"
    elif gf > gc:
        txt, pts, fg, bg = "Victoria", "+3 pts", VERDE, "rgba(48,209,88,.12)"
    elif gf < gc:
        txt, pts, fg, bg = "Derrota", "0 pts", ROJO, "rgba(255,69,58,.13)"
    elif ganador_so == "Cuervos":
        txt, pts, fg, bg = "Empate, Cuervos ganan el shootout", "+2 pts", AMARILLO, "rgba(255,214,10,.11)"
    elif ganador_so == "Rival":
        txt, pts, fg, bg = "Empate, el rival gana el shootout", "+1 pt", AMARILLO, "rgba(255,214,10,.11)"
    else:
        txt, pts, fg, bg = "Elige al ganador del shootout", "-", "#A1A1AA", "rgba(255,255,255,.05)"
        listo = False
    _html(f'<div class="cv-preview" style="color:{fg};background:{bg}"><span>{_e(txt)}</span><b>{pts}</b></div>')
    return listo


def vista_previa_liguilla(gf, gc, ganador_so, fase):
    """En liguilla no hay puntos: se muestra si avanzan o quedan eliminados."""
    siguiente = {"Cuartos": "pasan a semifinal", "Semifinal": "pasan a la final", "Final": "son campeones"}[fase]
    listo = True
    if gf > gc or (gf == gc and ganador_so == "Cuervos"):
        txt = ("Victoria" if gf > gc else "Empate, ganan el shootout") + f": {siguiente}"
        fg, bg = VERDE, "rgba(48,209,88,.12)"
    elif gf < gc or ganador_so == "Rival":
        txt = ("Derrota" if gf < gc else "Empate, pierden el shootout") + ": quedan eliminados"
        fg, bg = ROJO, "rgba(255,69,58,.13)"
    else:
        txt, fg, bg = "Elige al ganador del shootout", "#A1A1AA", "rgba(255,255,255,.05)"
        listo = False
    _html(f'<div class="cv-preview" style="color:{fg};background:{bg}"><span>{_e(txt)}</span></div>')
    return listo


_ICO_TROFEO = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 4h8v5a4 4 0 0 1-8 0V4z"></path><path d="M8 6H5a3 3 0 0 0 3 4"></path><path d="M16 6h3a3 3 0 0 1-3 4"></path><path d="M12 13v4"></path><path d="M8 20h8"></path></svg>'
_ICO_X = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12"></path><path d="M18 6L6 18"></path></svg>'
_ICO_FLECHA = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"></path><path d="M13 6l6 6-6 6"></path></svg>'
_RONDA = {"Cuartos": "cuartos de final", "Semifinal": "semifinal", "Final": "la final"}


def panel_liguilla(estado, df):
    """Tarjeta de estado + camino al título. Para liguilla activa, eliminado o campeón."""
    lig = _filas_liguilla(df)
    camino = camino_liguilla(estado, df)

    def ultima(fase):
        filas = lig[lig["Fase"] == fase]
        return filas.iloc[-1] if not filas.empty else None

    if estado == "Campeon":
        fila = ultima("Final")
        titulo = "Campeones"
        sub = f"Ganaron la final {_marcador(fila)} contra {fila['Equipo Rival']}" if fila is not None else "Ganaron la liguilla"
        ico, fg, bg = _ICO_TROFEO, AMARILLO, "rgba(255,214,10,.14)"
    elif estado == "Eliminado":
        perdida = next((f for f in FASES_LIGUILLA if camino[f] == "lost"), None)
        if perdida:
            fila = ultima(perdida)
            titulo = f"Eliminados en {_RONDA[perdida]}"
            if "P-SO" in str(fila["Resultado"]):
                sub = f"Empate {_marcador(fila)} y shootout perdido contra {fila['Equipo Rival']}"
            else:
                sub = f"Cayeron {_marcador(fila)} contra {fila['Equipo Rival']}"
        else:
            titulo, sub = "Temporada terminada", "No clasificaron a la liguilla"
        ico, fg, bg = _ICO_X, ROJO, "rgba(255,69,58,.14)"
    else:
        ganadas = [f for f in FASES_LIGUILLA if camino[f] == "won"]
        titulo = f"{NOMBRE_FASE.get(estado, estado)} en juego"
        if ganadas:
            fila = ultima(ganadas[-1])
            sub = f"Pasaron {_RONDA[ganadas[-1]]} {_marcador(fila)} contra {fila['Equipo Rival']}"
        else:
            sub = "Clasificaron a la liguilla"
        ico, fg, bg = _ICO_FLECHA, "#F2F2F4", "rgba(255,255,255,.08)"

    etiquetas = {"won": ("Ganado", VERDE, VERDE), "lost": ("Eliminados aquí", ROJO_FUERTE, ROJO),
                 "current": ("Por jugar", ACENTO, "#A1A1AA"), "todo": ("Sin jugar", "rgba(255,255,255,.10)", "#A1A1AA")}
    pasos = ""
    for f in FASES_LIGUILLA:
        txt, barra, color = etiquetas[camino[f]]
        tcolor = "var(--cv-faint)" if camino[f] == "todo" else "var(--cv-text)"
        pasos += f'<div><div class="cv-path-bar" style="background:{barra}"></div><b style="color:{tcolor}">{_e(NOMBRE_FASE[f])}</b><small style="color:{color}">{txt}</small></div>'
    if estado == "Campeon":
        pasos += f'<div><div class="cv-path-bar" style="background:{AMARILLO}"></div><b>Campeón</b><small style="color:{AMARILLO}">Título</small></div>'
    else:
        pasos += '<div><div class="cv-path-bar" style="background:rgba(255,255,255,.10)"></div><b style="color:var(--cv-faint)">Campeón</b><small style="color:#A1A1AA">Sin jugar</small></div>'

    _html(
        '<div class="cv-glass cv-status">'
        f'<div class="cv-status-ico" style="color:{fg};background:{bg}">{ico}</div>'
        f'<div style="flex:1 1 280px"><span class="cv-status-t">{_e(titulo)}</span><span class="cv-status-s">{_e(sub)}</span></div>'
        f'<div class="cv-path">{pasos}</div>'
        "</div>"
    )


def vacio(titulo, texto):
    _html(f'<div class="cv-empty"><b>{_e(titulo)}</b>{_e(texto)}</div>')

# =============================================================================
# APLICACIÓN
# =============================================================================

LOGO_PATH = "cuervos_logo.png"

# 1. Configuración de la página
st.set_page_config(page_title="Gestor Cuervos Cloud", page_icon=icono_pagina(LOGO_PATH), layout="wide")
aplicar_estilo()

# 2. Conexión a Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# 3. Control de Sesión
if 'contador_form' not in st.session_state:
    st.session_state.contador_form = 0
if 'estado_torneo' not in st.session_state:
    st.session_state.estado_torneo = "Regular"
if 'temporada_terminada' not in st.session_state:
    st.session_state.temporada_terminada = False
if 'preguntar_clasificacion' not in st.session_state:
    st.session_state.preguntar_clasificacion = False
if 'clasifico_liguilla' not in st.session_state:
    st.session_state.clasifico_liguilla = False
if 'override_cierre' not in st.session_state:
    st.session_state.override_cierre = False

def limpiar_formulario():
    st.session_state.contador_form += 1

# 4. Funciones de Datos
def cargar_datos():
    try:
        response = supabase.table("resultados").select("*").order("id").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=["id", "Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])
    except:
        return pd.DataFrame(columns=["id", "Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])

def guardar_correcciones(df_original, df_modificado):
    df_modificado = df_modificado.dropna(subset=['Equipo Rival'])
    ids_orig = set(df_original['id'].dropna())

    ids_mod = []
    for val in df_modificado['id']:
        if pd.notna(val) and not isinstance(val, str):
            ids_mod.append(val)
    ids_mod = set(ids_mod)
    ids_a_borrar = ids_orig - ids_mod

    try:
        for id_b in ids_a_borrar:
            supabase.table("resultados").delete().eq("id", id_b).execute()

        records = []
        for _, row in df_modificado.iterrows():
            rec = row.to_dict()
            id_val = rec.get('id')
            if pd.isna(id_val) or isinstance(id_val, str):
                rec.pop('id', None)
            else:
                rec['id'] = int(id_val)

            clean_rec = {}
            for k, v in rec.items():
                if pd.isna(v): clean_rec[k] = None
                else: clean_rec[k] = v
            records.append(clean_rec)

        if records:
            supabase.table("resultados").upsert(records).execute()

        st.cache_data.clear()
        st.success("Base de datos actualizada con éxito.", icon=":material/check_circle:")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

def reiniciar_sistema():
    try:
        supabase.table("resultados").delete().neq("id", 0).execute()
        st.session_state.update({
            "estado_torneo": "Regular",
            "temporada_terminada": False,
            "clasifico_liguilla": False,
            "preguntar_clasificacion": False,
            "override_cierre": False
        })
        limpiar_formulario()
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Error al reiniciar: {e}")

# 5. Lógica Deportiva
def procesar_marcador(favor, contra, so_ganador):
    if favor > contra: return 3, "Victoria"
    elif favor < contra: return 0, "Derrota"
    else: return (2, "Empate (G-SO)") if so_ganador == "Cuervos" else (1, "Empate (P-SO)")

def obtener_icono(res):
    if pd.isna(res): return ""
    res_s = str(res)
    if "Victoria" in res_s: return "✅ " + res_s
    if "Empate" in res_s: return "➖ " + res_s
    if "Pendiente" in res_s: return "⏳ " + res_s
    return "❌ " + res_s

def limpiar_icono(res):
    if pd.isna(res): return ""
    return str(res).replace("✅ ", "").replace("➖ ", "").replace("❌ ", "").replace("⏳ ", "")

def generar_excel(df_reg, stats):
    output = io.BytesIO()
    df_reg = df_reg.drop(columns=["Fase", "id"], errors="ignore")
    df_stats = pd.DataFrame([stats])
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_stats.to_excel(writer, index=False, sheet_name='Fase Regular', startrow=0)
        df_reg.to_excel(writer, index=False, sheet_name='Fase Regular', startrow=3)
    return output.getvalue()

def generar_pdf(df_reg, stats):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Reporte Cuervos - Fase Regular", ln=True, align='C')
    pdf.ln(2)
    pdf.set_font("Arial", "B", 11)
    stats_texto = f"PTS: {stats['PTS']} | J.J: {stats['JJ']} | J.G: {stats['JG']} | J.E: {stats['JE']} | J.P: {stats['JP']} | G.F: {stats['GF']} | G.C: {stats['GC']}"
    pdf.cell(200, 10, txt=stats_texto, ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    cols, anchos = ['Jornada', 'Equipo Rival', 'GF', 'GC', 'Resultado', 'Pts'], [20, 60, 20, 20, 40, 20]
    for i, col in enumerate(cols): pdf.cell(anchos[i], 10, col, border=1, align='C')
    pdf.ln()
    pdf.set_font("Arial", "", 10)
    for _, row in df_reg.iterrows():
        pdf.cell(anchos[0], 10, str(row.get('Jornada', '')), border=1, align='C')
        pdf.cell(anchos[1], 10, str(row.get('Equipo Rival', ''))[:25], border=1, align='C')
        pdf.cell(anchos[2], 10, str(row.get('Goles a Favor', '')), border=1, align='C')
        pdf.cell(anchos[3], 10, str(row.get('Goles en Contra', '')), border=1, align='C')
        pdf.cell(anchos[4], 10, str(row.get('Resultado', '')), border=1, align='C')
        pdf.cell(anchos[5], 10, str(row.get('Puntos', '')), border=1, align='C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- FLUJO PRINCIPAL ---
df = cargar_datos()
df_liguilla = df[df['Fase'].isin(['Cuartos', 'Semifinal', 'Final'])]

if not df_liguilla.empty and not st.session_state.override_cierre:
    st.session_state.clasifico_liguilla = True
    st.session_state.temporada_terminada = True
    st.session_state.preguntar_clasificacion = False

    if ((df_liguilla['Fase'] == 'Final') & (df_liguilla['Resultado'].str.contains('Victoria|G-SO'))).any():
        st.session_state.estado_torneo = "Campeon"
    elif (df_liguilla['Resultado'].str.contains('Derrota|P-SO')).any():
        st.session_state.estado_torneo = "Eliminado"
    else:
        if not df_liguilla[df_liguilla['Fase'] == 'Semifinal'].empty:
            st.session_state.estado_torneo = "Final"
        elif not df_liguilla[df_liguilla['Fase'] == 'Cuartos'].empty:
            st.session_state.estado_torneo = "Semifinal"
        else:
            st.session_state.estado_torneo = "Cuartos"
elif st.session_state.override_cierre:
    pass
else:
    if st.session_state.clasifico_liguilla:
        st.session_state.estado_torneo = "Cuartos"
    elif st.session_state.temporada_terminada:
        st.session_state.estado_torneo = "Eliminado"
    else:
        st.session_state.estado_torneo = "Regular"

ANCHO = ancho_completo()

# --- BARRA LATERAL ---
with st.sidebar:
    bloque_marca(LOGO_PATH)
    pasos_fase(st.session_state.estado_torneo, df)

    if not st.session_state.temporada_terminada:
        if st.button("Cerrar fase regular", type="primary", icon=":material/lock:", **ANCHO):
            st.session_state.preguntar_clasificacion = True

        if st.session_state.preguntar_clasificacion:
            st.warning("¿Clasificaron a la liguilla?", icon=":material/help:")
            c1, c2 = st.columns(2)
            if c1.button("Sí", **ANCHO):
                st.session_state.update({
                    "clasifico_liguilla": True,
                    "temporada_terminada": True,
                    "preguntar_clasificacion": False,
                    "estado_torneo": "Cuartos",
                    "override_cierre": False
                })
                limpiar_formulario()
                st.balloons(); st.rerun()
            if c2.button("No", **ANCHO):
                st.session_state.update({
                    "clasifico_liguilla": False,
                    "temporada_terminada": True,
                    "preguntar_clasificacion": False,
                    "estado_torneo": "Eliminado",
                    "override_cierre": False
                })
                st.rerun()
    else:
        if st.button("Deshacer cierre", icon=":material/undo:", **ANCHO):
            # Borramos físicamente los partidos de Liguilla para que no reaparezcan
            try:
                supabase.table("resultados").delete().in_("Fase", ["Cuartos", "Semifinal", "Final"]).execute()
            except Exception as e:
                st.error(f"Error limpiando Liguilla: {e}")

            st.session_state.update({
                "temporada_terminada": False,
                "clasifico_liguilla": False,
                "estado_torneo": "Regular",
                "preguntar_clasificacion": False,
                "override_cierre": False
            })
            limpiar_formulario()
            st.cache_data.clear()
            st.rerun()

    if st.button("Refrescar datos", icon=":material/refresh:", **ANCHO):
        st.cache_data.clear(); st.rerun()

    with st.expander("Restaurar desde Excel", icon=":material/upload:"):
        st.caption("Sube un archivo .xlsx generado por la app para restaurar los datos.")
        archivo_subido = st.file_uploader("Archivo Excel", type=["xlsx"], label_visibility="collapsed")

        if archivo_subido is not None:
            if st.button("Confirmar restauración", type="primary", icon=":material/warning:", **ANCHO):
                try:
                    df_nuevo = pd.read_excel(archivo_subido)
                    supabase.table("resultados").delete().neq("id", 0).execute()
                    registros = df_nuevo.to_dict(orient='records')
                    for r in registros:
                        r.pop('id', None)
                        r.pop('created_at', None)
                    if registros:
                        supabase.table("resultados").insert(registros).execute()
                    st.cache_data.clear()
                    st.success("Base de datos restaurada con éxito.", icon=":material/check_circle:")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al restaurar: {e}")

    with bloque("cv_danger"):
        confirma = st.checkbox("Confirmar reinicio de temporada", key=f"reset_{st.session_state.contador_form}")
        if st.button("Nueva temporada", type="secondary", icon=":material/delete:", disabled=not confirma, **ANCHO):
            reiniciar_sistema()

# --- ESTADÍSTICAS ---
df_reg = df[df["Fase"] == "Regular"]
df_j = df_reg[~df_reg["Resultado"].astype(str).str.contains("Pendiente", na=False)]
n_pendientes = int(df_reg["Resultado"].astype(str).str.contains("Pendiente", na=False).sum())

stats_dict = {
    "JJ": len(df_j),
    "JG": len(df_j[df_j["Resultado"].astype(str).str.contains("Victoria", na=False)]),
    "JE": len(df_j[df_j["Resultado"].astype(str).str.contains("Empate", na=False)]),
    "JP": len(df_j[df_j["Resultado"].astype(str).str.contains("Derrota", na=False)]),
    "GF": int(pd.to_numeric(df_j["Goles a Favor"], errors='coerce').fillna(0).sum()),
    "GC": int(pd.to_numeric(df_j["Goles en Contra"], errors='coerce').fillna(0).sum()),
    "PTS": int(pd.to_numeric(df_reg["Puntos"], errors='coerce').fillna(0).sum())
}

# --- ENCABEZADO Y RESUMEN ---
estado_actual = st.session_state.estado_torneo
if estado_actual == "Regular":
    max_reg = pd.to_numeric(df_reg["Jornada"], errors='coerce').max()
    prox_reg = int(max_reg) + 1 if pd.notna(max_reg) else 1
    encabezado("Temporada regular", f"Próximo partido: jornada {prox_reg}")
else:
    titulo = "Liguilla" if not df_liguilla.empty or estado_actual in ["Cuartos", "Semifinal", "Final"] else "Temporada terminada"
    encabezado(titulo, f"Fase regular cerrada con {stats_dict['PTS']} puntos")

if estado_actual == "Campeon":
    st.balloons()

panel_resumen(stats_dict, df_j, n_pendientes)

if estado_actual != "Regular":
    panel_liguilla(estado_actual, df)

col_f, col_h = st.columns([2, 3], gap="medium")

# --- Columna Izquierda: Formulario ---
with col_f:
    fase = st.session_state.estado_torneo
    if fase in ["Regular", "Cuartos", "Semifinal", "Final"]:
        with panel("form"):
            titulo_panel("Registrar partido" if fase == "Regular" else f"Registrar {NOMBRE_FASE[fase].lower()}")
            suffix = st.session_state.contador_form

            df_fase = df[df["Fase"] == fase]
            df_pend = df_fase[df_fase["Resultado"].astype(str).str.contains("Pendiente", na=False)]

            modo = "Nuevo Partido"
            if not df_pend.empty:
                etiquetas = {"Nuevo partido": "Nuevo Partido", f"Pendiente ({len(df_pend)})": "Actualizar Pendiente"}
                eleccion = selector("Acción", list(etiquetas.keys()), key=f"m_{suffix}", default="Nuevo partido", oculto=True)
                modo = etiquetas.get(eleccion, "Nuevo Partido")

            if modo == "Nuevo Partido":
                max_j = pd.to_numeric(df_fase["Jornada"], errors='coerce').max()
                num_p = int(max_j) + 1 if pd.notna(max_j) else 1

                c_j, c_r = st.columns([1, 3])
                c_j.number_input("Partido #", value=num_p, disabled=True, key=f"j_{suffix}")
                rival = c_r.text_input("Equipo rival", key=f"r_{suffix}", placeholder="Nombre del rival")
                id_upd = None
            else:
                opciones = df_pend["Jornada"].astype(str) + " - " + df_pend["Equipo Rival"]
                sel = st.selectbox("Partido pendiente", opciones.tolist(), key=f"s_{suffix}")

                match_row = df_pend[opciones == sel]
                if not match_row.empty:
                    row = match_row.iloc[0]
                    id_upd = row["id"]
                    rival_defecto = row["Equipo Rival"]
                    num_p_seguro = int(pd.to_numeric(row["Jornada"], errors='coerce')) if pd.notna(row["Jornada"]) else 1
                else:
                    id_upd = None
                    rival_defecto = ""
                    num_p_seguro = 1

                c_j, c_r = st.columns([1, 3])
                c_j.number_input("Partido #", value=num_p_seguro, disabled=True, key=f"ju_{id_upd}_{suffix}")
                rival = c_r.text_input("Equipo rival", value=rival_defecto, key=f"ru_{id_upd}_{suffix}")

            gf, gc, so = 0, 0, None
            pnd = False
            if modo == "Nuevo Partido":
                pnd = st.checkbox("Dejar como pendiente", key=f"p_{suffix}")

            if not pnd:
                with bloque("cv_marcador"):
                    cx, cy = st.columns(2)
                    gf = cx.number_input("Goles Cuervos", min_value=0, key=f"gf_{suffix}")
                    gc = cy.number_input("Goles rival", min_value=0, key=f"gc_{suffix}")
                if gf == gc:
                    so = selector("Empate. ¿Quién ganó el shootout?", ["Cuervos", "Rival"], key=f"so_{suffix}")

            if fase == "Regular" or pnd:
                listo = vista_previa(gf, gc, so, pnd)
            else:
                listo = vista_previa_liguilla(gf, gc, so, fase)

            txt_boton = "Guardar partido" if modo == "Nuevo Partido" else "Actualizar marcador"

            if st.button(txt_boton, type="primary", icon=":material/check:", disabled=not listo, **ANCHO):
                if rival.strip():
                    p, r = (0, "Pendiente") if pnd else procesar_marcador(gf, gc, so)
                    jornada_guardar = num_p if modo == "Nuevo Partido" else num_p_seguro
                    data = {"Jornada": jornada_guardar, "Fase": fase, "Equipo Rival": rival.strip(), "Goles a Favor": gf, "Goles en Contra": gc, "Resultado": r, "Puntos": p}

                    try:
                        if id_upd:
                            supabase.table("resultados").update(data).eq("id", int(id_upd)).execute()
                        else:
                            supabase.table("resultados").insert(data).execute()

                        st.cache_data.clear()
                        limpiar_formulario()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error con DB: {e}")
                else:
                    st.warning("Escribe el nombre del rival.", icon=":material/edit:")
    else:
        with panel("form"):
            vacio("Temporada cerrada", "Usa Deshacer cierre en la barra lateral para corregir la liguilla, o Nueva temporada para empezar de cero.")

# --- Columna Derecha: Tablas ---
with col_h:
    with panel("tabla"):
        titulo_panel("Partidos")
        st.caption("Doble clic en una celda para editar. Selecciona una fila y pulsa Suprimir para borrarla.")
        df_v = df.copy()
        if not df_v.empty: df_v['Resultado'] = df_v['Resultado'].apply(obtener_icono)

        if st.session_state.clasifico_liguilla and not st.session_state.override_cierre:
            if st.session_state.estado_torneo != "Regular":
                t_lig, t_reg = st.tabs(["Liguilla", "Fase regular"])
            else:
                t_reg, t_lig = st.tabs(["Fase regular", "Liguilla"])
        else:
            t_reg, = st.tabs(["Fase regular"])
            t_lig = None

        with t_reg:
            df_rv = df_v[df_v["Fase"] == "Regular"].reset_index(drop=True)
            ed_reg = st.data_editor(
                df_rv,
                hide_index=True,
                num_rows="dynamic",
                key="ed_r",
                column_config={
                    "id": None,
                    "Fase": None,
                    "Jornada": "Jor.",
                    "Goles a Favor": "GF",
                    "Goles en Contra": "GC",
                    "Puntos": "Pts",
                },
                **ANCHO
            )
            c_s, c_p, c_x = st.columns([2, 1, 1])
            if c_s.button("Guardar correcciones", key="btn_save_reg", icon=":material/save:", **ANCHO):
                ed_reg['Resultado'] = ed_reg['Resultado'].apply(limpiar_icono)
                ed_reg['Fase'] = "Regular"
                pd_final = pd.concat([ed_reg, df[df["Fase"] != "Regular"]], ignore_index=True)
                guardar_correcciones(df, pd_final)
                st.rerun()

            df_exp = ed_reg.copy()
            df_exp = df_exp.drop(columns=["id", "Fase"], errors="ignore")
            if "Resultado" in df_exp.columns:
                df_exp['Resultado'] = df_exp['Resultado'].apply(limpiar_icono)

            if FPDF_DISPONIBLE:
                c_p.download_button("PDF", generar_pdf(df_exp, stats_dict), "Cuervos_Reporte.pdf", icon=":material/download:", **ANCHO)
            c_x.download_button("Excel", generar_excel(df_exp, stats_dict), "Cuervos_Reporte.xlsx", icon=":material/download:", **ANCHO)

        if t_lig:
            with t_lig:
                df_lv = df_v[df_v["Fase"] != "Regular"].reset_index(drop=True)
                ed_lig = st.data_editor(
                    df_lv,
                    hide_index=True,
                    num_rows="dynamic",
                    key="ed_l",
                    column_config={
                        "id": None,
                        "Jornada": None,
                        "Puntos": None,
                        "Goles a Favor": "GF",
                        "Goles en Contra": "GC",
                    },
                    **ANCHO
                )
                if st.button("Guardar correcciones", key="btn_save_lig", icon=":material/save:"):
                    ed_lig['Resultado'] = ed_lig['Resultado'].apply(limpiar_icono)
                    pd_final_lig = pd.concat([df[df["Fase"] == "Regular"], ed_lig], ignore_index=True)
                    guardar_correcciones(df, pd_final_lig)
                    st.rerun()
