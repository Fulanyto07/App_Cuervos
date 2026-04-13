import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from PIL import Image
import io
import os

# Librerías opcionales para exportar
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# 1. Configuración de la página
st.set_page_config(page_title="Gestor Cuervos Cloud", page_icon="🐦‍⬛", layout="wide")

# 2. Conexión a Google Sheets
# Nota: Configuraremos las credenciales en el paso 3
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos_cloud():
    try:
        # Intenta leer la hoja llamada "Resultados"
        return conn.read(worksheet="Resultados", ttl=0)
    except:
        # Si la hoja está vacía o no existe, crea la estructura inicial
        return pd.DataFrame(columns=["Jornada", "Fase", "Equipo Rival", "Goles a Favor", "Goles en Contra", "Resultado", "Puntos"])

def guardar_datos_cloud(df_nuevo):
    # Limpieza de filas vacías antes de subir
    df_nuevo = df_nuevo.dropna(subset=['Equipo Rival'])
    df_nuevo = df_nuevo[~df_nuevo['Equipo Rival'].astype(str).str.strip().isin(['nan', 'None', ''])]
    conn.update(worksheet="Resultados", data=df_nuevo)

# --- (Las funciones de iconos, marcador, pdf y excel siguen igual) ---
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
    else: return (2, "Empate (G-SO)") if so_ganador == "Cuervos" else (1, "Empate (P-SO)")

# Carga inicial desde la nube
df = cargar_datos_cloud()

# --- INTERFAZ PRINCIPAL (Dashboard y Registro) ---
# (Aquí va el resto de tu lógica de Streamlit que ya conocemos)
# Al final de cada acción de "Guardar", cambiaremos el df.to_csv por:
# guardar_datos_cloud(df)

st.info("⚠️ Para que esta app funcione en la nube, necesitamos configurar el 'Secrets' en Streamlit Cloud con tu enlace de Google Sheets.")