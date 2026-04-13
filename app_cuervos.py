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

# 4. Funciones de Datos (Supabase)
def cargar_datos():
    try:
        response = supabase.table("resultados").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return pd.DataFrame(columns=["id", "Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])
        return df
    except:
        return pd.DataFrame(columns=["id", "Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])

def guardar_correcciones(df_completo):
    df_completo = df_completo.dropna(subset=['Equipo Rival'])
    if "id" in df_completo.columns:
        df_completo = df_completo.drop(columns=["id"])
    
    try:
        supabase.table("resultados").delete().neq("id", 0).execute()
        records = df_completo.to_dict(orient="records")
        if records:
            supabase.table("resultados").insert(records).execute()
        st.cache_data.clear()
        st.success("✅ ¡Cambios guardados en Supabase!")
    except Exception as e:
        st.error(f"Error al guardar correcciones: {e}")

# 5. Lógica Deportiva y Reportes
def procesar_marcador(favor, contra, so_ganador):
    if favor > contra: return 3, "Victoria"
    elif favor < contra: return 0, "Derrota"
    else: return (2, "Empate (G-SO)") if so_ganador == "Cuervos" else (1, "Empate (P-SO)")

def obtener_icono(res):
    res_str = str(res)
    if "Victoria" in res_str: return "✅ " + res_str
    elif "Empate" in res_str: return "➖ " + res_str
    elif "Pendiente" in res_str: return "⏳ " + res_str
    else: return "❌ " + res_str

def limpiar_icono(res):
    return str(res).replace("✅ ", "").replace("➖ ", "").replace("❌ ", "").replace("⏳ ", "")

def generar_excel(df_reg, stats):
    output = io.BytesIO()
    if "Fase" in df_reg.columns:
        df_reg = df_reg.drop(columns=["Fase"])
        
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
    for i, col in enumerate(cols): 
        pdf.cell(anchos[i], 10, col, border=1, align='C')
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

# Barra Lateral
with st.sidebar:
    if os.path.exists("cuervos_logo.png"):
        st.image(Image.open("cuervos_logo.png"), width=120)
    st.header("⚙️ Menú Admin")
    
    # Fases dinámicas según si clasificaron o no
    if st.session_state.clasifico_liguilla:
        fases = ["Regular", "Cuartos", "Semifinal", "Final", "Campeon"]
    else:
        fases = ["Regular", "Eliminado"]
        
    idx = fases.index(st.session_state.estado_torneo) if st.session_state.estado_torneo in fases else 0
    st.session_state.estado_torneo = st.selectbox("Fase Actual:", fases, index=idx)
    
    st.divider()
    
    # Lógica de cierre de temporada
    if not st.session_state.temporada_terminada:
        if st.button("🏁 Finalizar Fase Regular", type="primary", use_container_width=True):
            st.session_state.preguntar_clasificacion = True
            
        if st.session_state.preguntar_clasificacion:
            st.warning("¿El equipo clasificó a la Liguilla?")
            c_si, c_no = st.columns(2)
            if c_si.button("✅ Sí"):
                st.session_state.clasifico_liguilla = True
                st.session_state.temporada_terminada = True
                st.session_state.preguntar_clasificacion = False
                st.balloons()
                st.rerun()
            if c_no.button("❌ No"):
                st.session_state.clasifico_liguilla = False
                st.session_state.temporada_terminada = True
                st.session_state.preguntar_clasificacion = False
                st.rerun()
    else:
        if st.session_state.clasifico_liguilla:
            st.success("🏆 ¡Clasificados a Liguilla! Selecciona la fase arriba.")
        else:
            st.info("💔 Temporada finalizada. No clasificamos a Liguilla.")
            
        if st.button("⏪ Deshacer Cierre", use_container_width=True):
            st.session_state.temporada_terminada = False
            st.session_state.clasifico_liguilla = False
            st.session_state.estado_torneo = "Regular"
            st.rerun()
            
    st.divider()
    if st.button("🔄 Refrescar Datos (Forzar)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Interfaz Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<h1 style='text-align: center;'>Gestor de Temporada: Cuervos</h1>", unsafe_allow_html=True)

df_reg = df[df["Fase"] == "Regular"]
pts = int(df_reg["Puntos"].sum()) if not df_reg.empty else 0
df_j = df_reg[~df_reg["Resultado"].astype(str).str.contains("Pendiente", na=False)]

stats_dict = {
    "JJ": len(df_j),
    "JG": len(df_j[df_j["Resultado"].astype(str).str.contains("Victoria")]),
    "JE": len(df_j[df_j["Resultado"].astype(str).str.contains("Empate")]),
    "JP": len(df_j[df_j["Resultado"].astype(str).str.contains("Derrota")]),
    "GF": int(df_j["Goles a Favor"].sum()) if not df_j.empty else 0,
    "GC": int(df_j["Goles en Contra"].sum()) if not df_j.empty else 0,
    "PTS": pts
}

c_pts, c_stats = st.columns([1, 3])
c_pts.metric("Puntos", f"{stats_dict['PTS']} pts")
c_stats.markdown(f"""<div style='display:flex; justify-content:space-around; padding-top:20px;'>
    <div style='text-align:center;'><small>J.J</small><br><b>{stats_dict['JJ']}</b></div>
    <div style='text-align:center;'><small>J.G</small><br><b>{stats_dict['JG']}</b></div>
    <div style='text-align:center;'><small>J.E</small><br><b>{stats_dict['JE']}</b></div>
    <div style='text-align:center;'><small>J.P</small><br><b>{stats_dict['JP']}</b></div>
    <div style='text-align:center;'><small>G.F</small><br><b>{stats_dict['GF']}</b></div>
    <div style='text-align:center;'><small>G.C</small><br><b>{stats_dict['GC']}</b></div></div>""", unsafe_allow_html=True)
st.divider()

col_f, col_h = st.columns([2, 3])

# --- Columna Izquierda: Registro ---
with col_f:
    fase_actual = st.session_state.estado_torneo
    if fase_actual in ["Regular", "Cuartos", "Semifinal", "Final"]:
        st.subheader(f"Registrar Partido - {fase_actual}")
        suffix = st.session_state.contador_form
        
        df_fase = df[df["Fase"] == fase_actual]
        max_j = pd.to_numeric(df_fase["Jornada"], errors='coerce').max()
        next_j = int(max_j) + 1 if pd.notna(max_j) else 1
        
        st.number_input("Partido #", value=next_j, disabled=True, key=f"j_{suffix}")
        rival = st.text_input("Equipo Rival", key=f"r_{suffix}")
        es_pend = st.checkbox("⏳ Pendiente", key=f"p_{suffix}")
        
        g_f, g_c, g_so = 0, 0, None
        if not es_pend:
            cx, cy = st.columns(2)
            g_f = cx.number_input("Goles Cuervos", min_value=0, step=1, key=f"gf_{suffix}")
            g_c = cy.number_input("Goles Rival", min_value=0, step=1, key=f"gc_{suffix}")
            if g_f == g_c: 
                g_so = st.radio("Ganador SO:", ["Cuervos", "Rival"], horizontal=True, key=f"so_{suffix}")
        
        if st.button("Guardar Partido", type="primary"):
            if rival.strip():
                p, r = (0, "Pendiente") if es_pend else procesar_marcador(g_f, g_c, g_so)
                gf_i, gc_i = (0, 0) if es_pend else (g_f, g_c)
                
                nuevo_partido = {"Jornada": next_j, "Fase": fase_actual, "Equipo Rival": rival.strip(), 
                                 "Goles a Favor": gf_i, "Goles en Contra": gc_i, "Resultado": r, "Puntos": p}
                
                try:
                    supabase.table("resultados").insert(nuevo_partido).execute()
                    limpiar_formulario()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al conectar con DB: {e}")

# --- Columna Derecha: Tablas ---
with col_h:
    st.markdown("💡 *Doble clic para editar. Selecciona fila y presiona Suprimir para borrar.*")
    
    if st.session_state.clasifico_liguilla:
        tab_reg, tab_lig = st.tabs(["Fase Regular", "Liguilla"])
    else:
        tab_reg, = st.tabs(["Fase Regular"])
        tab_lig = None
    
    df_v = df.copy()
    if not df_v.empty:
        df_v['Resultado'] = df_v['Resultado'].apply(obtener_icono)
        
    with tab_reg:
        df_rv = df_v[df_v["Fase"] == "Regular"].reset_index(drop=True)
        columnas_ocultas = {"id": None, "Fase": None}
        df_ed = st.data_editor(df_rv, height=400, use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_r", column_config=columnas_ocultas)
        
        if st.button("💾 Guardar Correcciones (Regular)"):
            df_cl = df_ed.copy()
            df_cl['Resultado'] = df_cl['Resultado'].apply(limpiar_icono)
            df_cl['Fase'] = "Regular"
            pd_final = pd.concat([df_cl, df[df["Fase"] != "Regular"]], ignore_index=True)
            guardar_correcciones(pd_final)
            st.rerun()
            
        c_p, c_x = st.columns(2)
        df_exp = df_ed.copy()
        if "id" in df_exp.columns: df_exp = df_exp.drop(columns=["id"])
        df_exp['Resultado'] = df_exp['Resultado'].apply(limpiar_icono)
        
        if FPDF_DISPONIBLE: 
            c_p.download_button("📄 PDF", generar_pdf(df_exp, stats_dict), "Cuervos_Reporte.pdf")
        c_x.download_button("📊 Excel", generar_excel(df_exp, stats_dict), "Cuervos_Reporte.xlsx")

    if tab_lig:
        with tab_lig:
            df_lv = df_v[df_v["Fase"] != "Regular"].reset_index(drop=True)
            # Mostramos Fase para saber si es Cuartos o Semifinal
            df_ed_lig = st.data_editor(df_lv, height=400, use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_l", column_config={"id": None})
            
            if st.button("💾 Guardar Correcciones (Liguilla)"):
                df_cl_lig = df_ed_lig.copy()
                df_cl_lig['Resultado'] = df_cl_lig['Resultado'].apply(limpiar_icono)
                pd_final_lig = pd.concat([df[df["Fase"] == "Regular"], df_cl_lig], ignore_index=True)
                guardar_correcciones(pd_final_lig)
                st.rerun()
