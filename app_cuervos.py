import streamlit as st
import pandas as pd
import os
from PIL import Image
import io


# Librerías opcionales para exportar
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# =============================================================================
# CAPA VISUAL (estilo vidrio, tipografía y bloques HTML). Solo presentación:
# no toca datos ni reglas deportivas. El vidrio es una aproximación web con
# backdrop-filter; con 'Reducir transparencia' del sistema pasa a sólido.
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
html, body{background:#0A0B0D;}
[data-testid="stMainBlockContainer"], .main .block-container{padding-top:2rem; max-width:1440px;}

/* ---------- Barra lateral de vidrio ---------- */
section[data-testid="stSidebar"]{background:transparent !important; border:none !important; border-right:none !important; box-shadow:none !important; outline:none !important;}
section[data-testid="stSidebar"] > div:first-child{border:none !important; box-shadow:none !important;}
section[data-testid="stSidebar"]::before,section[data-testid="stSidebar"]::after{display:none !important; content:none !important;}
[data-testid="stSidebarResizer"]{display:none !important; width:0 !important; min-width:0 !important; max-width:0 !important; opacity:0 !important; pointer-events:none !important; overflow:hidden !important;}
div[class*="ResizeHandle"],div[class*="resizeHandle"],div[class*="sidebar-resize"]{display:none !important;}
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
@media (max-width: 768px){
  html, body{background:#0A0B0D !important;}
  .stApp{background-attachment:scroll !important;}
  section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div:first-child{box-shadow:none !important; border:0 !important; background:transparent !important;}
  [data-testid="stSidebarResizer"]{display:none !important;}
  [data-testid="stSidebarContent"]{margin:8px !important; width:auto !important; height:calc(100% - 16px) !important;}
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
        img = f'<img src="data:image/png;base64,{b64}" alt="Escudo de La Peste Negra">'
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

# 1. Archivos del sistema
ARCHIVO_DATOS = "resultados_cuervos.csv"
LOGO_PATH = "cuervos_logo.png"
ESCUDO_PATH = "cuervos_escudo.png"
ARCHIVO_ESTADO = "estado_cuervos.txt"

# 2. Configuración de la página
st.set_page_config(page_title="Gestor Cuervos", page_icon=icono_pagina(ESCUDO_PATH), layout="wide")
aplicar_estilo()
ANCHO = ancho_completo()

# 3. Sistema de reseteo de formulario
if 'contador_form' not in st.session_state:
    st.session_state.contador_form = 0
if 'confirmar_borrar' not in st.session_state:
    st.session_state.confirmar_borrar = False

def limpiar_formulario():
    st.session_state.contador_form += 1

# 4. Control del estado del Torneo
def obtener_estado():
    if os.path.exists(ARCHIVO_ESTADO):
        with open(ARCHIVO_ESTADO, "r") as f: return f.read().strip()
    return "Regular"

def guardar_estado(estado):
    with open(ARCHIVO_ESTADO, "w") as f: f.write(estado)

def avisar_y_recargar(mensaje):
    """Guarda un aviso que sobrevive al rerun (st.rerun borra lo que se mostró antes)."""
    st.session_state["aviso"] = mensaje
    st.rerun()

# 5. Funciones de datos
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        df = pd.read_csv(ARCHIVO_DATOS)
        if "Fase" not in df.columns:
            df.insert(1, "Fase", "Regular")
            df.to_csv(ARCHIVO_DATOS, index=False)
        return df
    else:
        return pd.DataFrame(columns=["Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])

def obtener_icono_resultado(resultado):
    res_str = str(resultado)
    if res_str in ['nan', 'None', '']: return ""
    if any(i in res_str for i in ["✅", "➖", "❌", "⏳"]): return res_str
    if "Victoria" in res_str: return "✅ " + res_str
    elif "Empate" in res_str: return "➖ " + res_str
    elif "Pendiente" in res_str: return "⏳ " + res_str
    else: return "❌ " + res_str

def limpiar_icono_resultado(resultado):
    return str(resultado).replace("✅ ", "").replace("➖ ", "").replace("❌ ", "").replace("⏳ ", "")

def procesar_marcador(favor, contra, so_ganador):
    if favor > contra: return 3, "Victoria"
    elif favor < contra: return 0, "Derrota"
    else:
        return (2, "Empate (G-SO)") if so_ganador == "Cuervos" else (1, "Empate (P-SO)")

def generar_excel(df_reg, stats):
    output = io.BytesIO()
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
    pdf.ln(5)
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

# Carga inicial
df, estado = cargar_datos(), obtener_estado()

# --- BARRA LATERAL ---
with st.sidebar:
    # Si aún no copias el escudo nuevo, usa el logo que ya tenías
    bloque_marca(ESCUDO_PATH if os.path.exists(ESCUDO_PATH) else LOGO_PATH)
    pasos_fase(estado, df)

    if estado == "Regular":
        if st.button("Cerrar fase regular", type="primary", icon=":material/lock:", **ANCHO):
            guardar_estado("Pregunta"); st.rerun()

    with st.expander("Ajustar fase manualmente", icon=":material/tune:"):
        fases = ["Regular", "Pregunta", "Cuartos", "Semifinal", "Final", "Eliminado", "Campeon"]
        idx = fases.index(estado) if estado in fases else 0
        f_m = st.selectbox("Forzar fase", fases, index=idx)
        if st.button("Aplicar ajuste", **ANCHO):
            guardar_estado(f_m)
            st.rerun()

    with st.expander("Restaurar respaldo (Excel/CSV)", icon=":material/upload:"):
        st.warning("La base de datos actual será reemplazada.", icon=":material/warning:")
        archivo_subido = st.file_uploader("Sube tu archivo", type=["xlsx", "csv"])
        if archivo_subido is not None:
            if st.button("Cargar respaldo", type="primary", **ANCHO):
                try:
                    if archivo_subido.name.endswith('.csv'):
                        df_importado = pd.read_csv(archivo_subido)
                        if "PTS" in df_importado.columns:
                            archivo_subido.seek(0)
                            df_importado = pd.read_csv(archivo_subido, skiprows=3)
                    else:
                        df_importado = pd.read_excel(archivo_subido)
                        if "PTS" in df_importado.columns:
                            archivo_subido.seek(0)
                            df_importado = pd.read_excel(archivo_subido, skiprows=3)

                    df_importado = df_importado.loc[:, ~df_importado.columns.str.contains('^Unnamed')]
                    df_importado = df_importado.rename(columns={"GF": "Goles a Favor", "GC": "Goles en Contra", "Pts": "Puntos"})

                    columnas_requeridas = ["Jornada", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"]
                    if not all(c in df_importado.columns for c in columnas_requeridas):
                        st.error("Formato incorrecto. Revisa las columnas de tu archivo.")
                    else:
                        df_importado = df_importado.dropna(subset=['Equipo Rival'])
                        if "Fase" not in df_importado.columns: df_importado.insert(1, "Fase", "Regular")
                        df_importado = df_importado[["Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"]]
                        df_importado.to_csv(ARCHIVO_DATOS, index=False)
                        avisar_y_recargar("Respaldo cargado con éxito.")
                except Exception as e:
                    st.error(f"Error al leer el archivo: {e}")

# --- DASHBOARD DE TOTALES ---
df_reg_stats = df[df["Fase"] == "Regular"].copy()
df_reg_stats["Puntos"] = pd.to_numeric(df_reg_stats["Puntos"], errors='coerce').fillna(0)
df_reg_stats["Goles a Favor"] = pd.to_numeric(df_reg_stats["Goles a Favor"], errors='coerce').fillna(0)
df_reg_stats["Goles en Contra"] = pd.to_numeric(df_reg_stats["Goles en Contra"], errors='coerce').fillna(0)
df_reg_stats["Resultado_str"] = df_reg_stats["Resultado"].astype(str).str.strip()

pts_reg = int(df_reg_stats["Puntos"].sum())
df_j = df_reg_stats[~df_reg_stats["Resultado_str"].str.contains("Pendiente", na=False)]
n_pendientes = int(df_reg_stats["Resultado_str"].str.contains("Pendiente", na=False).sum())

jj = len(df_j)
jg = len(df_j[df_j["Resultado_str"].str.contains("Victoria", na=False)])
je = len(df_j[df_j["Resultado_str"].str.contains("Empate", na=False)])
jp = len(df_j[df_j["Resultado_str"].str.contains("Derrota", na=False)])
gf = int(df_j["Goles a Favor"].sum())
gc = int(df_j["Goles en Contra"].sum())

stats_dict = {"JJ": jj, "JG": jg, "JE": je, "JP": jp, "GF": gf, "GC": gc, "PTS": pts_reg}

# --- AVISO DE LA ACCIÓN ANTERIOR ---
if "aviso" in st.session_state:
    st.toast(st.session_state.pop("aviso"), icon=":material/check_circle:")

# --- ENCABEZADO Y RESUMEN ---
if estado in ["Regular", "Pregunta"]:
    max_reg = pd.to_numeric(df_reg_stats["Jornada"], errors='coerce').max()
    prox_reg = int(max_reg) + 1 if pd.notna(max_reg) else 1
    sub = f"Próximo partido: jornada {prox_reg}" if estado == "Regular" else "Fase regular cerrada, falta confirmar la clasificación"
    encabezado("Temporada regular", sub)
else:
    hay_liguilla = df["Fase"].isin(FASES_LIGUILLA).any() if not df.empty else False
    titulo = "Liguilla" if hay_liguilla or estado in FASES_LIGUILLA else "Temporada terminada"
    encabezado(titulo, f"Fase regular cerrada con {pts_reg} puntos")

panel_resumen(stats_dict, df_j, n_pendientes)

if estado not in ["Regular", "Pregunta"]:
    panel_liguilla(estado, df)

col_form, col_hist = st.columns([2, 3], gap="medium")

# --- REGISTRO ---
with col_form:
    if estado == "Regular":
        with panel("form"):
            titulo_panel("Registrar partido")
            suffix = st.session_state.contador_form
            df_pend = df_reg_stats[df_reg_stats["Resultado_str"].str.contains("Pendiente", na=False)]

            modo = "Nuevo Partido"
            if not df_pend.empty:
                etiquetas = {"Nuevo partido": "Nuevo Partido", f"Pendiente ({len(df_pend)})": "Actualizar Pendiente"}
                eleccion = selector("Acción", list(etiquetas.keys()), key=f"m_{suffix}", default="Nuevo partido", oculto=True)
                modo = etiquetas.get(eleccion, "Nuevo Partido")

            if modo == "Nuevo Partido":
                max_j = pd.to_numeric(df_reg_stats["Jornada"], errors='coerce').max()
                next_j = int(max_j) + 1 if pd.notna(max_j) else 1

                c_j, c_r = st.columns([1, 3])
                c_j.number_input("Jornada", value=next_j, disabled=True, key=f"jor_{suffix}")
                rival = c_r.text_input("Equipo rival", key=f"rival_{suffix}", placeholder="Nombre del rival")
                es_pendiente = st.checkbox("Marcar como pendiente", key=f"pend_{suffix}")
                idx_upd = None
            else:
                opciones = df_pend["Jornada"].astype(str) + " - " + df_pend["Equipo Rival"]
                sel = st.selectbox("Partido pendiente", opciones.tolist(), key=f"s_{suffix}")

                match_idx = df_pend[opciones == sel].index
                if len(match_idx) > 0:
                    idx_upd = match_idx[0]
                    rival_defecto = df_reg_stats.loc[idx_upd, "Equipo Rival"]
                    next_j = int(df_reg_stats.loc[idx_upd, "Jornada"])
                else:
                    idx_upd = None
                    rival_defecto = ""
                    next_j = 1

                c_j, c_r = st.columns([1, 3])
                c_j.number_input("Jornada", value=next_j, disabled=True, key=f"jor_u_{suffix}")
                # Editable para poder cambiar el rival en vivo
                rival = c_r.text_input("Equipo rival", value=rival_defecto, key=f"rival_u_{suffix}")
                es_pendiente = False

            g_f, g_c, ganador_so = 0, 0, None
            if not es_pendiente:
                with bloque("cv_marcador"):
                    cx, cy = st.columns(2)
                    g_f = cx.number_input("Goles Cuervos", min_value=0, step=1, key=f"gf_{suffix}")
                    g_c = cy.number_input("Goles rival", min_value=0, step=1, key=f"gc_{suffix}")
                if g_f == g_c:
                    ganador_so = selector("Empate. ¿Quién ganó el shootout?", ["Cuervos", "Rival"], key=f"so_{suffix}")

            listo = vista_previa(g_f, g_c, ganador_so, es_pendiente)

            txt_boton = "Guardar partido" if modo == "Nuevo Partido" else "Actualizar marcador"
            if st.button(txt_boton, type="primary", icon=":material/check:", disabled=not listo, **ANCHO):
                if rival.strip():
                    if es_pendiente: pts, res, g_f, g_c = 0, "Pendiente", 0, 0
                    else: pts, res = procesar_marcador(g_f, g_c, ganador_so)

                    if modo == "Nuevo Partido":
                        nuevo = pd.DataFrame([{"Jornada": next_j, "Fase": "Regular", "Equipo Rival": rival.strip(), "Goles a Favor": g_f, "Goles en Contra": g_c, "Resultado": res, "Puntos": pts}])
                        df = pd.concat([df, nuevo], ignore_index=True)
                    else:
                        df.loc[idx_upd, "Equipo Rival"] = rival.strip()
                        df.loc[idx_upd, "Goles a Favor"] = g_f
                        df.loc[idx_upd, "Goles en Contra"] = g_c
                        df.loc[idx_upd, "Resultado"] = res
                        df.loc[idx_upd, "Puntos"] = pts

                    df.to_csv(ARCHIVO_DATOS, index=False)
                    limpiar_formulario()
                    st.rerun()
                else:
                    st.warning("Escribe el nombre del rival.", icon=":material/edit:")

    elif estado == "Pregunta":
        with panel("form"):
            titulo_panel("¿Clasificaron a la liguilla?")
            st.caption("Si respondes que sí, el siguiente registro será de cuartos de final.")
            c_y, c_n = st.columns(2)
            if c_y.button("Sí, clasificamos", type="primary", icon=":material/check:", **ANCHO): guardar_estado("Cuartos"); st.rerun()
            if c_n.button("No", icon=":material/close:", **ANCHO): guardar_estado("Eliminado"); st.rerun()
            if st.button("Volver a la fase regular", icon=":material/undo:", **ANCHO): guardar_estado("Regular"); st.rerun()

    elif estado in ["Cuartos", "Semifinal", "Final"]:
        with panel("form"):
            titulo_panel(f"Registrar {NOMBRE_FASE[estado].lower()}")
            suffix = st.session_state.contador_form
            rival = st.text_input("Rival", key=f"rival_lig_{suffix}", placeholder="Nombre del rival")
            with bloque("cv_marcador"):
                c1, c2 = st.columns(2)
                g_f = c1.number_input("Goles Cuervos", min_value=0, step=1, key=f"gf_lig_{suffix}")
                g_c = c2.number_input("Goles rival", min_value=0, step=1, key=f"gc_lig_{suffix}")
            ganador_so = None
            if g_f == g_c:
                ganador_so = selector("Empate. ¿Quién ganó el shootout?", ["Cuervos", "Rival"], key=f"so_lig_{suffix}")
            listo = vista_previa_liguilla(g_f, g_c, ganador_so, estado)
            if st.button(f"Guardar {NOMBRE_FASE[estado].lower()}", type="primary", icon=":material/check:", disabled=not listo, **ANCHO):
                if rival.strip():
                    _, res = procesar_marcador(g_f, g_c, ganador_so)
                    nuevo = pd.DataFrame([{"Jornada": "-", "Fase": estado, "Equipo Rival": rival.strip(), "Goles a Favor": g_f, "Goles en Contra": g_c, "Resultado": res, "Puntos": 0}])
                    df = pd.concat([df, nuevo], ignore_index=True); df.to_csv(ARCHIVO_DATOS, index=False)
                    if "Victoria" in res or "G-SO" in res:
                        prox = {"Cuartos": "Semifinal", "Semifinal": "Final", "Final": "Campeon"}
                        guardar_estado(prox[estado])
                    else: guardar_estado("Eliminado")
                    limpiar_formulario(); st.rerun()
                else:
                    st.warning("Escribe el nombre del rival.", icon=":material/edit:")

    elif estado in ["Eliminado", "Campeon"]:
        if estado == "Campeon": st.balloons()
        with panel("form"):
            vacio("Temporada terminada", "Para empezar de nuevo se borran TODOS los partidos. No se puede deshacer.")
            if not st.session_state.get("confirmar_borrar"):
                if st.button("Borrar todos los partidos", type="primary", icon=":material/restart_alt:", **ANCHO):
                    st.session_state["confirmar_borrar"] = True
                    st.rerun()
            else:
                st.warning("¿Borrar TODOS los partidos? No se puede deshacer.", icon=":material/warning:")
                c_si, c_no = st.columns(2)
                if c_si.button("Sí, borrar", type="primary", icon=":material/delete:", **ANCHO):
                    st.session_state["confirmar_borrar"] = False
                    pd.DataFrame(columns=df.columns).to_csv(ARCHIVO_DATOS, index=False)
                    guardar_estado("Regular")
                    avisar_y_recargar("Temporada reiniciada: se borraron todos los partidos.")
                if c_no.button("Cancelar", icon=":material/close:", **ANCHO):
                    st.session_state["confirmar_borrar"] = False
                    st.rerun()

# --- HISTORIAL ---
with col_hist:
    with panel("tabla"):
        titulo_panel("Partidos")
        st.caption("Doble clic en una celda para editar. Selecciona una fila y pulsa Suprimir para borrarla.")
        # Al cerrar la fase regular, la Liguilla pasa a ser la pestaña activa (la primera)
        hay_partidos_liguilla = df["Fase"].isin(FASES_LIGUILLA).any() if not df.empty else False
        liguilla_activa = estado in FASES_LIGUILLA or estado == "Campeon" or (estado == "Eliminado" and hay_partidos_liguilla)
        if liguilla_activa:
            t2, t1 = st.tabs(["Liguilla", "Fase regular"])
        else:
            t1, t2 = st.tabs(["Fase regular", "Liguilla"])
        df_v = df.copy()
        if not df_v.empty: df_v['Resultado'] = df_v['Resultado'].apply(obtener_icono_resultado)

        with t1:
            df_r_v = df_v[df_v["Fase"] == "Regular"].reset_index(drop=True)
            if not df_r_v.empty:
                df_ed_r = st.data_editor(df_r_v, height=350, hide_index=True, num_rows="dynamic", key="ed_r",
                                         column_config={"Fase": None, "Jornada": "Jor.", "Goles a Favor": "GF", "Goles en Contra": "GC", "Puntos": "Pts"},
                                         **ANCHO)

                c_s, c_p, c_x = st.columns([2, 1, 1])
                if c_s.button("Guardar correcciones", icon=":material/save:", key="btn_save_reg", **ANCHO):
                    df_clean = df_ed_r.copy()
                    df_clean = df_clean.dropna(subset=['Equipo Rival'])
                    df_clean = df_clean[~df_clean['Equipo Rival'].astype(str).str.strip().isin(['nan', 'None', ''])]
                    df_clean['Resultado'] = df_clean['Resultado'].apply(limpiar_icono_resultado)
                    pd.concat([df_clean, df[df["Fase"] != "Regular"]], ignore_index=True).to_csv(ARCHIVO_DATOS, index=False)
                    avisar_y_recargar("Cambios guardados en la tabla.")

                df_ex = df_ed_r.copy(); df_ex['Resultado'] = df_ex['Resultado'].apply(limpiar_icono_resultado)
                if FPDF_DISPONIBLE: c_p.download_button("PDF", generar_pdf(df_ex, stats_dict), "Cuervos_Regular.pdf", icon=":material/download:", **ANCHO)
                c_x.download_button("Excel", generar_excel(df_ex, stats_dict), "Cuervos_Regular.xlsx", icon=":material/download:", **ANCHO)
            else:
                vacio("Sin partidos todavía", "Registra la primera jornada con el formulario.")

        with t2:
            df_l_v = df_v[df_v["Fase"] != "Regular"].reset_index(drop=True)
            if not df_l_v.empty:
                df_ed_l = st.data_editor(df_l_v, height=350, hide_index=True, num_rows="dynamic", key="ed_l",
                                         column_config={"Jornada": None, "Puntos": None, "Goles a Favor": "GF", "Goles en Contra": "GC"},
                                         **ANCHO)
                if st.button("Guardar correcciones", icon=":material/save:", key="btn_save_lig"):
                    df_clean = df_ed_l.copy()
                    df_clean = df_clean.dropna(subset=['Equipo Rival'])
                    df_clean = df_clean[~df_clean['Equipo Rival'].astype(str).str.strip().isin(['nan', 'None', ''])]
                    df_clean['Resultado'] = df_clean['Resultado'].apply(limpiar_icono_resultado)
                    pd.concat([df[df["Fase"] == "Regular"], df_clean], ignore_index=True).to_csv(ARCHIVO_DATOS, index=False)
                    avisar_y_recargar("Cambios guardados en la tabla.")
            else:
                vacio("La liguilla aún no empieza", "Cierra la fase regular desde la barra lateral para registrar los cuartos de final.")
