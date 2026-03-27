import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import os
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Inches

# --- CONFIGURACIÓN DE SECRETOS ---
SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"

if not os.path.exists(LOGO_PATH):
    os.makedirs(LOGO_PATH, exist_ok=True)

st.set_page_config(page_title="Go For It | Consultoría Pro", layout="wide")

# --- FUNCIONES DE DATOS (GRATIS) ---
def leer_datos():
    try:
        # Leemos la hoja como CSV público (debe estar "Publicado en la Web")
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        df = pd.read_csv(url)
        return df.dropna(how='all')
    except:
        return pd.DataFrame(columns=["Empresa", "Dimensión", "Foco", "Nombre", "Actual", "Objetivo", "Brecha", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"])

def guardar_fila_google(datos_dict):
    try:
        # Enviamos los datos al Apps Script que creaste
        response = requests.post(SCRIPT_URL, json=datos_dict)
        return response.status_code == 200
    except:
        return False

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #f1f5f9; border-radius: 5px 5px 0 0; padding: 10px 15px; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN REPORTE WORD ---
def generar_word(empresa, df, fig, logo_p):
    doc = Document()
    doc.add_heading(f'Informe Estratégico: {empresa}', 0)
    if os.path.exists(logo_p):
        try: doc.add_picture(logo_p, width=Inches(1.5))
        except: pass
    
    doc.add_heading('1. Radar de Madurez', level=1)
    if fig:
        img_bytes = fig.to_image(format="png", engine="kaleido")
        doc.add_picture(BytesIO(img_bytes), width=Inches(5.5))

    doc.add_heading('2. Diagnóstico Detallado', level=1)
    for pilar in df['Dimensión'].unique():
        doc.add_heading(f'Pilar: {pilar}', level=2)
        sub = df[df['Dimensión'] == pilar]
        table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
        hdr = table.rows[0].cells
        hdr[0].text = 'Nombre (Foco)'; hdr[1].text = 'Puntaje'; hdr[2].text = 'Brecha'; hdr[3].text = 'Acciones'
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

if empresa_sel == "-- Nuevo Proyecto --":
    with st.sidebar.expander("✨ Registrar Empresa", expanded=True):
        nueva = st.text_input("Nombre:")
        logo_subido = st.file_uploader("Logo", type=["png", "jpg"])
        if st.button("Activar"):
            if nueva:
                # Registro inicial en Google
                exito = guardar_fila_google({
                    "Empresa": nueva, "Dimensión": "Alineación Estratégica", "Foco": "General", 
                    "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Brecha": 0,
                    "Facilita": "", "Dificulta": "", "No_Hacemos": "", "Accion_1": "", "Accion_2": ""
                })
                if logo_subido: Image.open(logo_subido).save(os.path.join(LOGO_PATH, f"{nueva}.png"))
                st.success("Proyecto creado. Seleccione el cliente en la lista.")
                st.rerun()
    st.stop()

# --- INTERFAZ PRINCIPAL ---
df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists(logo_file): st.image(logo_file, width=120)
with col_title:
    st.title(f"Cliente: {empresa_sel}")

tab1, tab2, tab3 = st.tabs(["📝 Evaluación", "📊 Radar Plotly", "📋 Resumen"])

dimensiones = ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]

# --- PESTAÑA 1: FORMULARIO ---
with tab1:
    with st.form("form_eval"):
        c1, c2 = st.columns(2)
        dim = c1.selectbox("Pilar:", dimensiones)
        foc = c2.text_input("Foco:", value="General")
        
        ca, cb, cc = st.columns([2, 1, 1])
        nom = ca.text_input("Nombre Participante:")
        act = cb.slider("Actual", 1, 10, 5)
        obj = cc.slider("Objetivo", 1, 10, 8)
        
        f_fac = st.text_area("Facilita:", height=60)
        f_dif = st.text_area("Dificulta:", height=60)
        f_no = st.text_area("No hacemos:", height=60)
        a1 = st.text_input("Acción 1:")
        a2 = st.text_input("Acción 2:")
        
        if st.form_submit_button("💾 Guardar en la Nube"):
            if nom:
                datos = {
                    "Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom,
                    "Actual": act, "Objetivo": obj, "Brecha": obj - act,
                    "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no,
                    "Accion_1": a1, "Accion_2": a2
                }
                if guardar_fila_google(datos):
                    st.success("¡Sincronizado!")
                    st.rerun()
                else: st.error("Error al conectar con Google Script.")

# --- PESTAÑA 2: RADAR ---
fig_radar = None
with tab2:
    if not df_empresa.empty:
        res = []
        for d in dimensiones:
            sub = df_empresa[df_empresa['Dimensión'] == d]
            res.append({"Eje": d, "Act": sub['Actual'].mean() if not sub.empty else 0, "Obj": sub['Objetivo'].mean() if not sub.empty else 0})
        df_r = pd.DataFrame(res)
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=df_r['Act'], theta=df_r['Eje'], fill='toself', name='Realidad', line_color='#E11D48'))
        fig_radar.add_trace(go.Scatterpolar(r=df_r['Obj'], theta=df_r['Eje'], fill='toself', name='Objetivo', line_color='#2563EB'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=450)
        st.plotly_chart(fig_radar, use_container_width=True)

# --- PESTAÑA 3: REPORTES ---
with tab3:
    if not df_empresa.empty:
        word_btn = generar_word(empresa_sel, df_empresa, fig_radar, logo_file)
        st.download_button("📄 Bajar Reporte Word", data=word_btn, file_name=f"Informe_{empresa_sel}.docx")
        st.divider()
        st.table(df_empresa[["Nombre", "Dimensión", "Actual", "Brecha", "Accion_1"]])