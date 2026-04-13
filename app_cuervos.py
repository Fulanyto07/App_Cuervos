import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from PIL import Image
import io
import os

# Intentar cargar la librería de PDF
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# 1. Configuración de la página
st.set_page_config(page_title="Gestor Cuervos Cloud", page_icon="🐦‍⬛", layout="wide")

# 2. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Sistema de reseteo de formulario
if 'contador_form' not in st.session_state:
    st.session_state.contador_form = 0

def limpiar_formulario():
    st.session_state.contador_form += 1

# 4. Control del estado del Torneo
if 'estado_torneo' not in st.session_state:
    st.session_state.estado_torneo = "Regular"

# 5. Funciones de datos
def cargar_datos_cloud():
    try:
        df_cloud = conn.read(worksheet="Resultados", ttl=0)
        if df_cloud is None or df_cloud.empty:
            return pd.DataFrame(columns=["Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])
        
        if "Equipo Rival" in df_cloud.columns:
            df_cloud = df_cloud.dropna(subset=['Equipo Rival'])
            df_cloud = df_cloud[~df_cloud['Equipo Rival'].astype(str).str.strip().isin(['nan', 'None', ''])]
            
            columnas_num = ["Jornada", "Puntos", "Goles a Favor", "Goles en Contra"]
            for col in columnas_num:
                if col in df_cloud.columns:
                    df_cloud[col] = pd.to_numeric(df_cloud[col], errors='coerce').fillna(0).astype(int)
        return df_cloud
    except Exception:
        return pd.DataFrame(columns=["Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])

def guardar_datos_cloud(df_nuevo):
    df_nuevo = df_nuevo.dropna(subset=['Equipo Rival'])
    df_nuevo = df_nuevo[~df_nuevo['Equipo Rival'].astype(str).str.strip().isin(['nan', 'None', ''])]
    try:
        conn.update(worksheet="Resultados", data=df_nuevo)
        st.cache_data.clear() 
        st.success("✅ ¡Sincronizado con Google Sheets!")
    except Exception as e:
        st.error(f"Error de permisos: {e}")

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

# --- FLUJO PRINCIPAL ---
df = cargar_datos_cloud()

with st.sidebar:
    if os.path.exists("cuervos_logo.png"):
        st.image(Image.open("cuervos_logo.png"), width=120)
    st.header("⚙️ Menú Admin")
    fases = ["Regular", "Cuartos", "Semifinal", "Final", "Eliminado", "Campeon"]
    st.session_state.estado_torneo = st.selectbox("Fase Actual:", fases, index=fases.index(st.session_state.estado_torneo))
    if st.button("🔄 Refrescar"):
        st.cache_data.clear()
        st.rerun()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<h1 style='text-align: center;'>Gestor de Temporada: Cuervos</h1>", unsafe_allow_html=True)

# Dashboard
df_reg_stats = df[df["Fase"] == "Regular"]
pts_reg = int(df_reg_stats["Puntos"].sum()) if not df_reg_stats.empty else 0
df_j = df_reg_stats[~df_reg_stats["Resultado"].astype(str).str.contains("Pendiente")]
jj, jg, je, jp = len(df_j), len(df_j[df_j["Resultado"]=="Victoria"]), len(df_j[df_j["Resultado"].str.contains("Empate", na=False)]), len(df_j[df_j["Resultado"]=="Derrota"])
gf, gc = int(df_j["Goles a Favor"].sum()) if not df_j.empty else 0, int(df_j["Goles en Contra"].sum()) if not df_j.empty else 0

c_pts, c_stats = st.columns([1, 3])
c_pts.metric("Puntos", f"{pts_reg} pts")
c_stats.markdown(f"""<div style='display:flex; justify-content:space-around; padding-top:20px;'>
    <div style='text-align:center;'><small>J.J</small><br><b>{jj}</b></div>
    <div style='text-align:center;'><small>J.G</small><br><b>{jg}</b></div>
    <div style='text-align:center;'><small>J.E</small><br><b>{je}</b></div>
    <div style='text-align:center;'><small>J.P</small><br><b>{jp}</b></div>
    <div style='text-align:center;'><small>G.F</small><br><b>{gf}</b></div>
    <div style='text-align:center;'><small>G.C</small><br><b>{gc}</b></div></div>""", unsafe_allow_html=True)
st.divider()

col_f, col_h = st.columns([2, 3])

with col_f:
    if st.session_state.estado_torneo == "Regular":
        st.subheader("Registrar Partido")
        suffix = st.session_state.contador_form
        max_j = pd.to_numeric(df_reg_stats["Jornada"], errors='coerce').max()
        next_j = int(max_j) + 1 if pd.notna(max_j) else 1
        st.number_input("Jornada", value=next_j, disabled=True, key=f"j_{suffix}")
        rival = st.text_input("Equipo Rival", key=f"r_{suffix}")
        es_pend = st.checkbox("⏳ Pendiente", key=f"p_{suffix}")
        g_f, g_c, g_so = 0, 0, None
        if not es_pend:
            cx, cy = st.columns(2)
            g_f = cx.number_input("Goles Cuervos", min_value=0, step=1, key=f"gf_{suffix}")
            g_c = cy.number_input("Goles Rival", min_value=0, step=1, key=f"gc_{suffix}")
            if g_f == g_c: g_so = st.radio("Ganador SO:", ["Cuervos", "Rival"], horizontal=True, key=f"so_{suffix}")
        
        if st.button("Guardar Partido", type="primary"):
            if rival.strip():
                if es_pend: p, r, gf_i, gc_i = 0, "Pendiente", 0, 0
                else: p, r = procesar_marcador(g_f, g_c, g_so); gf_i, gc_i = g_f, g_c
                nuevo = pd.DataFrame([{"Jornada": next_j, "Fase": "Regular", "Equipo Rival": rival.strip(), "Goles a Favor": gf_i, "Goles en Contra": gc_i, "Resultado": r, "Puntos": p}])
                df = pd.concat([df, nuevo], ignore_index=True)
                guardar_datos_cloud(df)
                limpiar_formulario()
                st.rerun()

with col_h:
    t1, t2 = st.tabs(["Fase Regular", "Liguilla"])
    df_v = df.copy()
    if not df_v.empty: df_v['Resultado'] = df_v['Resultado'].apply(obtener_icono_resultado)
    with t1:
        df_rv = df_v[df_v["Fase"] == "Regular"].reset_index(drop=True)
        df_ed = st.data_editor(df_rv, height=400, use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_r", column_config={"Fase": None})
        if st.button("💾 Guardar Cambios"):
            df_cl = df_ed.copy()
            df_cl = df_cl.dropna(subset=['Equipo Rival'])
            df_cl['Resultado'] = df_cl['Resultado'].apply(limpiar_icono_resultado)
            pd_final = pd.concat([df_cl, df[df["Fase"] != "Regular"]], ignore_index=True)
            guardar_datos_cloud(pd_final)
            st.rerun()
