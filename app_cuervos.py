import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestor Cuervos", page_icon="🦅", layout="wide")

# Fondo oscuro "Peste Negra" usando CSS inyectado
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stButton>button { background-color: #30363d; border: 1px solid #8b949e; color: #ffffff; }
    .stButton>button:hover { border-color: #ff4b4b; color: #ff4b4b; }
    div[data-testid="stMetricValue"] { color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    # Asegúrate de tener estas variables en tu archivo .streamlit/secrets.toml
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- FUNCIONES DE BASE DE DATOS ---
def cargar_datos():
    respuesta = supabase.table("resultados").select("*").order("Jornada").execute()
    return respuesta.data

def calcular_estadisticas(datos):
    pts = jj = jg = je = jp = gf = gc = 0
    for p in datos:
        if p.get("Resultado") and "Pendiente" not in p["Resultado"]:
            jj += 1
            gf += p.get("Goles a Favor", 0)
            gc += p.get("Goles en Contra", 0)
            
            res = p["Resultado"]
            if "Victoria" in res:
                jg += 1
                pts += 3
            elif "Derrota" in res:
                jp += 1
            elif "Empate" in res:
                je += 1
                if "(G-SO)" in res: pts += 2
                elif "(P-SO)" in res: pts += 1
                else: pts += 1
    return pts, jj, jg, je, jp, gf, gc

# Cargar los datos al inicio
datos_partidos = cargar_datos()

# --- BARRA LATERAL (MENÚ ADMIN) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: white;'>🛡️ LA PESTE NEGRA</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.header("⚙️ Menú Admin")
    st.info("📌 Fase Actual: Regular")
    
    # Botón rojo para cerrar fase
    st.markdown("""
        <style>
        div.stButton > button:first-child { background-color: #ff4b4b; color: white; border: none; }
        </style>
    """, unsafe_allow_html=True)
    st.button("🔒 Cerrar Fase Regular")
    
    if st.button("🔄 Refrescar Pantalla"):
        st.rerun()
        
    st.markdown("---")
    
    # --- NUEVA SECCIÓN: RESTAURAR DESDE EXCEL ---
    st.subheader("📥 Restaurar BD desde Excel")
    archivo_subido = st.file_uploader("Sube el archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo_subido is not None:
        if st.button("⚠️ Sobreescribir Nube"):
            try:
                # Leer el excel
                df = pd.read_excel(archivo_subido)
                # Borrar todo en Supabase (usamos un filtro que siempre sea verdadero)
                supabase.table("resultados").delete().neq("Jornada", 0).execute()
                # Insertar los nuevos datos
                registros = df.to_dict('records')
                # Limpiar la columna 'id' si viene en el Excel para que Supabase genere unos nuevos
                for reg in registros:
                    if 'id' in reg: del reg['id']
                
                supabase.table("resultados").insert(registros).execute()
                st.success("¡Base de datos restaurada con éxito!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al restaurar: {e}")

    st.markdown("---")
    st.header("Danger Zone")
    confirmar_reinicio = st.checkbox("Confirmar reinicio de temporada")
    if confirmar_reinicio:
        if st.button("♻️ Nueva Temporada"):
            supabase.table("resultados").delete().neq("Jornada", 0).execute()
            st.success("Temporada reiniciada.")
            st.rerun()


# --- PANEL PRINCIPAL ---
st.title("Gestor de Temporada: Cuervos 🔗")

# Estadísticas
if datos_partidos:
    pts, jj, jg, je, jp, gf, gc = calcular_estadisticas(datos_partidos)
else:
    pts = jj = jg = je = jp = gf = gc = 0

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
col1.metric("Puntos", f"{pts} pts")
col2.metric("J.J", jj)
col3.metric("J.G", jg)
col4.metric("J.E", je)
col5.metric("J.P", jp)
col6.metric("G.F", gf)
col7.metric("G.C", gc)

st.markdown("---")

# --- FORMULARIO DE CAPTURA ---
st.subheader("Registrar Partido - Regular")

# Calcular siguiente jornada automáticamente
siguiente_jornada = max([p["Jornada"] for p in datos_partidos]) + 1 if datos_partidos else 1

with st.form("form_captura", clear_on_submit=True):
    col_j, col_r = st.columns([1, 3])
    jornada = col_j.number_input("Partido #", value=siguiente_jornada, disabled=True)
    rival = col_r.text_input("Equipo Rival")
    
    pendiente = st.checkbox("⏳ Dejar como Pendiente")
    
    col_gc, col_gr = st.columns(2)
    goles_c = col_gc.number_input("Goles Cuervos", min_value=0, value=0, step=1)
    goles_r = col_gr.number_input("Goles Rival", min_value=0, value=0, step=1)
    
    ganador_so = "Ninguno"
    if goles_c == goles_r:
        ganador_so = st.radio("Ganador SO:", ["Ninguno", "Cuervos", "Rival"], horizontal=True)
        
    enviado = st.form_submit_button("Guardar Partido")
    
    if enviado:
        if not rival:
            st.error("Debes escribir el nombre del equipo rival.")
        else:
            resultado_final = "Pendiente"
            if not pendiente:
                if goles_c > goles_r: resultado_final = "Victoria"
                elif goles_c < goles_r: resultado_final = "Derrota"
                else:
                    if ganador_so == "Cuervos": resultado_final = "Empate (G-SO)"
                    elif ganador_so == "Rival": resultado_final = "Empate (P-SO)"
                    else: resultado_final = "Empate"
            
            nuevo_partido = {
                "Jornada": siguiente_jornada,
                "Equipo Rival": rival,
                "Goles a Favor": goles_c,
                "Goles en Contra": goles_r,
                "Resultado": resultado_final
            }
            supabase.table("resultados").insert(nuevo_partido).execute()
            st.success("Partido guardado en la nube.")
            st.rerun()

# --- TABLA DE RESULTADOS ---
st.markdown("---")
st.subheader("Fase Regular")
st.caption("💡 Para editar o borrar, hazlo desde tu celular en la aplicación nativa.")

if datos_partidos:
    df_mostrar = pd.DataFrame(datos_partidos)
    # Limpiar columnas innecesarias para la vista
    if 'id' in df_mostrar.columns:
        df_mostrar = df_mostrar.drop(columns=['id'])
    if 'created_at' in df_mostrar.columns:
        df_mostrar = df_mostrar.drop(columns=['created_at'])
        
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
else:
    st.info("No hay partidos registrados aún.")
