import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import os
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Inches

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Go For It | Strategic Advisor", page_icon="🚀", layout="wide")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    [data-testid="stSidebar"] { background-color: #0f172a; color: white; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div.stButton > button { width: 100%; border-radius: 8px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
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
        return df.dropna(subset=['Empresa'])
    except:
        return pd.DataFrame(columns=["Empresa", "Dimensión", "Foco", "Nombre", "Actual", "Objetivo", "Brecha", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"])

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
    doc.add_heading('1. Análisis de Madurez Seleccionado', level=1)
    if fig:
        img_bytes = fig.to_image(format="png", engine="kaleido")
        doc.add_picture(BytesIO(img_bytes), width=Inches(5.5))
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- DATOS ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

# --- SIDEBAR (LOGICA DE CREACIÓN CORREGIDA) ---
with st.sidebar:
    st.title("Consultoría Pro")
    st.markdown("---")
    empresa_sel = st.selectbox("🎯 Proyecto Actual:", ["-- Nuevo Proyecto --"] + empresas_list)
    
    # SECCIÓN PARA CREAR EMPRESA NUEVA
    if empresa_sel == "-- Nuevo Proyecto --":
        st.subheader("✨ Registrar Cliente")
        nueva_emp = st.text_input("Nombre de la Empresa:", placeholder="Ej. INNOVIA")
        logo_subido = st.file_uploader("Subir Logo (PNG/JPG):", type=["png", "jpg"])
        
        if st.button("🚀 Activar Proyecto"):
            if nueva_emp:
                # Guardamos una fila inicial en Google Sheets para crear la empresa en la base de datos
                exito = guardar_fila_google({
                    "Empresa": nueva_emp, "Dimensión": "Alineación Estratégica", "Foco": "General", 
                    "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Brecha": 0,
                    "Facilita": "", "Dificulta": "", "No_Hacemos": "", "Accion_1": "", "Accion_2": ""
                })
                if exito:
                    if logo_subido:
                        img = Image.open(logo_subido)
                        img.save(os.path.join(LOGO_PATH, f"{nueva_emp}.png"))
                    st.success(f"¡{nueva_emp} registrado!")
                    st.rerun()
            else:
                st.error("Por favor escribe un nombre.")
        st.stop() # Detiene la ejecución aquí si no hay empresa seleccionada

# --- HEADER (SI HAY EMPRESA SELECCIONADA) ---
df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

col_h1, col_h2 = st.columns([1, 5])
with col_h1:
    if os.path.exists(logo_file): 
        st.image(logo_file, width=120)
    else:
        st.info("Sin Logo")
with col_h2:
    st.title(f"Intervención: {empresa_sel}")

# --- PESTAÑAS (REGISTRO, RADAR, REPORTE) ---
tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Radar Analítico", "📋 Reporte Ejecutivo"])

# (El resto del código de las pestañas se mantiene igual para conservar los filtros y la tabla corregida)
with tab1:
    f_ex = sorted(df_empresa['Foco'].unique().tolist())
    n_ex = sorted(df_empresa['Nombre'].unique().tolist())
    c_m1, c_m2 = st.columns(2)
    m_foco = c_m1.radio("📌 Área / Foco:", ["Existente", "Nuevo"], horizontal=True, key=f"f_{st.session_state.form_reset}")
    m_nom = c_m2.radio("👤 Participante:", ["Existente", "Nuevo"], horizontal=True, key=f"n_{st.session_state.form_reset}")
    with st.form(key=f"form_{st.session_state.form_reset}"):
        f1, f2 = st.columns(2)
        dim = f1.selectbox("Pilar:", ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"])
        foc = f2.selectbox("Foco Actual:", f_ex) if m_foco == "Existente" and f_ex else f2.text_input("Nuevo Foco:", value="General")
        fa, fb, fc = st.columns([2, 1, 1])
        nom = fa.selectbox("Nombre:", n_ex) if m_nom == "Existente" and n_ex else fa.text_input("Nuevo Participante:")
        act = fb.slider("Hoy", 1, 10, 5)
        obj = fc.slider("Meta", 1, 10, 8)
        a1 = st.text_input("Acción 1:"); a2 = st.text_input("Acción 2:")
        if st.form_submit_button("✅ Guardar"):
            if nom and foc:
                guardar_fila_google({"Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom, "Actual": act, "Objetivo": obj, "Brecha": obj-act, "Accion_1": a1, "Accion_2": a2})
                st.session_state.form_reset += 1
                st.rerun()

with tab2:
    if not df_empresa.empty:
        st.markdown("### 🔍 Filtros")
        c1, c2, c3 = st.columns(3)
        pilar_f = c1.multiselect("Pilares:", df_empresa['Dimensión'].unique(), default=df_empresa['Dimensión'].unique(), key="p_r")
        foco_f = c2.multiselect("Focos:", df_empresa['Foco'].unique(), default=df_empresa['Foco'].unique(), key="f_r")
        nom_f = c3.multiselect("Participantes:", df_empresa['Nombre'].unique(), default=df_empresa['Nombre'].unique(), key="n_r")
        df_filtrado = df_empresa[(df_empresa['Dimensión'].isin(pilar_f)) & (df_empresa['Foco'].isin(foco_f)) & (df_empresa['Nombre'].isin(nom_f))]
        
        if not df_filtrado.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Madurez", f"{df_filtrado['Actual'].mean():.1f}/10")
            m2.metric("Meta", f"{df_filtrado['Objetivo'].mean():.1f}/10")
            m3.metric("Gap", f"{df_filtrado['Objetivo'].mean() - df_filtrado['Actual'].mean():.1f}")
            res = []
            for d in ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]:
                sub = df_filtrado[df_filtrado['Dimensión'] == d]
                res.append({"Dimensión": d, "Actual": sub['Actual'].mean() if not sub.empty else 0, "Objetivo": sub['Objetivo'].mean() if not sub.empty else 0})
            df_p = pd.DataFrame(res); df_p["Brecha"] = df_p["Objetivo"] - df_p["Actual"]
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta'))
            fig_radar.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy'))
            st.plotly_chart(fig_radar, use_container_width=True)
            st.table(df_p.style.map(lambda x: 'background-color: #fecaca' if x > 2 else 'background-color: #bbf7d0', subset=['Brecha']).format({"Actual": "{:.1f}", "Objetivo": "{:.1f}", "Brecha": "{:.1f}"}))

with tab3:
    if not df_empresa.empty:
        col_t, col_b = st.columns([4, 1])
        col_t.subheader("Resumen de Compromisos")
        with col_b:
            w_bin = generar_word(empresa_sel, df_empresa, None, logo_file)
            st.download_button("📥 Descargar Word", data=w_bin, file_name=f"Reporte_{empresa_sel}.docx")
        st.dataframe(df_empresa[["Dimensión", "Nombre", "Actual", "Brecha", "Accion_1"]].sort_values(by="Brecha", ascending=False), use_container_width=True)