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
@st.cache_data(ttl=30)
def leer_datos():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        df = df.dropna(subset=['Empresa'])
        
        # SEGURIDAD: Mapeo de nombres si la columna vieja existe o creación de la nueva
        if "Distintos" in df.columns and "Capacidades_Distintivas" not in df.columns:
            df = df.rename(columns={"Distintos": "Capacidades_Distintivas"})
        
        columnas_necesarias = ["Capacidades_Distintivas", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"]
        for col in columnas_necesarias:
            if col not in df.columns:
                df[col] = ""
        return df
    except:
        return pd.DataFrame(columns=["Empresa", "Dimensión", "Foco", "Nombre", "Actual", "Objetivo", "Brecha", "Facilita", "Dificulta", "No_Hacemos", "Capacidades_Distintivas", "Accion_1", "Accion_2"])

def guardar_fila_google(datos_dict):
    try:
        response = requests.post(SCRIPT_URL, json=datos_dict, timeout=10)
        return response.status_code == 200
    except: return False

def generar_word(empresa, df_filtrado, fig, logo_p):
    doc = Document()
    doc.add_heading(f'Informe Estratégico: {empresa}', 0)
    if os.path.exists(logo_p):
        try: doc.add_picture(logo_p, width=Inches(1.5))
        except: pass
    
    doc.add_heading('Detalle de Hallazgos y Capacidades Distintivas', level=1)
    for _, row in df_filtrado.iterrows():
        doc.add_heading(f"{row['Dimensión']} - {row['Foco']}", level=2)
        doc.add_paragraph(f"Participante: {row['Nombre']} | Puntaje: {row['Actual']}/{row['Objetivo']}")
        cap_dis = row['Capacidades_Distintivas'] if 'Capacidades_Distintivas' in row else ""
        doc.add_paragraph(f"Capacidades Distintivas: {cap_dis}").italic = True
        doc.add_paragraph(f"Acciones: 1. {row['Accion_1']} | 2. {row['Accion_2']}")
    
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- DATOS ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

# --- SIDEBAR ---
with st.sidebar:
    st.title("Consultoría Pro")
    st.markdown("---")
    empresa_sel = st.selectbox("🎯 Proyecto Actual:", ["-- Nuevo Proyecto --"] + empresas_list)
    
    if empresa_sel == "-- Nuevo Proyecto --":
        st.subheader("✨ Registrar Cliente")
        nueva_emp = st.text_input("Nombre de la Empresa:")
        logo_subido = st.file_uploader("Subir Logo:", type=["png", "jpg"])
        if st.button("🚀 Activar Proyecto"):
            if nueva_emp:
                guardar_fila_google({"Empresa": nueva_emp, "Dimensión": "Alineación Estratégica", "Foco": "General", "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Brecha": 0, "Capacidades_Distintivas": ""})
                if logo_subido: Image.open(logo_subido).save(os.path.join(LOGO_PATH, f"{nueva_emp}.png"))
                st.rerun()
        st.stop()

df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Radar Analítico", "📋 Reporte Ejecutivo"])

# --- TAB 1: REGISTRO ---
with tab1:
    f_ex = sorted(df_empresa['Foco'].unique().tolist())
    n_ex = sorted(df_empresa['Nombre'].unique().tolist())
    c_m1, c_m2 = st.columns(2)
    m_foco = c_m1.radio("📌 Área / Foco:", ["Existente", "Nuevo"], horizontal=True, key=f"f_{st.session_state.form_reset}")
    m_nom = c_m2.radio("👤 Participante:", ["Existente", "Nuevo"], horizontal=True, key=f"n_{st.session_state.form_reset}")
    
    with st.form(key=f"form_{st.session_state.form_reset}"):
        f1, f2 = st.columns(2)
        dim = f1.selectbox("Pilar Estratégico:", ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"])
        foc = f2.selectbox("Foco Actual:", f_ex) if m_foco == "Existente" and f_ex else f2.text_input("Nuevo Foco:", value="General")
        fa, fb, fc = st.columns([2, 1, 1])
        nom = fa.selectbox("Nombre:", n_ex) if m_nom == "Existente" and n_ex else fa.text_input("Nuevo Participante:")
        act = fb.slider("Hoy", 1, 10, 5)
        obj = fc.slider("Meta", 1, 10, 8)
        
        st.markdown("### 🗣️ Diagnóstico Cualitativo")
        t1, t2 = st.columns(2)
        f_fac = t1.text_area("¿Qué facilita?", height=70)
        f_dif = t1.text_area("¿Qué dificulta?", height=70)
        f_no = t2.text_area("¿Qué NO hacemos?", height=70)
        # Cambio de nombre solicitado:
        f_cap = t2.text_area("¿Qué capacidades distintivas tenemos?", height=70, help="Habilidades únicas o recursos críticos de la empresa.")
        
        a1 = st.text_input("Acción 1:"); a2 = st.text_input("Acción 2:")
        
        if st.form_submit_button("✅ Guardar Registro"):
            if nom and foc:
                guardar_fila_google({
                    "Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom, 
                    "Actual": act, "Objetivo": obj, "Brecha": obj-act,
                    "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no, 
                    "Capacidades_Distintivas": f_cap,
                    "Accion_1": a1, "Accion_2": a2
                })
                st.session_state.form_reset += 1
                st.rerun()

# --- LÓGICA FILTROS ---
def filtrar(df, k):
    st.markdown("### 🔍 Filtros de Análisis")
    c1, c2, c3 = st.columns(3)
    p = c1.multiselect("Pilares:", df['Dimensión'].unique(), default=df['Dimensión'].unique(), key=f"p_{k}")
    f = c2.multiselect("Focos:", df['Foco'].unique(), default=df['Foco'].unique(), key=f"f_{k}")
    n = c3.multiselect("Participantes:", df['Nombre'].unique(), default=df['Nombre'].unique(), key=f"n_{k}")
    return df[(df['Dimensión'].isin(p)) & (df['Foco'].isin(f)) & (df['Nombre'].isin(n))]

# --- TAB 2: RADAR ---
with tab2:
    if not df_empresa.empty:
        df_f = filtrar(df_empresa, "rad")
        if not df_f.empty:
            res = []
            for d in ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]:
                sub = df_f[df_f['Dimensión'] == d]
                res.append({"Dimensión": d, "Actual": sub['Actual'].mean() if not sub.empty else 0, "Objetivo": sub['Objetivo'].mean() if not sub.empty else 0})
            df_p = pd.DataFrame(res); df_p["Brecha"] = df_p["Objetivo"] - df_p["Actual"]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta'))
            fig.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy'))
            st.plotly_chart(fig, use_container_width=True)
            st.table(df_p.style.map(lambda x: 'background-color: #fecaca' if x > 2 else 'background-color: #bbf7d0', subset=['Brecha']).format({"Actual": "{:.1f}", "Objetivo": "{:.1f}", "Brecha": "{:.1f}"}))

# --- TAB 3: REPORTE ---
with tab3:
    if not df_empresa.empty:
        df_r = filtrar(df_empresa, "rep")
        col_t, col_b = st.columns([4, 1])
        col_t.subheader("Resumen de Compromisos")
        with col_b:
            w_bin = generar_word(empresa_sel, df_r, None, logo_file)
            st.download_button("📥 Reporte Word", data=w_bin, file_name=f"Informe_{empresa_sel}.docx")
        
        # Tabla resumen con el nuevo nombre de columna
        st.dataframe(df_r[["Dimensión", "Foco", "Nombre", "Actual", "Brecha", "Capacidades_Distintivas", "Accion_1"]].sort_values(by="Brecha", ascending=False), use_container_width=True)