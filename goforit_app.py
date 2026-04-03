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
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO CSS PERSONALIZADO ---
st.markdown("""
    <style>
    /* Fondo y tipografía */
    .main { background-color: #f1f5f9; }
    [data-testid="stSidebar"] { background-color: #0f172a; color: white; }
    
    /* Títulos y subtítulos */
    h1 { color: #1e293b; font-weight: 800; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; }
    
    /* Botones y tarjetas */
    div.stButton > button {
        width: 100%;
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
        height: 3em;
    }
    div.stButton > button:hover { background-color: #1d4ed8; border: none; color: white; }
    
    /* Estilo de métricas */
    [data-testid="stMetricValue"] { font-size: 28px; color: #1e40af; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE SECRETOS ---
SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"

if not os.path.exists(LOGO_PATH):
    os.makedirs(LOGO_PATH, exist_ok=True)

if 'form_reset' not in st.session_state:
    st.session_state.form_reset = 0

# --- FUNCIONES CORE ---
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
    except:
        return False

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
    
    doc.add_heading('2. Plan de Acción', level=1)
    for pilar in df['Dimensión'].unique():
        doc.add_heading(pilar, level=2)
        sub = df[df['Dimensión'] == pilar]
        table = doc.add_table(rows=1, cols=3); table.style = 'Table Grid'
        hdr = table.rows[0].cells
        hdr[0].text = 'Participante'; hdr[1].text = 'Puntaje'; hdr[2].text = 'Acciones'
        for _, row in sub.iterrows():
            cells = table.add_row().cells
            cells[0].text = f"{row['Nombre']} ({row['Foco']})"
            cells[1].text = f"{row['Actual']}/{row['Objetivo']}"
            cells[2].text = f"- {row['Accion_1']}\n- {row['Accion_2']}"
    
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- BARRA LATERAL ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80) # Icono genérico o tu logo
    st.title("Consultoría Pro")
    st.markdown("---")
    empresa_sel = st.selectbox("🎯 Proyecto Actual:", ["-- Nuevo Proyecto --"] + empresas_list)
    
    if empresa_sel == "-- Nuevo Proyecto --":
        with st.expander("✨ Crear Empresa", expanded=True):
            nueva = st.text_input("Nombre de Empresa:")
            logo_subido = st.file_uploader("Logo (PNG/JPG)", type=["png", "jpg"])
            if st.button("Activar"):
                if nueva:
                    guardar_fila_google({"Empresa": nueva, "Dimensión": "Alineación Estratégica", "Foco": "General", "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Brecha": 0})
                    if logo_subido: Image.open(logo_subido).save(os.path.join(LOGO_PATH, f"{nueva}.png"))
                    st.rerun()
        st.stop()

# --- HEADER PRINCIPAL ---
df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

col_header_1, col_header_2 = st.columns([1, 5])
with col_header_1:
    if os.path.exists(logo_file): st.image(logo_file, width=120)
with col_header_2:
    st.title(f"Plan de Intervención: {empresa_sel}")
    st.caption("Advisor: Javier Andrés Cárdenas | Gestión Estratégica")

tab1, tab2, tab3 = st.tabs(["📝 Evaluación", "📊 Radar Estratégico", "📋 Resumen Ejecutivo"])

# --- TAB 1: EVALUACIÓN ---
with tab1:
    f_ex = sorted(df_empresa['Foco'].unique().tolist()) if not df_empresa.empty else []
    n_ex = sorted(df_empresa['Nombre'].unique().tolist()) if not df_empresa.empty else []
    
    st.info("Complete la evaluación del pilar seleccionado. Use 'Nuevo' para agregar áreas o personas.")
    
    c_m1, c_m2 = st.columns(2)
    m_foco = c_m1.radio("📌 Área / Foco:", ["Existente", "Nuevo"], horizontal=True, key=f"f_{st.session_state.form_reset}")
    m_nom = c_m2.radio("👤 Participante:", ["Existente", "Nuevo"], horizontal=True, key=f"n_{st.session_state.form_reset}")

    with st.form(key=f"form_{st.session_state.form_reset}", clear_on_submit=True):
        f1, f2 = st.columns(2)
        dim = f1.selectbox("Pilar Estratégico:", ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"])
        
        if m_foco == "Existente" and f_ex: foc = f2.selectbox("Foco Actual:", f_ex)
        else: foc = f2.text_input("Nombre del Nuevo Foco:", placeholder="Ej. Gerencia Comercial")
        
        st.divider()
        fa, fb, fc = st.columns([2, 1, 1])
        if m_nom == "Existente" and n_ex: nom = fa.selectbox("Nombre:", n_ex)
        else: nom = fa.text_input("Nuevo Participante:", placeholder="Ej. Juan Pérez")
        
        act = fb.select_slider("Hoy", options=range(1, 11), value=5)
        obj = fc.select_slider("Meta", options=range(1, 11), value=8)
        
        t1, t2 = st.columns(2)
        f_fac = t1.text_area("🚀 Facilitadores (¿Qué ayuda?)", height=100)
        f_dif = t1.text_area("⚠️ Limitantes (¿Qué frena?)", height=100)
        f_no = t2.text_area("💡 Brechas (¿Qué NO estamos haciendo?)", height=235)
        
        a1 = st.text_input("⚡ Acción Prioritaria 1:")
        a2 = st.text_input("⚡ Acción Prioritaria 2:")
        
        if st.form_submit_button("✅ Sincronizar con Estrategia"):
            if nom and foc:
                with st.spinner("Actualizando Google Sheets..."):
                    res = guardar_fila_google({"Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom, "Actual": act, "Objetivo": obj, "Brecha": obj-act, "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no, "Accion_1": a1, "Accion_2": a2})
                    if res:
                        st.session_state.form_reset += 1
                        st.toast("¡Datos guardados correctamente!", icon="💾")
                        st.rerun()

# --- TAB 2: ANALÍTICA ---
fig_radar = None
with tab2:
    if not df_empresa.empty:
        # Métricas Rápidas
        avg_act = df_empresa['Actual'].mean()
        avg_obj = df_empresa['Objetivo'].mean()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Madurez Promedio", f"{avg_act:.1f}/10")
        m2.metric("Meta Aspiracional", f"{avg_obj:.1f}/10")
        m3.metric("Gap Global", f"{avg_obj - avg_act:.1f}", delta_color="inverse")
        
        st.markdown("---")
        
        res_radar = []
        for d in ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]:
            sub = df_empresa[df_empresa['Dimensión'] == d]
            res_radar.append({"Dimensión": d, "Actual": round(sub['Actual'].mean(), 1) if not sub.empty else 0, "Objetivo": round(sub['Objetivo'].mean(), 1) if not sub.empty else 0})
        
        df_p = pd.DataFrame(res_radar)
        df_p["Brecha"] = df_p["Objetivo"] - df_p["Actual"]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta', line_color='#2563eb'))
        fig_radar.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy', line_color='#ef4444'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=500)
        st.plotly_chart(fig_radar, use_container_width=True)

        st.table(df_p.style.map(lambda x: 'background-color: #fecaca' if x > 2 else 'background-color: #bbf7d0', subset=['Brecha']).format("{:.1f}"))

# --- TAB 3: REPORTE ---
with tab3:
    if not df_empresa.empty:
        c_r1, c_r2 = st.columns([4, 1])
        c_r1.subheader("Resumen de Compromisos")
        with c_r2:
            w_bin = generar_word(empresa_sel, df_empresa, fig_radar, logo_file)
            st.download_button("📥 Descargar Word", data=w_bin, file_name=f"Informe_{empresa_sel}.docx", use_container_width=True)
        
        st.dataframe(df_empresa[["Dimensión", "Nombre", "Actual", "Brecha", "Accion_1", "Accion_2"]].sort_values(by="Brecha", ascending=False), use_container_width=True)