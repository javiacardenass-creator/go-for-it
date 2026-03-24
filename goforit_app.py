import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Inches

# --- CONFIGURACIÓN DE DIRECTORIOS (ADAPTADO PARA NUBE) ---
# Usamos rutas relativas simples
FOLDER_PATH = "Proyectos_GoForIt"
LOGO_PATH = "Logos_GoForIt"

for p in [FOLDER_PATH, LOGO_PATH]:
    if not os.path.exists(p):
        os.makedirs(p, exist_ok=True)

st.set_page_config(page_title="Go For It | Consultoría", layout="wide")

# --- FUNCIÓN WORD (SIN CAMBIOS) ---
def exportar_word(empresa, df, fig, logo_path):
    doc = Document()
    doc.add_heading(f'Informe Estratégico: {empresa}', 0)
    if os.path.exists(logo_path):
        try: doc.add_picture(logo_path, width=Inches(1.5))
        except: pass
    doc.add_heading('1. Radar Estratégico', level=1)
    try:
        img_bytes = fig.to_image(format="png", engine="kaleido")
        image_stream = BytesIO(img_bytes)
        doc.add_picture(image_stream, width=Inches(5.5))
    except Exception as e:
        doc.add_paragraph(f"[Gráfico no disponible en este reporte: {e}]")
    
    doc.add_heading('2. Diagnóstico y Plan de Acción', level=1)
    dimensiones_lista = ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", 
                         "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]
    for dim in dimensiones_lista:
        df_dim = df[df['Dimensión'] == dim]
        if not df_dim.empty:
            doc.add_heading(f'Dimensión: {dim}', level=2)
            table = doc.add_table(rows=1, cols=4)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Participante'; hdr_cells[1].text = 'Puntaje'; hdr_cells[2].text = 'Análisis'; hdr_cells[3].text = 'Acciones'
            for _, row in df_dim.iterrows():
                row_cells = table.add_row().cells
                row_cells[0].text = str(row['Nombre'])
                row_cells[1].text = f"{row['Actual']}/{row['Objetivo']}"
                row_cells[2].text = f"F:{row['Facilita']}\nD:{row['Dificulta']}\nN:{row['No_Hacemos']}"
                row_cells[3].text = f"1.{row['Accion_1']}\n2.{row['Accion_2']}"
    target = BytesIO(); doc.save(target)
    return target.getvalue()

# --- INTERFAZ ---
st.sidebar.title("🚀 Go For It Cloud")

# Listar empresas
archivos = [f.replace(".xlsx", "") for f in os.listdir(FOLDER_PATH) if f.endswith(".xlsx")]
empresa_sel = st.sidebar.selectbox("Cliente:", ["-- Nuevo --"] + archivos)

if empresa_sel == "-- Nuevo --":
    nueva = st.sidebar.text_input("Nombre empresa:")
    if st.sidebar.button("Crear"):
        pd.DataFrame().to_excel(os.path.join(FOLDER_PATH, f"{nueva}.xlsx"), index=False)
        st.rerun()
    st.stop()

DB_FILE = os.path.join(FOLDER_PATH, f"{empresa_sel}.xlsx")
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

# Carga de datos
if 'respuestas' not in st.session_state or st.session_state.get('empresa_actual') != empresa_sel:
    if os.path.exists(DB_FILE):
        try:
            df_init = pd.read_excel(DB_FILE)
            st.session_state.respuestas = df_init.to_dict('records') if not df_init.empty else []
        except: st.session_state.respuestas = []
    st.session_state.empresa_actual = empresa_sel

# --- FORMULARIO Y GRÁFICOS ---
dimensiones = ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", 
                "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]
dim_actual = st.sidebar.selectbox("📍 Dimensión:", dimensiones)

# (Lógica de sliders y guardado igual a la anterior...)
# [INSERTAR AQUÍ EL BLOQUE DE SLIDERS Y BOTÓN GUARDAR DEL CÓDIGO ANTERIOR]

# --- RECOMENDACIÓN DE SEGURIDAD PARA CLOUD ---
st.warning("⚠️ Nota: En la nube, descarga tu Excel o Word al finalizar. Los cambios no guardados en GitHub se perderán si la app se reinicia.")