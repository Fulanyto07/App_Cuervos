import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from PIL import Image
import os

# 1. Configuración de la página
st.set_page_config(page_title="Gestor Cuervos Cloud", page_icon="🐦‍⬛", layout="wide")

# 2. Conexión a Google Sheets con Sistema Anticaídas
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("🚨 Error bloqueando la conexión a Google Sheets")
    st.write("🔍 **Diagnóstico de Secrets detectados:**")
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        st.code(list(st.secrets["connections"]["gsheets"].keys()), language="python")
        st.info("Si no ves 'token_uri' o 'client_email' en esta lista, hay un salto de línea invisible rompiendo tus Secrets.")
    else:
        st.warning("No se detectó el encabezado [connections.gsheets].")
    st.stop()

# 3. Estado de la sesión
if 'contador_form' not in st.session_state:
    st.session_state.contador_form = 0
if 'estado_torneo' not in st.session_state:
    st.session_state.estado_torneo = "Regular"

def cargar_datos():
    try:
        df_cloud = conn.read(worksheet="Resultados", ttl=0)
        if df_cloud is None or df_cloud.empty:
            return pd.DataFrame(columns=["Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])
        
        df_cloud = df_cloud.dropna(subset=['Equipo Rival'])
        for col in ["Jornada", "Puntos", "Goles a Favor", "Goles en Contra"]:
            if col in df_cloud.columns:
                df_cloud[col] = pd.to_numeric(df_cloud[col], errors='coerce').fillna(0).astype(int)
        return df_cloud
    except:
        return pd.DataFrame(columns=["Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])

def guardar_datos(df_nuevo):
    df_nuevo = df_nuevo.dropna(subset=['Equipo Rival'])
    try:
        conn.update(worksheet="Resultados", data=df_nuevo)
        st.cache_data.clear() 
        st.success("✅ ¡Actualizado en Google Sheets!")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

def procesar_marcador(favor, contra, so_ganador):
    if favor > contra: return 3, "Victoria"
    elif favor < contra: return 0, "Derrota"
    else: return (2, "Empate (G-SO)") if so_ganador == "Cuervos" else (1, "Empate (P-SO)")

def obtener_icono(res):
    res_s = str(res)
    if "Victoria" in res_s: return "✅ " + res_s
    if "Empate" in res_s: return "➖ " + res_s
    if "Pendiente" in res_s: return "⏳ " + res_s
    return "❌ " + res_s

# --- INICIO ---
df = cargar_datos()

# Barra Lateral
with st.sidebar:
    if os.path.exists("cuervos_logo.png"):
        st.image(Image.open("cuervos_logo.png"), width=120)
    st.header("⚙️ Admin")
    fases = ["Regular", "Cuartos", "Semifinal", "Final", "Eliminado", "Campeon"]
    st.session_state.estado_torneo = st.selectbox("Fase Actual:", fases, index=fases.index(st.session_state.estado_torneo))
    if st.button("🔄 Recargar Datos"):
        st.cache_data.clear()
        st.rerun()

# Dashboard
st.title("🐦‍⬛ Gestor de Temporada: Cuervos")
df_reg = df[df["Fase"] == "Regular"]
pts = int(df_reg["Puntos"].sum()) if not df_reg.empty else 0
jj = len(df_reg[~df_reg["Resultado"].astype(str).str.contains("Pendiente")])

c1, c2 = st.columns([1, 4])
c1.metric("Puntos", f"{pts} pts")
c2.write(f"Partidos jugados: {jj}")
st.divider()

col_f, col_h = st.columns([2, 3])

with col_f:
    if st.session_state.estado_torneo == "Regular":
        st.subheader("Registrar Partido")
        id_f = st.session_state.contador_form
        max_j = pd.to_numeric(df_reg["Jornada"], errors='coerce').max()
        proxima = int(max_j) + 1 if pd.notna(max_j) else 1
        
        st.number_input("Jornada", value=proxima, disabled=True, key=f"j_{id_f}")
        rival = st.text_input("Equipo Rival", key=f"r_{id_f}")
        es_p = st.checkbox("⏳ Pendiente", key=f"p_{id_f}")
        
        gf, gc, so = 0, 0, None
        if not es_p:
            cx, cy = st.columns(2)
            gf = cx.number_input("Goles Cuervos", min_value=0, step=1, key=f"gf_{id_f}")
            gc = cy.number_input("Goles Rival", min_value=0, step=1, key=f"gc_{id_f}")
            if gf == gc: so = st.radio("Ganador SO:", ["Cuervos", "Rival"], horizontal=True, key=f"so_{id_f}")
        
        if st.button("Guardar Partido", type="primary"):
            if rival.strip():
                p, r = (0, "Pendiente") if es_p else procesar_marcador(gf, gc, so)
                nuevo = pd.DataFrame([{"Jornada": proxima, "Fase": "Regular", "Equipo Rival": rival.strip(), 
                                       "Goles a Favor": gf, "Goles en Contra": gc, "Resultado": r, "Puntos": p}])
                df = pd.concat([df, nuevo], ignore_index=True)
                guardar_datos(df)
                st.session_state.contador_form += 1
                st.rerun()

with col_h:
    st.subheader("Historial")
    if not df.empty:
        df_ver = df.copy()
        df_ver["Resultado"] = df_ver["Resultado"].apply(obtener_icono)
        st.data_editor(df_ver[df_ver["Fase"]=="Regular"], width="stretch", hide_index=True, column_config={"Fase": None})
