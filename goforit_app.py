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
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"

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
    
    doc.add_heading('2. Detalle de Hallazgos y Acciones', level=1)
    for _, row in df_filtrado.iterrows():
        p = doc.add_paragraph()
        p.add_run(f"{row['Dimensión']} - {row['Foco']} ({row['Nombre']})").bold = True
        doc.add_paragraph(f"Puntaje: {row['Actual']}/{row['Objetivo']} | Brecha: {row['Brecha']}")
        doc.add_paragraph(f"Acciones: 1. {row['Accion_1']} | 2. {row['Accion_2']}")
    
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- DATOS Y NAVEGACIÓN ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

with st.sidebar:
    st.title("Consultoría Pro")
    empresa_sel = st.selectbox("🎯 Proyecto Actual:", ["-- Seleccione --"] + empresas_list)
    if empresa_sel == "-- Seleccione --": st.stop()

df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Radar Analítico", "📋 Reporte Ejecutivo"])

# --- TAB 1: REGISTRO (SIN CAMBIOS) ---
with tab1:
    f_ex = sorted(df_empresa['Foco'].unique().tolist())
    n_ex = sorted(df_empresa['Nombre'].unique().tolist())
    col_m1, col_m2 = st.columns(2)
    m_foco = col_m1.radio("📌 Área / Foco:", ["Existente", "Nuevo"], horizontal=True, key=f"f_{st.session_state.form_reset}")
    m_nom = col_m2.radio("👤 Participante:", ["Existente", "Nuevo"], horizontal=True, key=f"n_{st.session_state.form_reset}")
    
    with st.form(key=f"form_{st.session_state.form_reset}"):
        f1, f2 = st.columns(2)
        dim = f1.selectbox("Pilar:", ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"])
        foc = f2.selectbox("Foco Actual:", f_ex) if m_foco == "Existente" and f_ex else f2.text_input("Nuevo Foco:", value="General")
        fa, fb, fc = st.columns([2, 1, 1])
        nom = fa.selectbox("Nombre:", n_ex) if m_nom == "Existente" and n_ex else fa.text_input("Nuevo Participante:")
        act = fb.slider("Hoy", 1, 10, 5)
        obj = fc.slider("Meta", 1, 10, 8)
        a1 = st.text_input("Acción 1:")
        a2 = st.text_input("Acción 2:")
        if st.form_submit_button("✅ Guardar"):
            guardar_fila_google({"Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom, "Actual": act, "Objetivo": obj, "Brecha": obj-act, "Accion_1": a1, "Accion_2": a2})
            st.session_state.form_reset += 1
            st.rerun()

# --- LÓGICA DE FILTROS PARA TAB 2 Y 3 ---
def mostrar_filtros(df):
    st.markdown("### 🔍 Filtros de Visualización")
    c1, c2, c3 = st.columns(3)
    pilar_f = c1.multiselect("Pilar Estratégico:", df['Dimensión'].unique(), default=df['Dimensión'].unique())
    foco_f = c2.multiselect("Área / Foco:", df['Foco'].unique(), default=df['Foco'].unique())
    nom_f = c3.multiselect("Participante:", df['Nombre'].unique(), default=df['Nombre'].unique())
    
    mask = (df['Dimensión'].isin(pilar_f)) & (df['Foco'].isin(foco_f)) & (df['Nombre'].isin(nom_f))
    return df[mask]

# --- TAB 2: RADAR CON FILTROS ---
with tab2:
    if not df_empresa.empty:
        df_filtrado = mostrar_filtros(df_empresa)
        
        if not df_filtrado.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Madurez (Filtro)", f"{df_filtrado['Actual'].mean():.1f}/10")
            m2.metric("Meta (Filtro)", f"{df_filtrado['Objetivo'].mean():.1f}/10")
            m3.metric("Gap", f"{df_filtrado['Objetivo'].mean() - df_filtrado['Actual'].mean():.1f}")

            # Agrupar para el radar
            res = []
            for d in ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]:
                sub = df_filtrado[df_filtrado['Dimensión'] == d]
                res.append({"Dimensión": d, "Actual": sub['Actual'].mean() if not sub.empty else 0, "Objetivo": sub['Objetivo'].mean() if not sub.empty else 0})
            df_p = pd.DataFrame(res)

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta'))
            fig_radar.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy'))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=450)
            st.plotly_chart(fig_radar, use_container_width=True)

            st.table(df_p.style.map(lambda x: 'background-color: #fecaca' if x > 2 else 'background-color: #bbf7d0', subset=['Actual']).format("{:.1f}"))
        else:
            st.warning("No hay datos para la combinación de filtros seleccionada.")

# --- TAB 3: REPORTE CON FILTROS ---
with tab3:
    if not df_empresa.empty:
        # Aquí también aplicamos los mismos filtros para que el reporte sea coherente
        df_rep = mostrar_filtros(df_empresa)
        
        col_t, col_b = st.columns([4, 1])
        col_t.subheader("Resumen Filtrado de Compromisos")
        with col_b:
            # El Word ahora se genera solo con lo que está filtrado
            w_bin = generar_word(empresa_sel, df_rep, None, logo_file)
            st.download_button("📥 Word Filtrado", data=w_bin, file_name=f"Reporte_{empresa_sel}.docx")
        
        st.dataframe(df_rep[["Dimensión", "Foco", "Nombre", "Actual", "Brecha", "Accion_1"]].sort_values(by="Brecha", ascending=False), use_container_width=True)