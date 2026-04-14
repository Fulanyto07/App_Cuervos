import streamlit as st
import pandas as pd
from supabase import create_client, Client
from PIL import Image
import io
import os

# 1. Configuración de la página
st.set_page_config(page_title="Gestor Cuervos Cloud", page_icon="🐦‍⬛", layout="wide")

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

def limpiar_formulario():
    st.session_state.contador_form += 1

# 4. Funciones de Datos
def cargar_datos():
    try:
        response = supabase.table("resultados").select("*").order("id").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=["id", "Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])
    except:
        return pd.DataFrame(columns=["id", "Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])

def guardar_correcciones(df_completo):
    df_completo = df_completo.dropna(subset=['Equipo Rival'])
    if "id" in df_completo.columns: df_completo = df_completo.drop(columns=["id"])
    try:
        supabase.table("resultados").delete().neq("id", 0).execute()
        records = df_completo.to_dict(orient="records")
        if records: supabase.table("resultados").insert(records).execute()
        st.cache_data.clear()
        st.success("✅ ¡Base de datos actualizada!")
    except Exception as e:
        st.error(f"Error: {e}")

# 5. Lógica Deportiva
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

def limpiar_icono(res):
    return str(res).replace("✅ ", "").replace("➖ ", "").replace("❌ ", "").replace("⏳ ", "")

# --- FLUJO PRINCIPAL ---
df = cargar_datos()

with st.sidebar:
    if os.path.exists("cuervos_logo.png"): st.image(Image.open("cuervos_logo.png"), width=120)
    st.header("⚙️ Menú Admin")
    st.info(f"📌 **Fase Actual:** {st.session_state.estado_torneo}")
    st.divider()
    
    if not st.session_state.temporada_terminada:
        if st.button("🏁 Finalizar Etapa Regular", type="primary", use_container_width=True):
            st.session_state.preguntar_clasificacion = True
        if st.session_state.preguntar_clasificacion:
            st.warning("¿Clasificaron a Liguilla?")
            c1, c2 = st.columns(2)
            if c1.button("SÍ", use_container_width=True):
                st.session_state.update({"clasifico_liguilla": True, "temporada_terminada": True, "preguntar_clasificacion": False, "estado_torneo": "Cuartos"})
                st.balloons(); st.rerun()
            if c2.button("NO", use_container_width=True):
                st.session_state.update({"clasifico_liguilla": False, "temporada_terminada": True, "preguntar_clasificacion": False, "estado_torneo": "Eliminado"})
                st.rerun()
    else:
        st.success("🏆 ¡Temporada Cerrada!")
        if st.button("⏪ Reabrir Temporada", use_container_width=True):
            st.session_state.update({"temporada_terminada": False, "clasifico_liguilla": False, "estado_torneo": "Regular"})
            st.rerun()
    st.divider()
    if st.button("🔄 Refrescar Pantalla", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# Dashboard
st.markdown("<h1 style='text-align: center;'>Gestor de Temporada: Cuervos</h1>", unsafe_allow_html=True)
df_reg = df[df["Fase"] == "Regular"]
df_j = df_reg[~df_reg["Resultado"].astype(str).str.contains("Pendiente", na=False)]
stats = {"JJ": len(df_j), "JG": len(df_j[df_j["Resultado"]=="Victoria"]), "PTS": int(df_reg["Puntos"].sum()) if not df_reg.empty else 0}

c_pts, c_stats = st.columns([1, 3])
c_pts.metric("Puntos", f"{stats['PTS']} pts")
c_stats.write(f"Partidos Jugados: {stats['JJ']} | Victorias: {stats['JG']}")
st.divider()

col_f, col_h = st.columns([2, 3])

with col_f:
    fase = st.session_state.estado_torneo
    if fase in ["Regular", "Cuartos", "Semifinal", "Final"]:
        st.subheader(f"Registro: {fase}")
        suffix = st.session_state.contador_form
        df_pend = df[df["Resultado"].astype(str).str.contains("Pendiente", na=False)]
        modo = st.radio("Acción:", ["Nuevo", "Actualizar Pendiente"], horizontal=True, key=f"m_{suffix}") if not df_pend.empty else "Nuevo"
        
        if modo == "Nuevo":
            num_p = int(pd.to_numeric(df[df["Fase"]==fase]["Jornada"], errors='coerce').max() or 0) + 1
            st.number_input("Partido #", value=num_p, disabled=True, key=f"j_{suffix}")
            rival = st.text_input("Rival", key=f"r_{suffix}")
            pnd = st.checkbox("⏳ Pendiente", key=f"p_{suffix}")
            id_upd = None
        else:
            sel = st.selectbox("Seleccionar:", df_pend["Jornada"].astype(str) + " - " + df_pend["Equipo Rival"], key=f"s_{suffix}")
            row = df_pend.iloc[df_pend["Jornada"].astype(str).tolist().index(sel.split(" - ")[0])]
            num_p, rival, pnd, id_upd = row["Jornada"], row["Equipo Rival"], False, row["id"]
            st.text(f"Actualizando Partido {num_p} vs {rival}")

        gf, gc, so = 0, 0, None
        if not pnd:
            cx, cy = st.columns(2)
            gf = cx.number_input("Goles Cuervos", min_value=0, key=f"gf_{suffix}")
            gc = cy.number_input("Goles Rival", min_value=0, key=f"gc_{suffix}")
            if gf == gc: so = st.radio("Ganador SO:", ["Cuervos", "Rival"], horizontal=True, key=f"so_{suffix}")

        if st.button("Guardar Partido", type="primary", use_container_width=True):
            if rival.strip():
                p, r = (0, "Pendiente") if pnd else procesar_marcador(gf, gc, so)
                data = {"Jornada": num_p, "Fase": fase, "Equipo Rival": rival, "Goles a Favor": gf, "Goles en Contra": gc, "Resultado": r, "Puntos": p}
                if id_upd: supabase.table("resultados").update(data).eq("id", id_upd).execute()
                else: supabase.table("resultados").insert(data).execute()
                
                # Salto de fase automático
                if not pnd:
                    if fase == "Cuartos": st.session_state.estado_torneo = "Semifinal"
                    elif fase == "Semifinal": st.session_state.estado_torneo = "Final"
                    elif fase == "Final": st.session_state.estado_torneo = "Campeon" if p == 3 or "G-SO" in r else "Eliminado"
                
                st.cache_data.clear(); limpiar_formulario(); st.rerun()

with col_h:
    st.markdown("💡 *Doble clic para corregir marcador. Suprimir para borrar.*")
    tabs = st.tabs(["Fase Regular", "Liguilla"]) if st.session_state.clasifico_liguilla else st.tabs(["Fase Regular"])
    
    df_v = df.copy()
    if not df_v.empty: df_v['Resultado'] = df_v['Resultado'].apply(obtener_icono)
    
    with tabs[0]:
        df_rv = df_v[df_v["Fase"] == "Regular"].reset_index(drop=True)
        ed_reg = st.data_editor(df_rv, use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_r", column_config={"id": None, "Fase": None})
        if st.button("💾 Guardar Cambios Regular"):
            ed_reg['Resultado'] = ed_reg['Resultado'].apply(limpiar_icono)
            pd_f = pd.concat([ed_reg.assign(Fase="Regular"), df[df["Fase"]!="Regular"]], ignore_index=True)
            guardar_correcciones(pd_f); st.rerun()

    if st.session_state.clasifico_liguilla:
        with tabs[1]:
            df_lv = df_v[df_v["Fase"] != "Regular"].reset_index(drop=True)
            # AQUÍ QUITAMOS LA COLUMNA JORNADA (Partido #)
            ed_lig = st.data_editor(df_lv, use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_l", column_config={"id": None, "Jornada": None, "Puntos": None})
            if st.button("💾 Guardar Liguilla"):
                ed_lig['Resultado'] = ed_lig['Resultado'].apply(limpiar_icono)
                pd_f = pd.concat([df[df["Fase"]=="Regular"], ed_lig], ignore_index=True)
                guardar_correcciones(pd_f); st.rerun()
