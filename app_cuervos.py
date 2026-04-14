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
    ids_mod = set(df_modificado['id'].dropna())
    ids_a_borrar = ids_orig - ids_mod
    
    try:
        for id_b in ids_a_borrar:
            supabase.table("resultados").delete().eq("id", id_b).execute()
        
        records = []
        for _, row in df_modificado.iterrows():
            rec = row.to_dict()
            if pd.isna(rec.get('id')): 
                rec.pop('id', None)
            records.append(rec)
            
        if records: 
            supabase.table("resultados").upsert(records).execute()
            
        st.cache_data.clear()
        st.success("✅ Base de datos actualizada.")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

def reiniciar_sistema():
    try:
        res = supabase.table("resultados").select("id").execute()
        for r in res.data:
            supabase.table("resultados").delete().eq("id", r["id"]).execute()
            
        st.session_state.update({
            "estado_torneo": "Regular",
            "temporada_terminada": False,
            "clasifico_liguilla": False,
            "preguntar_clasificacion": False
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
    res_s = str(res)
    if "Victoria" in res_s: return "✅ " + res_s
    if "Empate" in res_s: return "➖ " + res_s
    if "Pendiente" in res_s: return "⏳ " + res_s
    return "❌ " + res_s

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

# 🚨 CEREBRO MAESTRO BLINDADO 🚨
# La Base de Datos dicta la realidad. No más peleas con los botones.
df_liguilla = df[df['Fase'].isin(['Cuartos', 'Semifinal', 'Final'])]

if not df_liguilla.empty:
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
    if st.session_state.clasifico_liguilla:
        st.session_state.estado_torneo = "Cuartos"
    else:
        st.session_state.estado_torneo = "Regular"

with st.sidebar:
    if os.path.exists("cuervos_logo.png"): st.image(Image.open("cuervos_logo.png"), width=120)
    st.header("⚙️ Menú Admin")
    st.info(f"📌 **Fase Actual:** {st.session_state.estado_torneo}")
    st.divider()
    
    if not st.session_state.temporada_terminada:
        if st.button("🔒 Cerrar Fase Regular", type="primary", use_container_width=True):
            st.session_state.preguntar_clasificacion = True
        
        if st.session_state.preguntar_clasificacion:
            st.warning("¿Clasificaron a Liguilla?")
            c1, c2 = st.columns(2)
            if c1.button("SÍ", use_container_width=True):
                st.session_state.update({"clasifico_liguilla": True, "temporada_terminada": True, "preguntar_clasificacion": False, "estado_torneo": "Cuartos"})
                limpiar_formulario()
                st.balloons(); st.rerun()
            if c2.button("NO", use_container_width=True):
                st.session_state.update({"clasifico_liguilla": False, "temporada_terminada": True, "preguntar_clasificacion": False, "estado_torneo": "Eliminado"})
                st.rerun()
    else:
        if st.session_state.estado_torneo == "Campeon":
            st.success("🏆 ¡SOMOS CAMPEONES!")
        elif st.session_state.estado_torneo == "Eliminado":
            st.error("❌ Torneo Finalizado")
        else:
            st.success("🏆 Liguilla Activa")
        
        # Bloqueo de seguridad: Si ya hay juegos de Liguilla, escondemos el botón de Deshacer para evitar el Limbo.
        if df_liguilla.empty:
            if st.button("⏪ Deshacer Cierre", use_container_width=True):
                st.session_state.update({"temporada_terminada": False, "clasifico_liguilla": False, "estado_torneo": "Regular", "preguntar_clasificacion": False})
                limpiar_formulario()
                st.rerun()
        else:
            st.caption("💡 *Edita directamente la tabla para modificar o corregir la Liguilla.*")

    st.divider()
    if st.button("🔄 Refrescar Pantalla", use_container_width=True):
        st.cache_data.clear(); st.rerun()

    st.divider()
    st.subheader("Danger Zone")
    confirma = st.checkbox("Confirmar reinicio de temporada")
    if st.button("♻️ Nueva Temporada", type="secondary", disabled=not confirma, use_container_width=True):
        reiniciar_sistema()

# Dashboard
st.markdown("<h1 style='text-align: center;'>Gestor de Temporada: Cuervos</h1>", unsafe_allow_html=True)
if st.session_state.estado_torneo == "Campeon":
    st.balloons()
    st.success("🎉 ¡FELICIDADES CUERVOS! HAN GANADO EL CAMPEONATO. 🎉")

df_reg = df[df["Fase"] == "Regular"]
df_j = df_reg[~df_reg["Resultado"].astype(str).str.contains("Pendiente", na=False)]

stats_dict = {
    "JJ": len(df_j),
    "JG": len(df_j[df_j["Resultado"].astype(str).str.contains("Victoria", na=False)]),
    "JE": len(df_j[df_j["Resultado"].astype(str).str.contains("Empate", na=False)]),
    "JP": len(df_j[df_j["Resultado"].astype(str).str.contains("Derrota", na=False)]),
    "GF": int(pd.to_numeric(df_j["Goles a Favor"], errors='coerce').fillna(0).sum()),
    "GC": int(pd.to_numeric(df_j["Goles en Contra"], errors='coerce').fillna(0).sum()),
    "PTS": int(pd.to_numeric(df_reg["Puntos"], errors='coerce').fillna(0).sum())
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

# --- Columna Izquierda: Formulario ---
with col_f:
    fase = st.session_state.estado_torneo
    if fase in ["Regular", "Cuartos", "Semifinal", "Final"]:
        st.subheader(f"Registrar Partido - {fase}")
        suffix = st.session_state.contador_form
        
        df_fase = df[df["Fase"] == fase]
        df_pend = df_fase[df_fase["Resultado"].astype(str).str.contains("Pendiente", na=False)]
        
        modo = st.radio("Acción:", ["Nuevo Partido", "Actualizar Pendiente"], horizontal=True, key=f"m_{suffix}") if not df_pend.empty else "Nuevo Partido"
        
        if modo == "Nuevo Partido":
            max_j = pd.to_numeric(df_fase["Jornada"], errors='coerce').max()
            num_p = int(max_j) + 1 if pd.notna(max_j) else 1
            
            st.number_input("Partido #", value=num_p, disabled=True, key=f"j_{suffix}")
            rival = st.text_input("Equipo Rival", key=f"r_{suffix}")
            pnd = st.checkbox("⏳ Dejar como Pendiente", key=f"p_{suffix}")
            id_upd = None
        else:
            opciones = df_pend["Jornada"].astype(str) + " - " + df_pend["Equipo Rival"]
            sel = st.selectbox("Seleccionar partido a actualizar:", opciones.tolist(), key=f"s_{suffix}")
            
            match_row = df_pend[opciones == sel]
            if not match_row.empty:
                row = match_row.iloc[0]
                id_upd = row["id"]
                rival = row["Equipo Rival"]
                num_p_seguro = int(pd.to_numeric(row["Jornada"], errors='coerce')) if pd.not
