import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Inches
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE DIRECTORIOS PARA LOGOS ---
LOGO_PATH = "Logos_GoForIt"
if not os.path.exists(LOGO_PATH): 
    os.makedirs(LOGO_PATH, exist_ok=True)

st.set_page_config(page_title="Go For It | Consultoría Pro", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos():
    try:
        # ttl="0m" obliga a leer datos frescos de Google en cada recarga
        return conn.read(ttl="0m")
    except:
        return pd.DataFrame(columns=["Empresa", "Dimensión", "Foco", "Nombre", "Actual", "Objetivo", "Brecha", "Facilita", "Dificulta", "No_Hacemos", "Accion_1", "Accion_2"])

# --- ESTILO CSS ---
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

# --- FUNCIÓN GENERAR WORD ---
def exportar_reporte_word(empresa, df, fig, logo_path):
    doc = Document()
    doc.add_heading(f'Informe Estratégico: {empresa}', 0)
    if os.path.exists(logo_path):
        try: doc.add_picture(logo_path, width=Inches(1.5))
        except: pass
    doc.add_heading('1. Radar de Madurez', level=1)
    try:
        img_bytes = fig.to_image(format="png", engine="kaleido")
        doc.add_picture(BytesIO(img_bytes), width=Inches(5.5))
    except: doc.add_paragraph("[Gráfico no disponible en la exportación]")
    
    doc.add_heading('2. Diagnóstico por Participante', level=1)
    for pilar in df['Dimensión'].unique():
        doc.add_heading(f'Pilar: {pilar}', level=2)
        sub = df[df['Dimensión'] == pilar]
        table = doc.add_table(rows=1, cols=4); table.style = 'Table Grid'
        hdr = table.rows[0].cells
        hdr[0].text = 'Nombre/Foco'; hdr[1].text = 'Puntaje'; hdr[2].text = 'Brecha'; hdr[3].text = 'Acciones'
        for _, row in sub.iterrows():
            cells = table.add_row().cells
            cells[0].text = f"{row['Nombre']}\n({row['Foco']})"
            cells[1].text = f"{row['Actual']}/{row['Objetivo']}"
            cells[2].text = str(row['Brecha'])
            cells[3].text = f"1. {row['Accion_1']}\n2. {row['Accion_2']}"
    target = BytesIO(); doc.save(target)
    return target.getvalue()

# --- GESTIÓN DE PROYECTOS (SIDEBAR) ---
df_global = leer_datos()
# Limpiar datos nulos si los hay
df_global = df_global.dropna(subset=['Empresa']) if not df_global.empty else df_global
empresas_existentes = sorted(df_global['Empresa'].unique().tolist())

st.sidebar.title("🚀 Go For It Cloud")
empresa_sel = st.sidebar.selectbox("Seleccione Cliente:", ["-- Nuevo Proyecto --"] + empresas_existentes)

# --- BORRAR EMPRESA ---
if empresa_sel != "-- Nuevo Proyecto --":
    st.sidebar.divider()
    with st.sidebar.expander("⚠️ Zona de Peligro"):
        if st.button(f"Borrar datos de {empresa_sel}"):
            df_final = df_global[df_global['Empresa'] != empresa_sel]
            conn.update(data=df_final)
            logo_path = os.path.join(LOGO_PATH, f"{empresa_sel}.png")
            if os.path.exists(logo_path): os.remove(logo_path)
            st.success("Empresa eliminada de la nube.")
            st.rerun()

# --- CREAR EMPRESA ---
if empresa_sel == "-- Nuevo Proyecto --":
    with st.sidebar.expander("✨ Registrar Nueva Empresa", expanded=True):
        nueva = st.text_input("Nombre de la empresa:")
        nuevo_logo = st.file_uploader("Cargar Logo", type=["png", "jpg"])
        if st.button("Activar Proyecto"):
            if nueva:
                # Fila de inicialización para que aparezca en el selectbox
                init_row = pd.DataFrame([{
                    "Empresa": nueva, "Dimensión": "Alineación Estratégica", "Foco": "General", 
                    "Nombre": "Configuración", "Actual": 1, "Objetivo": 1, "Brecha": 0,
                    "Facilita": "", "Dificulta": "", "No_Hacemos": "", "Accion_1": "", "Accion_2": ""
                }])
                df_up = pd.concat([df_global, init_row], ignore_index=True)
                conn.update(data=df_up)
                if nuevo_logo: Image.open(nuevo_logo).save(os.path.join(LOGO_PATH, f"{nueva}.png"))
                st.success("Proyecto creado. Selecciónelo arriba.")
                st.rerun()
    st.stop()

# --- FILTRAR DATOS EMPRESA ACTUAL ---
df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

# --- CABECERA ---
col_l, col_t = st.columns([1, 4])
with col_l:
    if os.path.exists(logo_file): st.image(logo_file, width=150)
with col_t:
    st.title(f"Proyecto: {empresa_sel}")

tab1, tab2, tab3 = st.tabs(["📝 Evaluación", "📊 Radar Estratégico", "📋 Resumen Ejecutivo"])

dimensiones = ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]

