import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import os
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Inches

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Go For It | Strategic Advisor", page_icon="🚀", layout="wide")

SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"

if not os.path.exists(LOGO_PATH):
    os.makedirs(LOGO_PATH, exist_ok=True)

if 'form_reset' not in st.session_state:
    st.session_state.form_reset = 0

# --- FUNCIONES ---
@st.cache_data(ttl=5) # Reducimos el TTL para que los cambios se vean casi instantáneos
def leer_datos():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        df = df.dropna(subset=['Empresa'])
        
        # Estandarización de columnas
        if "Distintos" in df.columns:
            df = df.rename(columns={"Distintos": "Capacidades_Distintivas"})
        
        cols = ["Capacidades_Distintivas", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"]
        for col in cols:
            if col not in df.columns: df[col] = ""
        return df
    except:
        return pd.DataFrame()

def guardar_fila_google(datos_dict):
    try:
        # Nota: Asegúrate que tu Google Apps Script busque por Empresa/Dimensión/Nombre para actualizar
        response = requests.post(SCRIPT_URL, json=datos_dict, timeout=10)
        return response.status_code == 200
    except: return False

# --- DATOS ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

# --- SIDEBAR ---
with st.sidebar:
    st.title("Consultoría Pro")
    empresa_sel = st.selectbox("🎯 Proyecto Actual:", ["-- Nuevo Proyecto --"] + empresas_list)
    
    if empresa_sel == "-- Nuevo Proyecto --":
        st.subheader("✨ Registrar Cliente")
        nueva_emp = st.text_input("Nombre de la Empresa:")
        logo_subido = st.file_uploader("Subir Logo:", type=["png", "jpg"])
        if st.button("🚀 Activar Proyecto"):
            if nueva_emp:
                guardar_fila_google({"Empresa": nueva_emp, "Dimensión": "Alineación Estratégica", "Foco": "General", "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Brecha": 0})
                if logo_subido: Image.open(logo_subido).save(os.path.join(LOGO_PATH, f"{nueva_emp}.png"))
                st.rerun()
        st.stop()

df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

tab1, tab2, tab3 = st.tabs(["📝 Registro y Edición", "📊 Radar Analítico", "📋 Reporte Ejecutivo"])

# --- TAB 1: REGISTRO CON AUTOCARGA ---
with tab1:
    st.subheader("Edición de Evaluaciones")
    st.info("Selecciona el Pilar y el Participante. Si ya existen datos, se cargarán automáticamente para su edición.")
    
    f_ex = sorted(df_empresa['Foco'].unique().tolist())
    n_ex = sorted(df_empresa['Nombre'].unique().tolist())
    
    # 1. Selectores de búsqueda (Fuera del Form para que disparen la carga)
    c_sel1, c_sel2, c_sel3 = st.columns(3)
    dim_sel = c_sel1.selectbox("Pilar Estratégico:", ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"])
    
    # Lógica para Foco (Existente o Nuevo)
    m_foco = c_sel2.toggle("Nuevo Foco", key="t_foco")
    foc_sel = c_sel2.text_input("Escriba Nuevo Foco:") if m_foco else c_sel2.selectbox("Foco Actual:", f_ex)
    
    # Lógica para Nombre (Existente o Nuevo)
    m_nom = c_sel3.toggle("Nuevo Participante", key="t_nom")
    nom_sel = c_sel3.text_input("Escriba Nuevo Nombre:") if m_nom else c_sel3.selectbox("Participante Actual:", n_ex)

    # 2. BUSCAR DATOS PREVIOS
    datos_previos = df_empresa[
        (df_empresa['Dimensión'] == dim_sel) & 
        (df_empresa['Foco'] == foc_sel) & 
        (df_empresa['Nombre'] == nom_sel)
    ]
    
    exists = not datos_previos.empty
    row = datos_previos.iloc[0] if exists else None

    # 3. Formulario con valores por defecto (Si row existe, carga; si no, vacío)
    with st.form(key=f"form_edicion_{st.session_state.form_reset}"):
        st.markdown(f"### {'✏️ Editando' if exists else '➕ Nuevo Registro'}: {nom_sel}")
        
        fa, fb = st.columns(2)
        val_act = fa.slider("Nivel Actual (Hoy)", 1, 10, int(row['Actual']) if exists else 5)
        val_obj = fb.slider("Nivel Objetivo (Meta)", 1, 10, int(row['Objetivo']) if exists else 8)
        
        st.markdown("---")
        t1, t2 = st.columns(2)
        f_fac = t1.text_area("¿Qué facilita?", value=str(row['Facilita']) if exists else "", height=80)
        f_dif = t1.text_area("¿Qué dificulta?", value=str(row['Dificulta']) if exists else "", height=80)
        f_no = t2.text_area("¿Qué NO hacemos?", value=str(row['No_Hacemos']) if exists else "", height=80)
        f_cap = t2.text_area("Capacidades Distintivas:", value=str(row['Capacidades_Distintivas']) if exists else "", height=80)
        
        a1 = st.text_input("Acción 1:", value=str(row['Accion_1']) if exists else "")
        a2 = st.text_input("Acción 2:", value=str(row['Accion_2']) if exists else "")
        
        label_boton = "🔄 Actualizar Registro" if exists else "✅ Guardar Nuevo"
        if st.form_submit_button(label_boton):
            if nom_sel and foc_sel:
                exito = guardar_fila_google({
                    "Empresa": empresa_sel, "Dimensión": dim_sel, "Foco": foc_sel, "Nombre": nom_sel, 
                    "Actual": val_act, "Objetivo": val_obj, "Brecha": val_obj - val_act,
                    "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no, 
                    "Capacidades_Distintivas": f_cap, "Accion_1": a1, "Accion_2": a2
                })
                if exito:
                    st.success("¡Sincronizado con éxito!")
                    st.session_state.form_reset += 1
                    st.cache_data.clear() # Limpia cache para forzar lectura
                    st.rerun()

# --- LAS PESTAÑAS 2 Y 3 SE MANTIENEN IGUAL QUE EN LA VERSIÓN ANTERIOR ---
# (Filtros, Radar y Tabla de Reporte)