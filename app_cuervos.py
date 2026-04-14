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

# 2. Conexión a Supabase (¡ADÍOS GOOGLE SHEETS!)
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

def reiniciar_sistema():
    try:
        supabase.table("resultados").delete().neq("id", 0).execute()
        st.session_state.update({
            "estado_torneo": "Regular",
            "temporada_terminada": False,
            "clasifico_liguilla": False,
            "preguntar_clasificacion": False
        })
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Error al reiniciar: {e}")

# 5. Lógica Deportiva y Reportes
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

# Lógica de detección automática de estado según los datos
if not df.empty:
    if ((df['Fase'] == 'Final') & (df['Resultado'].str.contains('Victoria|G-SO'))).any():
        st.session_state.estado_torneo = "Campeon"
        st.session_state.temporada_terminada = True
        st.session_state.clasifico_liguilla = True
    elif ((df['Fase'].isin(['Cuartos', 'Semifinal', 'Final'])) & (df['Resultado'].str.contains('Derrota|P-SO'))).any():
        st.session_state.estado_torneo = "Eliminado"
        st.session_state.temporada_terminada = True
    elif st.session_state.clasifico_liguilla:
        if not df[df['Fase'] == 'Semifinal'].empty: st.session_state.estado_torneo = "Final"
        elif not df[df['Fase'] == 'Cuartos'].empty: st.session_state.estado_torneo = "Semifinal"

# Barra Lateral
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
                st.balloons(); st.rerun()
            if c2.button("NO", use_container_width=True):
                st.session_state.update({"clasifico_liguilla": False, "temporada_terminada": True, "preguntar_clasificacion": False, "estado_torneo": "Eliminado"})
                st.rerun()
    else:
        if st.session_state.estado_torneo == "Campeon":
            st.success("🏆 ¡SOMOS CAMPEONES!")
        elif st.session_state.estado_torneo == "Eliminado":
            st.error("❌ Torneo Finalizado")
        
        if st.button("⏪ Deshacer Cierre", use_container_width=True):
            st.session_state.update({"temporada_terminada": False, "clasifico_liguilla": False, "estado_torneo": "Regular"})
            st.rerun()

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
stats = {"JJ": len(df_j), "JG": len(df_j[df_j["Resultado"].astype(str).str.contains("Victoria", na=False)]), "PTS": int(df_reg["Puntos"].sum()) if not df_reg.empty else 0}

c_pts, c_stats = st.columns([1, 3])
c_pts.metric("Puntos", f"{stats['PTS']} pts")
c_stats.write(f"Partidos Jugados: {stats['JJ']} | Victorias: {stats['JG']}")
st.divider()

col_f, col_h = st.columns([2, 3])

# --- Columna Izquierda: Formulario Inteligente ---
with col_f:
    fase = st.session_state.estado_torneo
    if fase in ["Regular", "Cuartos", "Semifinal", "Final"]:
        st.subheader(f"Registro: {fase}")
        suffix = st.session_state.contador_form
        df_pend = df[df["Resultado"].astype(str).str.contains("Pendiente", na=False)]
        modo = st.radio("Acción:", ["Nuevo Partido", "Actualizar Pendiente"], horizontal=True, key=f"m_{suffix}") if not df_pend.empty else "Nuevo Partido"
        
        if modo == "Nuevo Partido":
            num_p = int(pd.to_numeric(df[df["Fase"]==fase]["Jornada"], errors='coerce').max() or 0) + 1
            st.number_input("Partido #", value=num_p, disabled=True, key=f"j_{suffix}")
            rival = st.text_input("Equipo Rival", key=f"r_{suffix}")
            pnd = st.checkbox("⏳ Dejar como Pendiente", key=f"p_{suffix}")
            id_upd = None
        else:
            sel = st.selectbox("Seleccionar partido a actualizar:", df_pend["Jornada"].astype(str) + " - " + df_pend["Equipo Rival"], key=f"s_{suffix}")
            row = df_pend.iloc[df_pend["Jornada"].astype(str).tolist().index(sel.split(" - ")[0])]
            num_p, rival, pnd, id_upd = row["Jornada"], row["Equipo Rival"], False, row["id"]
            st.number_input("Partido #", value=int(num_p), disabled=True, key=f"ju_{id_upd}_{suffix}")
            st.text_input("Equipo Rival", value=rival, disabled=True, key=f"ru_{id_upd}_{suffix}")

        gf, gc, so = 0, 0, None
        if not pnd:
            cx, cy = st.columns(2)
            gf = cx.number_input("Goles Cuervos", min_value=0, key=f"gf_{suffix}")
            gc = cy.number_input("Goles Rival", min_value=0, key=f"gc_{suffix}")
            if gf == gc: so = st.radio("Ganador SO:", ["Cuervos", "Rival"], horizontal=True, key=f"so_{suffix}")

        txt_boton = "Guardar Partido" if modo == "Nuevo Partido" else "Actualizar Marcador"

        if st.button(txt_boton, type="primary", use_container_width=True):
            if rival.strip():
                p, r = (0, "Pendiente") if pnd else procesar_marcador(gf, gc, so)
                data = {"Jornada": num_p, "Fase": fase, "Equipo Rival": rival, "Goles a Favor": gf, "Goles en Contra": gc, "Resultado": r, "Puntos": p}
                
                try:
                    if id_upd: 
                        supabase.table("resultados").update(data).eq("id", int(id_upd)).execute()
                    else: 
                        supabase.table("resultados").insert(data).execute()
                    
                    st.cache_data.clear()
                    limpiar_formulario()
                    
                    # Salto automático
                    if not pnd:
                        if fase == "Cuartos": st.session_state.estado_torneo = "Semifinal"
                        elif fase == "Semifinal": st.session_state.estado_torneo = "Final"
                        elif fase == "Final": st.session_state.estado_torneo = "Campeon" if p == 3 or "G-SO" in r else "Eliminado"
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error con DB: {e}")

