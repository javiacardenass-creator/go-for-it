import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import os
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Go For It | Strategic Advisor", page_icon="🚀", layout="wide")

# --- CONFIGURACIÓN DE CONEXIÓN ---
SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"
if not os.path.exists(LOGO_PATH): os.makedirs(LOGO_PATH, exist_ok=True)

# --- FUNCIONES CORE ---
@st.cache_data(ttl=5)
def leer_datos():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url).dropna(subset=['Empresa'])
        if "Distintos" in df.columns and "Capacidades_Distintivas" not in df.columns:
            df = df.rename(columns={"Distintos": "Capacidades_Distintivas"})
        cols_check = ["Capacidades_Distintivas", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"]
        for c in cols_check:
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame()

def enviar_datos(payload):
    try:
        res = requests.post(SCRIPT_URL, json=payload, timeout=15)
        return res.status_code == 200
    except: return False

# --- NUEVA FUNCIÓN DE REPORTE MEJORADO ---
def generar_word_pro(empresa, df_f, fig_radar, logo_p):
    doc = Document()
    
    # 1. Encabezado con Logo y Título
    section = doc.sections[0]
    header = section.header
    p_header = header.paragraphs[0]
    if os.path.exists(logo_p):
        run_logo = p_header.add_run()
        run_logo.add_picture(logo_p, width=Inches(1.2))
    
    title = doc.add_heading(f'Informe de Intervención Estratégica', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Cliente: {empresa}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Consultor: Go For It - Strategic Advisor").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 2. Radar Estratégico
    doc.add_heading('1. Radar de Madurez Estratégica', level=1)
    doc.add_paragraph("La siguiente gráfica muestra la brecha entre la situación actual y los objetivos definidos por dimensión:")
    
    # Convertir Plotly a Imagen para el Word
    img_bytes = fig_radar.to_image(format="png", engine="kaleido")
    doc.add_picture(BytesIO(img_bytes), width=Inches(5.5))
    
    # 3. Tabla de Calificaciones y Brechas
    doc.add_heading('2. Tabla de Calificaciones y Brechas', level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Light Grid Accent 1'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Dimensión'
    hdr_cells[1].text = 'Actual'
    hdr_cells[2].text = 'Objetivo'
    hdr_cells[3].text = 'Brecha (GAP)'

    # Resumen por dimensión para la tabla
    for d in df_f['Dimensión'].unique():
        sub = df_f[df_f['Dimensión'] == d]
        row_cells = table.add_row().cells
        row_cells[0].text = str(d)
        row_cells[1].text = f"{sub['Actual'].mean():.1f}"
        row_cells[2].text = f"{sub['Objetivo'].mean():.1f}"
        row_cells[3].text = f"{(sub['Objetivo'].mean() - sub['Actual'].mean()):.1f}"

    # 4. Mención Especial: Capacidades Distintivas
    doc.add_heading('3. Capacidades Distintivas Identificadas', level=1)
    doc.add_paragraph("Se han identificado las siguientes ventajas competitivas y recursos críticos:")
    for cap in df_f['Capacidades_Distintivas'].unique():
        if str(cap).strip():
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(str(cap)).bold = True

    # 5. Hallazgos Cualitativos (Comentarios por Pilar)
    doc.add_heading('4. Diagnóstico Detallado por Pilar', level=1)
    for d in df_f['Dimensión'].unique():
        doc.add_heading(d, level=2)
        sub = df_f[df_f['Dimensión'] == d]
        for _, r in sub.iterrows():
            p = doc.add_paragraph()
            p.add_run(f"Participante: {r['Nombre']} ({r['Foco']})").bold = True
            doc.add_paragraph(f"• Facilita: {r['Facilita']}")
            doc.add_paragraph(f"• Dificulta: {r['Dificulta']}")
            doc.add_paragraph(f"• Acciones Propuestas: {r['Accion_1']}, {r['Accion_2']}")

    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- CARGA DE DATOS ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

# --- SIDEBAR ---
with st.sidebar:
    st.title("Consultoría Pro")
    emp_sel = st.selectbox("🎯 Proyecto:", ["-- Nuevo Proyecto --"] + empresas_list)
    if emp_sel == "-- Nuevo Proyecto --":
        # ... (Código de registro de proyecto igual que antes) ...
        st.stop()

df_emp = df_global[df_global['Empresa'] == emp_sel]
logo_file = os.path.join(LOGO_PATH, f"{emp_sel}.png")

tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Radar Analítico", "📋 Reporte Ejecutivo"])

# --- TAB 1 (REGISTRO) Se mantiene igual ---
with tab1:
    # ... código del formulario ...
    pass

# --- FUNCIÓN DE FILTROS ---
def interfaz_filtros(df, k):
    cf1, cf2, cf3 = st.columns(3)
    p = cf1.multiselect("Pilares:", df['Dimensión'].unique(), default=df['Dimensión'].unique(), key=f"p_{k}")
    f = cf2.multiselect("Focos:", df['Foco'].unique(), default=df['Foco'].unique(), key=f"f_{k}")
    n = cf3.multiselect("Participantes:", df['Nombre'].unique(), default=df['Nombre'].unique(), key=f"n_{k}")
    return df[(df['Dimensión'].isin(p)) & (df['Foco'].isin(f)) & (df['Nombre'].isin(n))]

# --- TAB 2: RADAR (PREPARANDO FIGURA PARA EL WORD) ---
with tab2:
    if not df_emp.empty:
        df_f_rad = interfaz_filtros(df_emp, "radar")
        if not df_f_rad.empty:
            # Lógica de cálculo del Radar
            res = []
            for d in ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]:
                sub = df_f_rad[df_f_rad['Dimensión'] == d]
                res.append({"Dimensión": d, "Actual": sub['Actual'].mean() if not sub.empty else 0, "Objetivo": sub['Objetivo'].mean() if not sub.empty else 0})
            df_p = pd.DataFrame(res)
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta'))
            fig.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])))
            st.plotly_chart(fig, use_container_width=True)
            
            # Guardamos la figura en session_state para usarla en el Tab 3
            st.session_state.fig_actual = fig

# --- TAB 3: REPORTE MEJORADO ---
with tab3:
    if not df_emp.empty:
        df_f_rep = interfaz_filtros(df_emp, "reporte")
        st.subheader("Visualización de Resultados")
        
        col_t, col_b = st.columns([4, 1])
        with col_b:
            if 'fig_actual' in st.session_state:
                w_bin = generar_word_pro(emp_sel, df_f_rep, st.session_state.fig_actual, logo_file)
                st.download_button("📥 Descargar Informe Pro", data=w_bin, file_name=f"Reporte_Estrategico_{emp_sel}.docx")
            else:
                st.warning("Ve a la pestaña Radar primero para cargar la gráfica.")
        
        st.dataframe(df_f_rep.sort_values(by="Brecha", ascending=False))