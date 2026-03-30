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

# --- ESTADOS DE SESIÓN (Para limpieza de formulario) ---
if 'form_reset' not in st.session_state:
    st.session_state.form_reset = 0

# --- FUNCIONES DE DATOS ---
def leer_datos():
    try:
        # La hoja debe estar "Publicada en la web" en Google Sheets
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

tab1, tab2, tab3 = st.tabs(["📝 Evaluación", "📊 Radar & Brechas", "📋 Resumen Ejecutivo"])

# --- TAB 1: EVALUACIÓN (CON LIMPIEZA) ---
with tab1:
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
                    st.session_state.form_reset += 1
                    st.success(f"Información de {nom} guardada.")
                    st.rerun()
                else: st.error("Error al conectar con Google Script.")

# --- TAB 2: RADAR DINÁMICO & TABLA RESUMEN ---
fig_radar = None
with tab2:
    if not df_empresa.empty:
        st.subheader("Análisis de Madurez Estratégica")
        
        # Filtros Multiselect
        col_filt1, col_filt2 = st.columns(2)
        with col_filt1:
            focos_sel = st.multiselect("Filtrar Focos:", sorted(df_empresa['Foco'].unique()), default=sorted(df_empresa['Foco'].unique()))
        with col_filt2:
            nombres_sel = st.multiselect("Filtrar Participantes:", sorted(df_empresa['Nombre'].unique()), default=sorted(df_empresa['Nombre'].unique()))

        # Filtrado de datos
        df_radar_filtered = df_empresa[(df_empresa['Foco'].isin(focos_sel)) & (df_empresa['Nombre'].isin(nombres_sel))]

        if not df_radar_filtered.empty:
            res_radar = []
            for d in dimensiones:
                sub = df_radar_filtered[df_radar_filtered['Dimensión'] == d]
                res_radar.append({
                    "Dimensión": d, 
                    "Actual": round(sub['Actual'].mean(), 1) if not sub.empty else 0, 
                    "Objetivo": round(sub['Objetivo'].mean(), 1) if not sub.empty else 0
                })
            df_plot = pd.DataFrame(res_radar)
            df_plot["Brecha"] = df_plot["Objetivo"] - df_plot["Actual"]

            # --- GRÁFICO RADAR MEJORADO ---
            fig_radar = go.Figure()
            # Capa Objetivo
            fig_radar.add_trace(go.Scatterpolar(
                r=df_plot['Objetivo'], theta=df_plot['Dimensión'], fill='toself', 
                name='Meta Estratégica', line_color='#1E3A8A', fillcolor='rgba(30, 58, 138, 0.2)',
                marker=dict(symbol="diamond", size=8)
            ))
            # Capa Actual
            fig_radar.add_trace(go.Scatterpolar(
                r=df_plot['Actual'], theta=df_plot['Dimensión'], fill='toself', 
                name='Estado Actual', line_color='#E11D48', fillcolor='rgba(225, 29, 72, 0.4)',
                marker=dict(size=10, line=dict(color="white", width=2))
            ))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#cbd5e1")),
                height=550, margin=dict(l=80, r=80, t=30, b=30), paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            # --- TABLA RESUMEN CON SEMÁFORO ---
            st.markdown("---")
            st.markdown("### 📊 Indicadores por Pilar")
            
            def estilo_brecha(val):
                color = '#fecaca' if val > 2.0 else '#fef08a' if val > 0.5 else '#bbf7d0'
                return f'background-color: {color}'

            # Mostramos la tabla con formato y colores
            st.table(df_plot.style.applymap(estilo_brecha, subset=['Brecha']).format({
                "Actual": "{:.1f}", "Objetivo": "{:.1f}", "Brecha": "{:.1f}"
            }))
            
            st.info("💡 **Guía de colores:** Rojo (Brecha > 2.0), Amarillo (Brecha > 0.5), Verde (Meta cercana/cumplida).")
        else:
            st.warning("Selecciona al menos un filtro para ver los resultados.")
    else:
        st.info("Aún no hay datos para esta empresa.")

# --- TAB 3: RESUMEN EJECUTIVO ---
with tab3:
    if not df_empresa.empty:
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn2:
            word_bin = generar_word(empresa_sel, df_empresa, fig_radar, logo_file)
            st.download_button("📄 Bajar Reporte Word", data=word_bin, file_name=f"Informe_{empresa_sel}.docx")
        
        st.dataframe(
            df_empresa[["Nombre", "Foco", "Dimensión", "Actual", "Brecha", "Accion_1"]]
            .sort_values(by="Brecha", ascending=False), 
            use_container_width=True
        )