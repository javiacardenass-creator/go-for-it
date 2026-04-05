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

# --- ESTILO ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a; color: white; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE DATOS ---
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
        
        # Unificar nombres de columnas para Capacidades Distintivas
        if "Distintos" in df.columns and "Capacidades_Distintivas" not in df.columns:
            df = df.rename(columns={"Distintos": "Capacidades_Distintivas"})
        
        cols_necesarias = ["Capacidades_Distintivas", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"]
        for c in cols_necesarias:
            if c not in df.columns: df[c] = ""
        return df
    except:
        return pd.DataFrame()

def enviar_datos(payload):
    try:
        res = requests.post(SCRIPT_URL, json=payload, timeout=10)
        return res.status_code == 200
    except: return False

def generar_word(empresa, df_f, logo_p):
    doc = Document()
    doc.add_heading(f'Informe Estratégico: {empresa}', 0)
    if os.path.exists(logo_p): doc.add_picture(logo_p, width=Inches(1.5))
    doc.add_heading('Detalle de Hallazgos', level=1)
    for _, r in df_f.iterrows():
        doc.add_heading(f"{r['Dimensión']} ({r['Nombre']})", level=2)
        doc.add_paragraph(f"Puntaje: {r['Actual']}/{r['Objetivo']} | Brecha: {r['Brecha']}")
        cap = r['Capacidades_Distintivas'] if 'Capacidades_Distintivas' in r else ""
        doc.add_paragraph(f"Capacidades Distintivas: {cap}")
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- CARGA INICIAL ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

# --- SIDEBAR: GESTIÓN DE PROYECTOS ---
with st.sidebar:
    st.title("Consultoría Pro")
    emp_sel = st.selectbox("🎯 Proyecto / Cliente:", ["-- Nuevo Proyecto --"] + empresas_list)
    
    if emp_sel == "-- Nuevo Proyecto --":
        st.subheader("✨ Registrar Cliente")
        n_emp = st.text_input("Nombre de la Empresa:")
        u_logo = st.file_uploader("Logo:", type=["png", "jpg"])
        if st.button("🚀 Activar Proyecto"):
            if n_emp:
                if enviar_datos({"Empresa": n_emp, "Dimensión": "Alineación Estratégica", "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Foco": "General"}):
                    if u_logo: 
                        img = Image.open(u_logo)
                        img.save(os.path.join(LOGO_PATH, f"{n_emp}.png"))
                    st.success(f"¡Proyecto {n_emp} creado!")
                    st.rerun()
        st.stop()

# --- SCOPE DE DATOS POR EMPRESA ---
df_emp = df_global[df_global['Empresa'] == emp_sel]
logo_file = os.path.join(LOGO_PATH, f"{emp_sel}.png")

# --- RENDERIZADO DE INTERFAZ ---
c_h1, c_h2 = st.columns([1, 5])
with c_h1: 
    if os.path.exists(logo_file): st.image(logo_file, width=100)
with c_h2: st.title(f"Intervención: {emp_sel}")

t1, t2, t3 = st.tabs(["📝 Registro y Edición", "📊 Radar Analítico", "📋 Reporte Ejecutivo"])

# --- TAB 1: REGISTRO Y EDICIÓN ---
with t1:
    st.info("Selecciona los criterios para cargar datos previos o crear uno nuevo.")
    c1, c2, c3 = st.columns(3)
    dim_f = c1.selectbox("Pilar Estratégico:", ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"])
    
    m_foc = c2.toggle("Nuevo Foco")
    foc_f = c2.text_input("Nombre Foco:") if m_foc else c2.selectbox("Foco:", sorted(df_emp['Foco'].unique()) if not df_emp.empty else ["General"])
    
    m_nom = c3.toggle("Nuevo Participante")
    nom_f = c3.text_input("Nombre Participante:") if m_nom else c3.selectbox("Participante:", sorted(df_emp['Nombre'].unique()) if not df_emp.empty else ["Admin"])

    # Búsqueda de coincidencia para autocarga
    match = df_emp[(df_emp['Dimensión'] == dim_f) & (df_emp['Foco'] == foc_f) & (df_emp['Nombre'] == nom_f)]
    row = match.iloc[0] if not match.empty else None

    with st.form("form_smart"):
        st.subheader("✏️ Editando Evaluación" if row is not None else "➕ Nuevo Registro")
        f_a, f_b = st.columns(2)
        v_act = f_a.slider("Nivel Hoy", 1, 10, int(row['Actual']) if row is not None else 5)
        v_obj = f_b.slider("Nivel Meta", 1, 10, int(row['Objetivo']) if row is not None else 8)
        
        st.markdown("---")
        tx1, tx2 = st.columns(2)
        
        # Función interna para leer valores de forma segura
        def get_v(r, col): return str(r[col]) if r is not None and col in r and pd.notna(r[col]) else ""

        f_fac = tx1.text_area("¿Qué facilita?", value=get_v(row, 'Facilita'))
        f_dif = tx1.text_area("¿Qué dificulta?", value=get_v(row, 'Dificulta'))
        f_no = tx2.text_area("¿Qué NO estamos haciendo?", value=get_v(row, 'No_Hacemos'))
        
        # CASILLA CRÍTICA: Capacidades Distintivas
        f_cap = tx2.text_area("Capacidades Distintivas:", value=get_v(row, 'Capacidades_Distintivas'))
        
        a1 = st.text_input("Acción 1:", value=get_v(row, 'Accion_1'))
        a2 = st.text_input("Acción 2:", value=get_v(row, 'Accion_2'))

        if st.form_submit_button("💾 Guardar Cambios"):
            payload = {
                "Empresa": emp_sel, "Dimensión": dim_f, "Foco": foc_f, "Nombre": nom_f,
                "Actual": v_act, "Objetivo": v_obj, "Brecha": v_obj-v_act,
                "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no,
                "Capacidades_Distintivas": f_cap, "Accion_1": a1, "Accion_2": a2
            }
            if enviar_datos(payload):
                st.success("¡Sincronizado!")
                st.cache_data.clear()
                st.rerun()

# --- LÓGICA FILTROS ---
def interfaz_filtros(df, key_id):
    st.markdown("### 🔍 Filtros de Análisis")
    cf1, cf2, cf3 = st.columns(3)
    p_fil = cf1.multiselect("Pilares:", df['Dimensión'].unique(), default=df['Dimensión'].unique(), key=f"p_{key_id}")
    f_fil = cf2.multiselect("Focos:", df['Foco'].unique(), default=df['Foco'].unique(), key=f"f_{key_id}")
    n_fil = cf3.multiselect("Participantes:", df['Nombre'].unique(), default=df['Nombre'].unique(), key=f"n_{key_id}")
    return df[(df['Dimensión'].isin(p_fil)) & (df['Foco'].isin(f_fil)) & (df['Nombre'].isin(n_fil))]

# --- TAB 2: RADAR ---
with t2:
    if not df_emp.empty:
        df_f_rad = interfaz_filtros(df_emp, "radar")
        if not df_f_rad.empty:
            res = []
            for d in ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]:
                sub = df_f_rad[df_f_rad['Dimensión'] == d]
                res.append({"Dimensión": d, "Actual": sub['Actual'].mean() if not sub.empty else 0, "Objetivo": sub['Objetivo'].mean() if not sub.empty else 0})
            df_p = pd.DataFrame(res); df_p["Brecha"] = df_p["Objetivo"] - df_p["Actual"]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta'))
            fig.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy'))
            st.plotly_chart(fig, use_container_width=True)
            st.table(df_p.style.map(lambda x: 'background-color: #fecaca' if x > 2 else 'background-color: #bbf7d0', subset=['Brecha']).format({"Actual": "{:.1f}", "Objetivo": "{:.1f}", "Brecha": "{:.1f}"}))

# --- TAB 3: REPORTE ---
with t3:
    if not df_emp.empty:
        df_f_rep = interfaz_filtros(df_emp, "reporte")
        c_t, c_b = st.columns([4, 1])
        c_t.subheader("Resumen Ejecutivo")
        with c_b:
            w_bin = generar_word(emp_sel, df_f_rep, logo_file)
            st.download_button("📥 Descargar Word", data=w_bin, file_name=f"Reporte_{emp_sel}.docx")
        st.dataframe(df_f_rep[["Dimensión", "Foco", "Nombre", "Actual", "Brecha", "Capacidades_Distintivas", "Accion_1"]].sort_values(by="Brecha", ascending=False), use_container_width=True)