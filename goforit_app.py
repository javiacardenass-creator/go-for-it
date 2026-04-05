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
    div.stButton > button { width: 100%; border-radius: 8px; height: 3em; background-color: #2563eb; color: white; }
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
        return pd.DataFrame(columns=["Empresa", "Dimensión", "Foco", "Nombre", "Actual", "Objetivo", "Brecha", "Facilita", "Dificulta", "No_Hacemos", "Distintos", "Accion_1", "Accion_2"])

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
    
    if fig:
        doc.add_heading('1. Radar Estratégico', level=1)
        img_bytes = fig.to_image(format="png", engine="kaleido")
        doc.add_picture(BytesIO(img_bytes), width=Inches(5.5))
    
    doc.add_heading('2. Detalle de Hallazgos y Compromisos', level=1)
    for _, row in df_filtrado.iterrows():
        doc.add_heading(f"{row['Dimensión']} - {row['Foco']}", level=2)
        doc.add_paragraph(f"Participante: {row['Nombre']} | Puntaje: {row['Actual']}/{row['Objetivo']}")
        doc.add_paragraph(f"Facilita: {row['Facilita']}").italic = True
        doc.add_paragraph(f"Dificulta: {row['Dificulta']}").italic = True
        doc.add_paragraph(f"Diferencial: {row['Distintos']}")
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

tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Radar Analítico", "📋 Reporte Ejecutivo"])

# --- TAB 1: REGISTRO (CON TODOS LOS CAMPOS) ---
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
        
        st.markdown("### 🗣️ Retroalimentación Cualitativa")
        t1, t2 = st.columns(2)
        f_fac = t1.text_area("¿Qué facilita el proceso?", height=80)
        f_dif = t1.text_area("¿Qué lo dificulta?", height=80)
        f_no = t2.text_area("¿Qué NO estamos haciendo?", height=80)
        f_dis = t2.text_area("¿Qué nos hace distintos?", height=80)
        
        a1 = st.text_input("Acción 1:"); a2 = st.text_input("Acción 2:")
        
        if st.form_submit_button("✅ Guardar Registro"):
            if nom and foc:
                guardar_fila_google({
                    "Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom, 
                    "Actual": act, "Objetivo": obj, "Brecha": obj-act,
                    "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no, "Distintos": f_dis,
                    "Accion_1": a1, "Accion_2": a2
                })
                st.session_state.form_reset += 1
                st.rerun()

# --- LÓGICA DE FILTROS REUTILIZABLE ---
def filtrar_df(df, key_prefix):
    st.markdown("### 🔍 Filtros de Análisis")
    c1, c2, c3 = st.columns(3)
    p_f = c1.multiselect("Pilares:", df['Dimensión'].unique(), default=df['Dimensión'].unique(), key=f"p_{key_prefix}")
    f_f = c2.multiselect("Focos:", df['Foco'].unique(), default=df['Foco'].unique(), key=f"f_{key_prefix}")
    n_f = c3.multiselect("Participantes:", df['Nombre'].unique(), default=df['Nombre'].unique(), key=f"n_{key_prefix}")
    return df[(df['Dimensión'].isin(p_f)) & (df['Foco'].isin(f_f)) & (df['Nombre'].isin(n_f))]

# --- TAB 2: RADAR ---
with tab2:
    if not df_empresa.empty:
        df_f_radar = filtrar_df(df_empresa, "rad")
        if not df_f_radar.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Madurez", f"{df_f_radar['Actual'].mean():.1f}/10")
            m2.metric("Meta", f"{df_f_radar['Objetivo'].mean():.1f}/10")
            m3.metric("Brecha", f"{(df_f_radar['Objetivo'].mean() - df_f_radar['Actual'].mean()):.1f}")
            
            res = []
            for d in ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]:
                sub = df_f_radar[df_f_radar['Dimensión'] == d]
                res.append({"Dimensión": d, "Actual": sub['Actual'].mean() if not sub.empty else 0, "Objetivo": sub['Objetivo'].mean() if not sub.empty else 0})
            df_p = pd.DataFrame(res); df_p["Brecha"] = df_p["Objetivo"] - df_p["Actual"]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta'))
            fig_radar.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy'))
            st.plotly_chart(fig_radar, use_container_width=True)
            st.table(df_p.style.map(lambda x: 'background-color: #fecaca' if x > 2 else 'background-color: #bbf7d0', subset=['Brecha']).format({"Actual": "{:.1f}", "Objetivo": "{:.1f}", "Brecha": "{:.1f}"}))

# --- TAB 3: REPORTE (GRÁFICA Y FILTROS RESTAURADOS) ---
with tab3:
    if not df_empresa.empty:
        df_f_rep = filtrar_df(df_empresa, "rep")
        
        # Gráfica pequeña de resumen
        res_rep = []
        for d in df_f_rep['Dimensión'].unique():
            sub = df_f_rep[df_f_rep['Dimensión'] == d]
            res_rep.append({"Dimensión": d, "Brecha": sub['Brecha'].mean()})
        df_res_rep = pd.DataFrame(res_rep)
        
        col_t, col_b = st.columns([4, 1])
        col_t.subheader("Resumen Ejecutivo de Hallazgos")
        with col_b:
            # Aquí generamos el Word con la gráfica del radar del Tab 2 (si existe)
            w_bin = generar_word(empresa_sel, df_f_rep, None, logo_file)
            st.download_button("📥 Descargar Reporte Word", data=w_bin, file_name=f"Estrategia_{empresa_sel}.docx")
        
        if not df_res_rep.empty:
            st.bar_chart(df_res_rep.set_index("Dimensión"))
            
        st.dataframe(df_f_rep[["Dimensión", "Foco", "Nombre", "Actual", "Brecha", "Distintos", "Accion_1"]].sort_values(by="Brecha", ascending=False), use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")