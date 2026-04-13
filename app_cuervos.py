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
    # Esta función limpia la tabla y sube todo el dataframe corregido
    df_completo = df_completo.dropna(subset=['Equipo Rival'])
    if "id" in df_completo.columns:
        df_completo = df_completo.drop(columns=["id"])
    
    try:
        # Borrar todo (neq id 0 borra todo) y reinsertar
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

def generar_excel(df_reg):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_reg.to_excel(writer, index=False, sheet_name='Fase Regular')
    return output.getvalue()

def generar_pdf(df_reg):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Reporte Cuervos - Fase Regular", ln=True, align='C')
    pdf.ln(10)
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
    fases = ["Regular", "Cuartos", "Semifinal", "Final", "Eliminado", "Campeon"]
    st.session_state.estado_torneo = st.selectbox("Fase Actual:", fases, index=fases.index(st.session_state.estado_torneo))
    st.divider()
    if st.button("🔄 Refrescar Datos (Forzar)"):
        st.cache_data.clear()
        st.rerun()

# Interfaz Header (Exactamente como la captura)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<h1 style='text-align: center;'>Gestor de Temporada: Cuervos</h1>", unsafe_allow_html=True)

df_reg = df[df["Fase"] == "Regular"]
pts = int(df_reg["Puntos"].sum()) if not df_reg.empty else 0
df_j = df_reg[~df_reg["Resultado"].astype(str).str.contains("Pendiente", na=False)]
jj = len(df_j)
jg = len(df_j[df_j["Resultado"].astype(str).str.contains("Victoria")])
je = len(df_j[df_j["Resultado"].astype(str).str.contains("Empate")])
jp = len(df_j[df_j["Resultado"].astype(str).str.contains("Derrota")])
gf = int(df_j["Goles a Favor"].sum()) if not df_j.empty else 0
gc = int(df_j["Goles en Contra"].sum()) if not df_j.empty else 0

c_pts, c_stats = st.columns([1, 3])
c_pts.metric("Puntos", f"{pts} pts")
c_stats.markdown(f"""<div style='display:flex; justify-content:space-around; padding-top:20px;'>
    <div style='text-align:center;'><small>J.J</small><br><b>{jj}</b></div>
    <div style='text-align:center;'><small>J.G</small><br><b>{jg}</b></div>
    <div style='text-align:center;'><small>J.E</small><br><b>{je}</b></div>
    <div style='text-align:center;'><small>J.P</small><br><b>{jp}</b></div>
    <div style='text-align:center;'><small>G.F</small><br><b>{gf}</b></div>
    <div style='text-align:center;'><small>G.C</small><br><b>{gc}</b></div></div>""", unsafe_allow_html=True)
st.divider()

col_f, col_h = st.columns([2, 3])

# --- Columna Izquierda: Registro ---
with col_f:
    if st.session_state.estado_torneo == "Regular":
        st.subheader("Registrar Partido")
        suffix = st.session_state.contador_form
        max_j = pd.to_numeric(df_reg["Jornada"], errors='coerce').max()
        next_j = int(max_j) + 1 if pd.notna(max_j) else 1
        
        st.number_input("Jornada", value=next_j, disabled=True, key=f"j_{suffix}")
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
                
                nuevo_partido = {"Jornada": next_j, "Fase": "Regular", "Equipo Rival": rival.strip(), 
                                 "Goles a Favor": gf_i, "Goles en Contra": gc_i, "Resultado": r, "Puntos": p}
                
                # Insertar directo en Supabase
                try:
                    supabase.table("resultados").insert(nuevo_partido).execute()
                    limpiar_formulario()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al conectar con DB: {e}")

# --- Columna Derecha: Tablas ---
with col_h:
    st.markdown("💡 *Doble clic para editar. Para borrar, selecciona fila y presiona Suprimir.*")
    t1, t2 = st.tabs(["Fase Regular", "Liguilla"])
    
    df_v = df.copy()
    if not df_v.empty:
        df_v['Resultado'] = df_v['Resultado'].apply(obtener_icono)
        
    with t1:
        df_rv = df_v[df_v["Fase"] == "Regular"].reset_index(drop=True)
        # Ocultar ID y Fase en la interfaz
        columnas_ocultas = {"id": None, "Fase": None}
        df_ed = st.data_editor(df_rv, height=400, use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_r", column_config=columnas_ocultas)
        
        if st.button("💾 Guardar Correcciones"):
            df_cl = df_ed.copy()
            df_cl['Resultado'] = df_cl['Resultado'].apply(limpiar_icono)
            pd_final = pd.concat([df_cl, df[df["Fase"] != "Regular"]], ignore_index=True)
            guardar_correcciones(pd_final)
            st.rerun()
            
        c_p, c_x = st.columns(2)
        df_exp = df_ed.copy()
        if "id" in df_exp.columns: df_exp = df_exp.drop(columns=["id"])
        df_exp['Resultado'] = df_exp['Resultado'].apply(limpiar_icono)
        
        if FPDF_DISPONIBLE: 
            c_p.download_button("📄 PDF", generar_pdf(df_exp), "Cuervos_Reporte.pdf")
        c_x.download_button("📊 Excel", generar_excel(df_exp), "Cuervos_Reporte.xlsx")

    with t2:
        df_lv = df_v[df_v["Fase"] != "Regular"].reset_index(drop=True)
        st.data_editor(df_lv, use_container_width=True, hide_index=True, column_config={"id": None, "Jornada": None, "Puntos": None})
