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
st.set_page_config(
    page_title="Go For It | Strategic Advisor",
    page_icon="🚀",
    layout="wide"
)

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    [data-testid="stSidebar"] { background-color: #0f172a; color: white; }
    h1 { color: #1e293b; font-weight: 800; }
    div.stButton > button {
        width: 100%; background-color: #2563eb; color: white; border-radius: 8px; height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"

if 'form_reset' not in st.session_state:
    st.session_state.form_reset = 0

# --- FUNCIONES ---
@st.cache_data(ttl=60)
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

def generar_word(empresa, df, fig, logo_p):
    doc = Document()
    doc.add_heading(f'Informe Estratégico: {empresa}', 0)
    if os.path.exists(logo_p):
        try: doc.add_picture(logo_p, width=Inches(1.5))
        except: pass
    doc.add_heading('1. Análisis de Madurez', level=1)
    if fig:
        img_bytes = fig.to_image(format="png", engine="kaleido")
        doc.add_picture(BytesIO(img_bytes), width=Inches(5.5))
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- SIDEBAR ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

with st.sidebar:
    st.title("Consultoría Pro")
    empresa_sel = st.selectbox("🎯 Proyecto Actual:", ["-- Nuevo Proyecto --"] + empresas_list)
    if empresa_sel == "-- Nuevo Proyecto --":
        nueva = st.text_input("Nombre de Empresa:")
        if st.button("Activar"):
            if nueva:
                guardar_fila_google({"Empresa": nueva, "Dimensión": "Alineación Estratégica", "Foco": "General", "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Brecha": 0})
                st.rerun()
        st.stop()

# --- HEADER ---
df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")
col_h1, col_h2 = st.columns([1, 5])
with col_h1:
    if os.path.exists(logo_file): st.image(logo_file, width=120)
with col_h2:
    st.title(f"Intervención: {empresa_sel}")

tab1, tab2, tab3 = st.tabs(["📝 Evaluación", "📊 Radar", "📋 Resumen"])

# --- TAB 1: EVALUACIÓN ---
with tab1:
    f_ex = sorted(df_empresa['Foco'].unique().tolist()) if not df_empresa.empty else []
    n_ex = sorted(df_empresa['Nombre'].unique().tolist()) if not df_empresa.empty else []
    
    col_m1, col_m2 = st.columns(2)
    m_foco = col_m1.radio("📌 Área / Foco:", ["Existente", "Nuevo"], horizontal=True, key=f"f_{st.session_state.form_reset}")
    m_nom = col_m2.radio("👤 Participante:", ["Existente", "Nuevo"], horizontal=True, key=f"n_{st.session_state.form_reset}")

    with st.form(key=f"form_{st.session_state.form_reset}"):
        f1, f2 = st.columns(2)
        dim = f1.selectbox("Pilar Estratégico:", ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"])
        foc = f2.selectbox("Foco Actual:", f_ex) if m_foco == "Existente" and f_ex else f2.text_input("Nuevo Foco:", value="General")
        
        fa, fb, fc = st.columns([2, 1, 1])
        nom = fa.selectbox("Nombre:", n_ex) if m_nom == "Existente" and n_ex else fa.text_input("Nuevo Participante:")
        act = fb.select_slider("Hoy", options=range(1, 11), value=5)
        obj = fc.select_slider("Meta", options=range(1, 11), value=8)
        
        t1, t2 = st.columns(2)
        f_fac = t1.text_area("Facilitadores", height=80)
        f_dif = t1.text_area("Limitantes", height=80)
        f_no = t2.text_area("Brechas (Lo que no hacemos)", height=175)
        a1 = st.text_input("Acción Prioritaria 1:")
        a2 = st.text_input("Acción Prioritaria 2:")
        
        if st.form_submit_button("✅ Guardar"):
            if nom and foc:
                res = guardar_fila_google({"Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom, "Actual": act, "Objetivo": obj, "Brecha": obj-act, "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no, "Accion_1": a1, "Accion_2": a2})
                if res:
                    st.session_state.form_reset += 1
                    st.rerun()

# --- TAB 2: ANALÍTICA (CORREGIDA) ---
fig_radar = None
with tab2:
    if not df_empresa.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Madurez Promedio", f"{df_empresa['Actual'].mean():.1f}/10")
        m2.metric("Meta Aspiracional", f"{df_empresa['Objetivo'].mean():.1f}/10")
        m3.metric("Gap Global", f"{df_empresa['Objetivo'].mean() - df_empresa['Actual'].mean():.1f}")
        
        res_radar = []
        for d in ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]:
            sub = df_empresa[df_empresa['Dimensión'] == d]
            res_radar.append({"Dimensión": d, "Actual": round(sub['Actual'].mean(), 1) if not sub.empty else 0, "Objetivo": round(sub['Objetivo'].mean(), 1) if not sub.empty else 0})
        
        df_p = pd.DataFrame(res_radar)
        df_p["Brecha"] = df_p["Objetivo"] - df_p["Actual"]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta'))
        fig_radar.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy'))
        st.plotly_chart(fig_radar, use_container_width=True)

        # TABLA CON CORRECCIÓN DE FORMATO POR COLUMNA
        st.table(df_p.style.map(
            lambda x: 'background-color: #fecaca' if x > 2 else 'background-color: #bbf7d0', 
            subset=['Brecha']
        ).format({
            "Actual": "{:.1f}", 
            "Objetivo": "{:.1f}", 
            "Brecha": "{:.1f}"
        }))

# --- TAB 3: REPORTE ---
with tab3:
    if not df_empresa.empty:
        col_t, col_b = st.columns([4, 1])
        col_t.subheader("Resumen de Compromisos")
        with col_b:
            w_bin = generar_word(empresa_sel, df_empresa, fig_radar, logo_file)
            st.download_button("📥 Descargar Word", data=w_bin, file_name=f"Informe_{empresa_sel}.docx")
        st.dataframe(df_empresa[["Dimensión", "Nombre", "Actual", "Brecha", "Accion_1"]].sort_values(by="Brecha", ascending=False), use_container_width=True)