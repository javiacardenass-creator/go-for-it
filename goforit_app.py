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
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Go For It | Strategic Advisor", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a; color: white; }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #2563eb; color: white; }
    .stTable { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"
if not os.path.exists(LOGO_PATH): os.makedirs(LOGO_PATH, exist_ok=True)

# --- FUNCIONES ---
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
    section = doc.sections[0]
    p_header = section.header.paragraphs[0]
    if os.path.exists(logo_p):
        p_header.add_run().add_picture(logo_p, width=Inches(1.2))
    
    doc.add_heading('Informe de Intervención Estratégica', 0).alignment = 1
    doc.add_paragraph(f"Cliente: {empresa}").alignment = 1
    
    doc.add_heading('1. Radar de Madurez', level=1)
    img_bytes = fig_radar.to_image(format="png", engine="kaleido")
    doc.add_picture(BytesIO(img_bytes), width=Inches(5.2))
    
    doc.add_heading('2. Calificaciones y Brechas', level=1)
    t_q = doc.add_table(rows=1, cols=4); t_q.style = 'Light Grid Accent 1'
    for i, txt in enumerate(['Pilar', 'Actual', 'Meta', 'GAP']): t_q.rows[0].cells[i].text = txt
    for d in df_f['Dimensión'].unique():
        sub = df_f[df_f['Dimensión'] == d]
        r = t_q.add_row().cells
        act, obj = sub['Actual'].mean(), sub['Objetivo'].mean()
        r[0].text, r[1].text, r[2].text, r[3].text = d, f"{act:.1f}", f"{obj:.1f}", f"{(obj-act):.1f}"

    doc.add_heading('3. Matriz de Diagnóstico', level=1)
    matriz = doc.add_table(rows=1, cols=4); matriz.style = 'Table Grid'
    hdr = matriz.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = 'Pilar', 'Facilita', 'Dificulta', 'No hacemos'
    for d in df_f['Dimensión'].unique():
        sub = df_f[df_f['Dimensión'] == d]
        r = matriz.add_row().cells
        r[0].text = d
        r[1].text = "\n".join(set([str(x) for x in sub['Facilita'] if str(x).strip() and str(x).lower() != "nan"]))
        r[2].text = "\n".join(set([str(x) for x in sub['Dificulta'] if str(x).strip() and str(x).lower() != "nan"]))
        r[3].text = "\n".join(set([str(x) for x in sub['No_Hacemos'] if str(x).strip() and str(x).lower() != "nan"]))

    target = BytesIO(); doc.save(target)
    return target.getvalue()

# --- CARGA ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

# --- SIDEBAR ---
with st.sidebar:
    st.title("Consultoría Pro")
    emp_sel = st.selectbox("🎯 Proyecto:", ["-- Nuevo Proyecto --"] + empresas_list)
    
    if emp_sel == "-- Nuevo Proyecto --":
        st.subheader("✨ Registrar Cliente")
        n_emp = st.text_input("Nombre Empresa:")
        u_logo = st.file_uploader("Logo:", type=["png", "jpg"])
        if st.button("🚀 Activar"):
            if n_emp:
                if enviar_datos({"Empresa": n_emp, "Dimensión": "Alineación", "Foco": "General", "Nombre": "Admin", "Actual": 1, "Objetivo": 1}):
                    if u_logo: Image.open(u_logo).save(os.path.join(LOGO_PATH, f"{n_emp}.png"))
                    st.cache_data.clear(); st.rerun()
        st.stop()
    else:
        st.subheader("🖼️ Gestión de Imagen")
        u_logo_ex = st.file_uploader("Actualizar Logo:", type=["png", "jpg"], key="up_logo")
        if u_logo_ex and st.button("💾 Guardar Logo"):
            Image.open(u_logo_ex).save(os.path.join(LOGO_PATH, f"{emp_sel}.png"))
            st.success("Logo actualizado."); st.rerun()

# --- INTERFAZ ---
df_emp = df_global[df_global['Empresa'] == emp_sel]
logo_file = os.path.join(LOGO_PATH, f"{emp_sel}.png")

t1, t2, t3 = st.tabs(["📝 Registro", "📊 Radar Analítico", "📋 Reporte"])

# --- TAB 1 (REGISTRO) ---
with t1:
    st.subheader("Ingreso de Hallazgos")
    c1, c2, c3 = st.columns(3)
    pilares_m = ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]
    dim_f = c1.selectbox("Pilar:", pilares_m)
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
        f_fac, f_dif = tx1.text_area("¿Qué facilita?", value=gv(row, 'Facilita')), tx1.text_area("¿Qué dificulta?", value=gv(row, 'Dificulta'))
        f_no, f_cap = tx2.text_area("¿Qué NO hacemos?", value=gv(row, 'No_Hacemos')), tx2.text_area("Capacidades:", value=gv(row, 'Capacidades_Distintivas'))
        a1, a2 = st.text_input("Acción 1:", value=gv(row, 'Accion_1')), st.text_input("Acción 2:", value=gv(row, 'Accion_2'))
        if st.form_submit_button("💾 Guardar"):
            if enviar_datos({"Empresa": emp_sel, "Dimensión": dim_f, "Foco": foc_f, "Nombre": nom_f, "Actual": v_act, "Objetivo": v_obj, "Brecha": v_obj-v_act, "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no, "Capacidades_Distintivas": f_cap, "Accion_1": a1, "Accion_2": a2}):
                st.cache_data.clear(); st.rerun()

# --- TAB 2 (RADAR + TABLA DE BRECHAS) ---
with t2:
    if not df_emp.empty:
        col_f1, col_f2 = st.columns(2)
        p_filt = col_f1.multiselect("Filtrar Pilares:", pilares_m, default=pilares_m)
        n_filt = col_f2.multiselect("Filtrar Participantes:", df_emp['Nombre'].unique(), default=df_emp['Nombre'].unique())
        
        df_f_rad = df_emp[(df_emp['Dimensión'].isin(p_filt)) & (df_emp['Nombre'].isin(n_filt))]
        
        res = []
        for d in p_filt:
            sub = df_f_rad[df_f_rad['Dimensión'] == d]
            res.append({"Dimensión": d, "Actual": sub['Actual'].mean() if not sub.empty else 0, "Objetivo": sub['Objetivo'].mean() if not sub.empty else 0})
        df_p = pd.DataFrame(res)
        
        if not df_p.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta', line_color='#1e293b'))
            fig.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy', line_color='#2563eb'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            st.session_state.fig_actual = fig
            
            # --- AQUÍ ESTÁ LA TABLA QUE FALTABA ---
            st.subheader("Análisis de Brechas (GAP)")
            df_p['GAP'] = df_p['Objetivo'] - df_p['Actual']
            # Formateo para mostrar 1 decimal
            df_mostrar = df_p.copy()
            df_mostrar['Actual'] = df_mostrar['Actual'].map('{:.1f}'.format)
            df_mostrar['Objetivo'] = df_mostrar['Objetivo'].map('{:.1f}'.format)
            df_mostrar['GAP'] = df_mostrar['GAP'].map('{:.1f}'.format)
            st.table(df_mostrar)
        else: st.warning("Selecciona al menos un pilar.")

# --- TAB 3 (REPORTE) ---
with t3:
    if not df_emp.empty:
        if 'fig_actual' in st.session_state:
            w_bin = generar_word_pro(emp_sel, df_emp, st.session_state.fig_actual, logo_file)
            st.download_button("📥 Descargar Reporte Completo", data=w_bin, file_name=f"Informe_{emp_sel}.docx")
        st.dataframe(df_emp)