# --- Columna Derecha: Tablas ---
with col_h:
    st.markdown("💡 *Doble clic para corregir marcador manual. Suprimir para borrar fila.*")
    tabs = st.tabs(["Fase Regular", "Liguilla"]) if st.session_state.clasifico_liguilla else st.tabs(["Fase Regular"])
    
    df_v = df.copy()
    if not df_v.empty: df_v['Resultado'] = df_v['Resultado'].apply(obtener_icono)
    
    # Cálculos para el reporte
    df_reg_reporte = df[df["Fase"] == "Regular"].copy()
    df_j_reporte = df_reg_reporte[~df_reg_reporte["Resultado"].astype(str).str.contains("Pendiente", na=False)]
    stats_dict = {
        "JJ": len(df_j_reporte),
        "JG": len(df_j_reporte[df_j_reporte["Resultado"].astype(str).str.contains("Victoria", na=False)]),
        "JE": len(df_j_reporte[df_j_reporte["Resultado"].astype(str).str.contains("Empate", na=False)]),
        "JP": len(df_j_reporte[df_j_reporte["Resultado"].astype(str).str.contains("Derrota", na=False)]),
        "GF": int(df_j_reporte["Goles a Favor"].sum()) if not df_j_reporte.empty else 0,
        "GC": int(df_j_reporte["Goles en Contra"].sum()) if not df_j_reporte.empty else 0,
        "PTS": int(df_reg_reporte["Puntos"].sum()) if not df_reg_reporte.empty else 0
    }

    with tabs[0]:
        df_rv = df_v[df_v["Fase"] == "Regular"].reset_index(drop=True)
        ed_reg = st.data_editor(df_rv, use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_r", column_config={"id": None, "Fase": None})
        
        if st.button("💾 Guardar Correcciones Manuales (Regular)"):
            ed_reg['Resultado'] = ed_reg['Resultado'].apply(limpiar_icono)
            pd_f = pd.concat([ed_reg.assign(Fase="Regular"), df[df["Fase"]!="Regular"]], ignore_index=True)
            guardar_correcciones(pd_f)
            st.rerun()

        c_p, c_x = st.columns(2)
        df_exp = ed_reg.copy()
        if "id" in df_exp.columns: df_exp = df_exp.drop(columns=["id"])
        df_exp['Resultado'] = df_exp['Resultado'].apply(limpiar_icono)
        
        if FPDF_DISPONIBLE: 
            c_p.download_button("📄 PDF", generar_pdf(df_exp, stats_dict), "Cuervos_Reporte.pdf")
        c_x.download_button("📊 Excel", generar_excel(df_exp, stats_dict), "Cuervos_Reporte.xlsx")

    if st.session_state.clasifico_liguilla:
        with tabs[1]:
            df_lv = df_v[df_v["Fase"] != "Regular"].reset_index(drop=True)
            ed_lig = st.data_editor(df_lv, use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_l", column_config={"id": None, "Jornada": None, "Puntos": None})
            
            if st.button("💾 Guardar Correcciones Manuales (Liguilla)"):
                ed_lig['Resultado'] = ed_lig['Resultado'].apply(limpiar_icono)
                pd_f = pd.concat([df[df["Fase"]=="Regular"], ed_lig], ignore_index=True)
                guardar_correcciones(pd_f)
                st.rerun()
