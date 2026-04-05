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

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Go For It | Strategic Advisor", page_icon="🚀", layout="wide")

# Estilo para que se vea profesional en el iPad
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a; color: white; }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #2563eb; color: white; }
    </style>
    """, unsafe_allow_html=True)

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
        for c in ["Capacidades_Distintivas", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"]:
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame()

def enviar_datos(payload):
    try:
        res = requests.post(SCRIPT_URL, json=payload, timeout=15)
        return res.status_code == 200
    except: return False

def generar_word_pro(empresa, df_f, fig_radar, logo_p):
    doc = Document()
    # Encabezado
    section = doc.sections[0]
    p_header = section.header.paragraphs[0]
    if os.path.exists(logo_p):
        p_header.add_run().add_picture(logo_p, width=Inches(1.2))
    
    doc.add_heading('Informe de Intervención Estratégica', 0).alignment = 1
    doc.add_paragraph(f"Cliente: {empresa}").alignment = 1
    
    # 1. Radar
    doc.add_heading('1. Radar Estratégico', level=1)
    img_bytes = fig_radar.to_image(format="png", engine="kaleido")
    doc.add_picture(BytesIO(img_bytes), width=Inches(5.5))
    
    # 2. Tabla de Brechas
    doc.add_heading('2. Calificaciones y Brechas', level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Light Grid Accent 1'
    for i, text in enumerate(['Pilar', 'Actual', 'Meta', 'GAP']):
        table.rows[0].cells[i].text = text
    for d in df_f['Dimensión'].unique():
        sub = df_f[df_f['Dimensión'] == d]
        row = table.add_row().cells
        row[0].text = d
        row[1].text = f"{sub['Actual'].mean():.1f}"
        row[2].text = f"{sub['Objetivo'].mean():.1f}"
        row[3].text = f"{(sub['Objetivo'].mean()-sub['Actual'].mean()):.1f}"

    # 3. Capacidades
    doc.add_heading('3. Capacidades Distintivas', level=1)
    for cap in df_f['Capacidades_Distintivas'].unique():
        if str(cap).strip(): doc.add_paragraph(str(cap), style='List Bullet')

    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- CARGA INICIAL ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

# --- SIDEBAR: CREACIÓN DE CLIENTES ---
with st.sidebar:
    st.title("Consultoría Pro")
    emp_sel = st.selectbox("🎯 Proyecto:", ["-- Nuevo Proyecto --"] + empresas_list)
    
    if emp_sel == "-- Nuevo Proyecto --":
        st.subheader("✨ Registrar Cliente")
        n_emp = st.text_input("Nombre Empresa:")
        u_logo = st.file_uploader("Logo:", type=["png", "jpg"])
        if st.button("🚀 Activar Proyecto"):
            if n_emp:
                if enviar_datos({"Empresa": n_emp, "Dimensión": "Alineación", "Foco": "General", "Nombre": "Admin", "Actual": 1, "Objetivo": 1}):
                    if u_logo: Image.open(u_logo).save(os.path.join(LOGO_PATH, f"{n_emp}.png"))
                    st.cache_data.clear()
                    st.rerun()
        st.stop()

# --- INTERFAZ PRINCIPAL ---
df_emp = df_global[df_global['Empresa'] == emp_sel]
logo_file = os.path.join(LOGO_PATH, f"{emp_sel}.png")

t1, t2, t3 = st.tabs(["📝 Registro", "📊 Radar", "📋 Reporte"])

# --- TAB 1: FORMULARIO DE INGRESO ---
with t1:
    st.subheader("Ingreso de Hallazgos")
    c1, c2, c3 = st.columns(3)
    dim_f = c1.selectbox("Pilar:", ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"])
    m_foc = c2.toggle("Nuevo Foco")
    foc_f = c2.text_input("Foco:") if m_foc else c2.selectbox("Foco:", sorted(df_emp['Foco'].unique()) if not df_emp.empty else ["General"])
    m_nom = c3.toggle("Nuevo Participante")
    nom_f = c3.text_input("Nombre:") if m_nom else c3.selectbox("Participante:", sorted(df_emp['Nombre'].unique()) if not df_emp.empty else ["Admin"])

    match = df_emp[(df_emp['Dimensión'] == dim_f) & (df_emp['Foco'] == foc_f) & (df_emp['Nombre'] == nom_f)]
    row = match.iloc[0] if not match.empty else None

    with st.form("form_registro"):
        f_a, f_b = st.columns(2)
        v_act = f_a.slider("Hoy", 1, 10, int(row['Actual']) if row is not None else 5)
        v_obj = f_b.slider("Meta", 1, 10, int(row['Objetivo']) if row is not None else 8)
        
        tx1, tx2 = st.columns(2)
        def gv(r, c): return str(r[c]) if r is not None and c in r and pd.notna(r[c]) else ""
        
        f_fac = tx1.text_area("Facilita:", value=gv(row, 'Facilita'))
        f_dif = tx1.text_area("Dificulta:", value=gv(row, 'Dificulta'))
        f_no = tx2.text_area("No hacemos:", value=gv(row, 'No_Hacemos'))
        f_cap = tx2.text_area("Capacidades Distintivas:", value=gv(row, 'Capacidades_Distintivas'))
        
        a1 = st.text_input("Acción 1:", value=gv(row, 'Accion_1'))
        a2 = st.text_input("Acción 2:", value=gv(row, 'Accion_2'))

        if st.form_submit_button("💾 Guardar"):
            if enviar_datos({"Empresa": emp_sel, "Dimensión": dim_f, "Foco": foc_f, "Nombre": nom_f, "Actual": v_act, "Objetivo": v_obj, "Brecha": v_obj-v_act, "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no, "Capacidades_Distintivas": f_cap, "Accion_1": a1, "Accion_2": a2}):
                st.cache_data.clear(); st.rerun()

# --- TAB 2: RADAR ---
with t2:
    if not df_emp.empty:
        # Filtros simplificados para el Radar
        pilares_sel = st.multiselect("Filtrar Pilares:", df_emp['Dimensión'].unique(), default=df_emp['Dimensión'].unique())
        df_f_rad = df_emp[df_emp['Dimensión'].isin(pilares_sel)]
        
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
        st.session_state.fig_actual = fig

# --- TAB 3: REPORTE ---
with t3:
    if not df_emp.empty:
        st.subheader("Generar Informe Word")
        if 'fig_actual' in st.session_state:
            w_bin = generar_word_pro(emp_sel, df_emp, st.session_state.fig_actual, logo_file)
            st.download_button("📥 Descargar Reporte Completo", data=w_bin, file_name=f"Informe_{emp_sel}.docx")
        else:
            st.warning("⚠️ Primero visualiza el Radar en la pestaña anterior.")
        st.dataframe(df_emp)