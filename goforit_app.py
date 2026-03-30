import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import os
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Inches

# --- CONFIGURACIÓN DE SECRETOS Y RUTAS ---
SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"

if not os.path.exists(LOGO_PATH):
    os.makedirs(LOGO_PATH, exist_ok=True)

st.set_page_config(page_title="Go For It | Consultoría Pro", layout="wide")

# --- INICIALIZACIÓN DE ESTADOS (Para limpiar formulario) ---
if 'form_reset' not in st.session_state:
    st.session_state.form_reset = 0

# --- FUNCIONES DE DATOS ---
def leer_datos():
    try:
        # Importante: La hoja debe estar "Publicada en la web"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        return df.dropna(subset=['Empresa'])
    except:
        return pd.DataFrame(columns=["Empresa", "Dimensión", "Foco", "Nombre", "Actual", "Objetivo", "Brecha", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"])

def guardar_fila_google(datos_dict):
    try:
        response = requests.post(SCRIPT_URL, json=datos_dict)
        return response.status_code == 200
    except:
        return False

# --- ESTILO VISUAL PERSONALIZADO ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        height: 45px; background-color: #f1f5f9; border-radius: 5px 5px 0 0; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN GENERAR INFORME WORD ---
def generar_word(empresa, df, fig, logo_p):
    doc = Document()
    doc.add_heading(f'Informe Estratégico: {empresa}', 0)
    if os.path.exists(logo_p):
        try: doc.add_picture(logo_p, width=Inches(1.5))
        except: pass
    
    doc.add_heading('1. Análisis de Madurez (Radar)', level=1)
    if fig:
        img_bytes = fig.to_image(format="png", engine="kaleido")
        doc.add_picture(BytesIO(img_bytes), width=Inches(5.5))

    doc.add_heading('2. Compromisos y Acciones', level=1)
    for pilar in df['Dimensión'].unique():
        doc.add_heading(f'Pilar: {pilar}', level=2)
        sub = df[df['Dimensión'] == pilar]
        table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
        hdr = table.rows[0].cells
        hdr[0].text = 'Participante (Foco)'; hdr[1].text = 'Puntaje'; hdr[2].text = 'Brecha'; hdr[3].text = 'Acciones'
        for _, row in sub.iterrows():
            cells = table.add_row().cells
            cells[0].text = f"{row['Nombre']}\n({row['Foco']})"
            cells[1].text = f"{row['Actual']}/{row['Objetivo']}"
            cells[2].text = str(row['Brecha'])
            cells[3].text = f"1. {row['Accion_1']}\n2. {row['Accion_2']}"
    
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- LÓGICA DE NAVEGACIÓN ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

st.sidebar.title("🚀 Go For It Cloud")
empresa_sel = st.sidebar.selectbox("Seleccione Cliente:", ["-- Nuevo Proyecto --"] + empresas_list)

dimensiones = ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]

if empresa_sel == "-- Nuevo Proyecto --":
    with st.sidebar.expander("✨ Registrar Empresa", expanded=True):
        nueva = st.text_input("Nombre de la Empresa:")
        logo_subido = st.file_uploader("Subir Logo", type=["png", "jpg"])
        if st.button("Activar Proyecto"):
            if nueva:
                # Registro inicial silencioso
                guardar_fila_google({
                    "Empresa": nueva, "Dimensión": "Alineación Estratégica", "Foco": "General", 
                    "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Brecha": 0,
                    "Facilita": "", "Dificulta": "", "No_Hacemos": "", "Accion_1": "", "Accion_2": ""
                })
                if logo_subido: Image.open(logo_subido).save(os.path.join(LOGO_PATH, f"{nueva}.png"))
                st.success("¡Proyecto activado!")
                st.rerun()
    st.stop()

# --- INTERFAZ DE CONSULTORÍA ---
df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

col_l, col_r = st.columns([1, 4])
with col_l:
    if os.path.exists(logo_file): st.image(logo_file, width=130)
with col_r:
    st.title(f"Diagnóstico: {empresa_sel}")

tab1, tab2, tab3 = st.tabs(["📝 Evaluación", "📊 Radar Dinámico", "📋 Resumen Ejecutivo"])

# --- PESTAÑA 1: FORMULARIO CON AUTO-LIMPIEZA ---
with tab1:
    # El counter form_reset hace que el formulario se vacíe al guardar
    with st.form(key=f"eval_form_{st.session_state.form_reset}"):
        st.subheader("Nueva Entrada de Datos")
        c1, c2 = st.columns(2)
        dim = c1.selectbox("Pilar Estratégico:", dimensiones)
        foc = c2.text_input("Foco / Área específica:", value="General")
        
        ca, cb, cc = st.columns([2, 1, 1])
        nom = ca.text_input("Nombre del Participante:")
        act = cb.slider("Nivel Actual", 1, 10, 5)
        obj = cc.slider("Nivel Objetivo", 1, 10, 8)
        
        col_text1, col_text2 = st.columns(2)
        f_fac = col_text1.text_area("¿Qué facilita el proceso?", height=80)
        f_dif = col_text1.text_area("¿Qué lo dificulta?", height=80)
        f_no = col_text2.text_area("¿Qué NO estamos haciendo?", height=175)
        
        a1 = st.text_input("Acción Inmediata 1:")
        a2 = st.text_input("Acción Inmediata 2:")
        
        if st.form_submit_button("💾 Guardar y Sincronizar"):
            if nom and foc:
                datos = {
                    "Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom,
                    "Actual": act, "Objetivo": obj, "Brecha": obj - act,
                    "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no,
                    "Accion_1": a1, "Accion_2": a2
                }
                if guardar_fila_google(datos):
                    st.session_state.form_reset += 1 # Esto limpia las casillas
                    st.success(f"Información de {nom} guardada correctamente.")
                    st.rerun()
                else:
                    st.error("Error al conectar con la base de datos de Google.")

# --- PESTAÑA 2: RADAR DINÁMICO CON FILTROS ---
fig_radar = None
with tab2:
    if not df_empresa.empty:
        st.subheader("Radar de Madurez Estratégica")
        
        col_filt1, col_filt2 = st.columns(2)
        with col_filt1:
            focos_disponibles = sorted(df_empresa['Foco'].unique().tolist())
            focos_sel = st.multiselect("Filtrar por Focos:", focos_disponibles, default=focos_disponibles)
        with col_filt2:
            nombres_disponibles = sorted(df_empresa['Nombre'].unique().tolist())
            nombres_sel = st.multiselect("Filtrar por Participantes:", nombres_disponibles, default=nombres_disponibles)

        # Filtrado de datos para el radar
        df_radar = df_empresa[
            (df_empresa['Foco'].isin(focos_sel)) & 
            (df_empresa['Nombre'].isin(nombres_sel))
        ]

        if not df_radar.empty:
            res_radar = []
            for d in dimensiones:
                sub = df_radar[df_radar['Dimensión'] == d]
                res_radar.append({
                    "Eje": d, 
                    "Act": sub['Actual'].mean() if not sub.empty else 0, 
                    "Obj": sub['Objetivo'].mean() if not sub.empty else 0
                })
            df_plot = pd.DataFrame(res_radar)

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=df_plot['Act'], theta=df_plot['Eje'], fill='toself', 
                name='Estado Actual', line_color='#E11D48', fillcolor='rgba(225, 29, 72, 0.3)'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=df_plot['Obj'], theta=df_plot['Eje'], fill='toself', 
                name='Meta Objetivo', line_color='#1E3A8A', fillcolor='rgba(30, 58, 138, 0.2)'
            ))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#cbd5e1")),
                height=550, margin=dict(l=100, r=100, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("No hay datos suficientes para generar el radar.")

# --- PESTAÑA 3: RESUMEN Y EXPORTACIÓN ---
with tab3:
    if not df_empresa.empty:
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn2:
            word_bin = generar_word(empresa_sel, df_empresa, fig_radar, logo_file)
            st.download_button("📄 Descargar Reporte Word", data=word_bin, file_name=f"Informe_{empresa_sel}.docx")
        
        st.markdown("### Tabla de Compromisos")
        st.dataframe(df_empresa[["Nombre", "Foco", "Dimensión", "Actual", "Brecha", "Accion_1"]].sort_values(by="Brecha", ascending=False), use_container_width=True)