# --- PESTAÑA 1: EVALUACIÓN ---
with tab1:
    c_a, c_b = st.columns(2)
    with c_a: dim_actual = st.selectbox("📍 Pilar Estratégico:", dimensiones)
    with c_b:
        f_existentes = sorted(df_empresa['Foco'].unique().tolist()) if not df_empresa.empty else []
        f_opcion = st.radio("Foco:", ["Existente", "Nuevo"], horizontal=True)
        foco_actual = st.selectbox("Foco actual:", f_existentes) if f_opcion == "Existente" and f_existentes else st.text_input("Nuevo Foco:", value="General")

    nombres_reg = sorted(df_empresa[df_empresa['Dimensión'] == dim_actual]['Nombre'].unique().tolist())
    part_sel = st.selectbox("👤 Participante:", ["-- Nuevo --"] + nombres_reg)

    d_pre = {"Nom": "", "Act": 5, "Obj": 8, "Fa": "", "Di": "", "No": "", "A1": "", "A2": ""}
    if part_sel != "-- Nuevo --":
        r = df_empresa[(df_empresa['Nombre'] == part_sel) & (df_empresa['Dimensión'] == dim_actual)].iloc[0]
        d_pre = {"Nom": r['Nombre'], "Act": r['Actual'], "Obj": r['Objetivo'], "Fa": r['Facilita'], "Di": r['Dificulta'], "No": r['No_Hacemos'], "A1": r['Accion_1'], "A2": r['Accion_2']}

    with st.form("f_eval"):
        c1, c2, c3 = st.columns([2, 1, 1])
        n_in = c1.text_input("Nombre", value=d_pre["Nom"])
        s_act = c2.slider("Actual", 1, 10, int(d_pre["Act"]))
        s_obj = c3.slider("Objetivo", 1, 10, int(d_pre["Obj"]))
        ca, cb = st.columns(2)
        f_fac = ca.text_area("Facilita", value=d_pre["Fa"], height=70)
        f_dif = ca.text_area("Dificulta", value=d_pre["Di"], height=70)
        f_no = cb.text_area("No hacemos", value=d_pre["No"], height=160)
        a1 = st.text_input("Acción 1", value=d_pre["A1"])
        a2 = st.text_input("Acción 2", value=d_pre["A2"])
        
        if st.form_submit_button("💾 Guardar y Sincronizar"):
            if n_in:
                # Eliminar previo y añadir nuevo
                df_global = df_global[~((df_global['Empresa'] == empresa_sel) & (df_global['Nombre'] == n_in) & (df_global['Dimensión'] == dim_actual))]
                nuevo_reg = pd.DataFrame([{
                    "Empresa": empresa_sel, "Dimensión": dim_actual, "Foco": foco_actual, "Nombre": n_in, 
                    "Actual": s_act, "Objetivo": s_obj, "Brecha": s_obj - s_act, "Facilita": f_fac, 
                    "Dificulta": f_dif, "No_Hacemos": f_no, "Accion_1": a1, "Accion_2": a2
                }])
                df_final = pd.concat([df_global, nuevo_reg], ignore_index=True)
                conn.update(data=df_final)
                st.success("¡Datos guardados en Google Sheets!")
                st.rerun()

# --- PESTAÑA 2: RADAR ---
with tab2:
    if not df_empresa.empty:
        modo = st.radio("Radar por:", ["Pilar", "Foco"], horizontal=True)
        col_g = "Dimensión" if modo == "Pilar" else "Foco"
        etqs = dimensiones if modo == "Pilar" else sorted(df_empresa['Foco'].unique())
        res = []
        for e in etqs:
            sub = df_empresa[df_empresa[col_g] == e]
            res.append({"Eje": e, "Act": sub['Actual'].mean() if not sub.empty else 0, "Obj": sub['Objetivo'].mean() if not sub.empty else 0})
        df_r = pd.DataFrame(res)
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=df_r['Act'], theta=df_r['Eje'], fill='toself', name='Realidad', line_color='#E11D48'))
        fig.add_trace(go.Scatterpolar(r=df_r['Obj'], theta=df_r['Eje'], fill='toself', name='Objetivo', line_color='#2563EB'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=500)
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("No hay evaluaciones registradas.")

# --- PESTAÑA 3: RESUMEN Y REPORTES ---
with tab3:
    if not df_empresa.empty:
        c_f1, c_f2 = st.columns(2)
        p_s = c_f1.selectbox("Filtrar Pilar:", ["Todos"] + dimensiones)
        f_s = c_f2.selectbox("Filtrar Foco:", ["Todos"] + sorted(df_empresa['Foco'].unique().tolist()))
        df_f = df_empresa.copy()
        if p_s != "Todos": df_f = df_f[df_f['Dimensión'] == p_s]
        if f_s != "Todos": df_f = df_f[df_f['Foco'] == f_s]
        
        st.divider()
        # Generar reporte con los datos actuales
        word_data = exportar_reporte_word(empresa_sel, df_empresa, fig if 'fig' in locals() else None, logo_file)
        st.download_button("📄 Descargar Informe Word", data=word_data, file_name=f"Informe_{empresa_sel}.docx")
        st.divider()
        
        st.markdown("### 📋 Calificaciones")
        try:
            pivot = df_f.pivot_table(index='Nombre', columns='Dimensión', values='Actual', aggfunc='mean').fillna(0)
            st.dataframe(pivot.style.background_gradient(cmap='Blues'), use_container_width=True)
        except: st.dataframe(df_f)
        
        st.markdown("### 🚩 Plan de Acción")
        st.table(df_f[["Nombre", "Foco", "Dimensión", "Actual", "Brecha", "Accion_1"]].sort_values(by="Brecha", ascending=False))