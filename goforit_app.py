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
SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"

if not os.path.exists(LOGO_PATH):
    os.makedirs(LOGO_PATH, exist_ok=True)

st.set_page_config(page_title="Go For It | Consultoría Pro", layout="wide")

if 'form_reset' not in st.session_state:
    st.session_state.form_reset = 0

# --- FUNCIONES ---
def leer_datos():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        return df.dropna(subset=['Empresa'])
    except:
        return pd.DataFrame(columns=["Empresa", "Dimensión", "Foco", "Nombre", "Actual", "Objetivo", "Brecha", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"])

def guardar_fila_google(datos_dict):
    try:
        response = requests.post(SCRIPT_URL, json=datos_dict)
        return response.status_code == 200
    except:
        return False

# --- NAVEGACIÓN ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

st.sidebar.title("🚀 Go For It Cloud")
empresa_sel = st.sidebar.selectbox("Seleccione Cliente:", ["-- Nuevo Proyecto --"] + empresas_list)

dimensiones = ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]

if empresa_sel == "-- Nuevo Proyecto --":
    with st.sidebar.expander("✨ Registrar Empresa", expanded=True):
        nueva = st.text_input("Nombre de la Empresa:")
        logo_subido = st.file_uploader("Subir Logo", type=["png", "jpg"])
        if st.button("Activar Proyecto"):
            if nueva:
                guardar_fila_google({
                    "Empresa": nueva, "Dimensión": "Alineación Estratégica", "Foco": "General", 
                    "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Brecha": 0,
                    "Facilita": "", "Dificulta": "", "No_Hacemos": "", "Accion_1": "", "Accion_2": ""
                })
                if logo_subido: Image.open(logo_subido).save(os.path.join(LOGO_PATH, f"{nueva}.png"))
                st.rerun()
    st.stop()

# --- INTERFAZ PRINCIPAL ---
df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

col_l, col_r = st.columns([1, 4])
with col_l:
    if os.path.exists(logo_file): st.image(logo_file, width=130)
with col_r:
    st.title(f"Diagnóstico: {empresa_sel}")

tab1, tab2, tab3 = st.tabs(["📝 Evaluación", "📊 Radar & Brechas", "📋 Resumen Ejecutivo"])

# --- TAB 1: EVALUACIÓN ---
with tab1:
    focos_existentes = sorted(df_empresa['Foco'].unique().tolist()) if not df_empresa.empty else []
    nombres_existentes = sorted(df_empresa['Nombre'].unique().tolist()) if not df_empresa.empty else []

    st.subheader("Registro de Diagnóstico")
    
    # 1. SELECTORES DE MODO (FUERA DEL FORM PARA REACTIVIDAD)
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        modo_foco = st.radio("¿Foco?", ["Existente", "Nuevo"], horizontal=True, key=f"m_foco_{st.session_state.form_reset}")
    with col_m2:
        modo_nom = st.radio("¿Participante?", ["Existente", "Nuevo"], horizontal=True, key=f"m_nom_{st.session_state.form_reset}")

    # 2. FORMULARIO
    with st.form(key=f"main_form_{st.session_state.form_reset}"):
        c1, c2 = st.columns(2)
        dim = c1.selectbox("Pilar Estratégico:", dimensiones)
        
        # Lógica Foco
        if modo_foco == "Existente" and focos_existentes:
            foc = c2.selectbox("Seleccione Foco:", focos_existentes)
        else:
            foc = c2.text_input("Escriba el Foco:", value="General")
        
        st.divider()
        ca, cb, cc = st.columns([2, 1, 1])
        
        # Lógica Nombre
        if modo_nom == "Existente" and nombres_existentes:
            nom = ca.selectbox("Seleccione Participante:", nombres_existentes)
        else:
            nom = ca.text_input("Nombre del Participante:")
            
        act = cb.slider("Nivel Actual", 1, 10, 5)
        obj = cc.slider("Nivel Objetivo", 1, 10, 8)
        
        st.divider()
        t1, t2 = st.columns(2)
        f_fac = t1.text_area("¿Qué facilita el proceso?", height=80)
        f_dif = t1.text_area("¿Qué lo dificulta?", height=80)
        f_no = t2.text_area("¿Qué NO estamos haciendo?", height=175)
        
        a1 = st.text_input("Acción Inmediata 1:")
        a2 = st.text_input("Acción Inmediata 2:")
        
        if st.form_submit_button("💾 Guardar Datos"):
            if nom and foc:
                datos = {
                    "Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom,
                    "Actual": act, "Objetivo": obj, "Brecha": obj - act,
                    "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no,
                    "Accion_1": a1, "Accion_2": a2
                }
                if guardar_fila_google(datos):
                    st.session_state.form_reset += 1 # Esto limpia los campos al recargar
                    st.success("Guardado exitoso.")
                    st.rerun()
                else:
                    st.error("Error de conexión.")

# --- TAB 2 Y TAB 3 (SIN CAMBIOS) ---
with tab2:
    if not df_empresa.empty:
        st.subheader("Radar Estratégico")
        # ... (resto del código de radar igual que antes)
        res_radar = []
        for d in dimensiones:
            sub = df_empresa[df_empresa['Dimensión'] == d]
            res_radar.append({
                "Dimensión": d, 
                "Actual": round(sub['Actual'].mean(), 1) if not sub.empty else 0, 
                "Objetivo": round(sub['Objetivo'].mean(), 1) if not sub.empty else 0
            })
        df_p = pd.DataFrame(res_radar)
        df_p["Brecha"] = df_p["Objetivo"] - df_p["Actual"]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta'))
        fig.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy'))
        st.plotly_chart(fig, use_container_width=True)
        
        st.table(df_p.style.format({"Actual": "{:.1f}", "Objetivo": "{:.1f}", "Brecha": "{:.1f}"}))

with tab3:
    if not df_empresa.empty:
        st.dataframe(df_empresa)