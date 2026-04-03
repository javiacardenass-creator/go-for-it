import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import os
from io import BytesIO
from PIL import Image
from docx import Document
from docx.shared import Inches

# --- CONFIGURACIÓN ---
SHEET_ID = st.secrets["SHEET_ID"]
SCRIPT_URL = st.secrets["SCRIPT_URL"]
LOGO_PATH = "Logos_GoForIt"

if not os.path.exists(LOGO_PATH):
    os.makedirs(LOGO_PATH, exist_ok=True)

st.set_page_config(page_title="Go For It | Consultoría Pro", layout="wide")

if 'form_reset' not in st.session_state:
    st.session_state.form_reset = 0

# --- FUNCIONES ---
def leer_datos():
    try:
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

# --- FUNCIÓN WORD ---
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

# --- LÓGICA ---
df_global = leer_datos()
empresas_list = sorted(df_global['Empresa'].unique().tolist()) if not df_global.empty else []

st.sidebar.title("🚀 Go For It Cloud")
empresa_sel = st.sidebar.selectbox("Seleccione Cliente:", ["-- Nuevo Proyecto --"] + empresas_list)

dimensiones = ["Intimidad Cliente-Mercado", "Liderazgo Producto-Servicio", "Excelencia Operacional", "Flujo de Caja Sostenible", "Aprendizaje Constante", "Alineación Estratégica"]

if empresa_sel == "-- Nuevo Proyecto --":
    with st.sidebar.expander("✨ Registrar Empresa", expanded=True):
        nueva = st.text_input("Nombre:")
        if st.button("Activar"):
            if nueva:
                guardar_fila_google({"Empresa": nueva, "Dimensión": "Alineación Estratégica", "Foco": "General", "Nombre": "Admin", "Actual": 1, "Objetivo": 1, "Brecha": 0})
                st.rerun()
    st.stop()

df_empresa = df_global[df_global['Empresa'] == empresa_sel]
logo_file = os.path.join(LOGO_PATH, f"{empresa_sel}.png")

tab1, tab2, tab3 = st.tabs(["📝 Evaluación", "📊 Radar", "📋 Resumen"])

# --- TAB 1 ---
with tab1:
    f_ex = sorted(df_empresa['Foco'].unique().tolist()) if not df_empresa.empty else []
    n_ex = sorted(df_empresa['Nombre'].unique().tolist()) if not df_empresa.empty else []
    
    col_m1, col_m2 = st.columns(2)
    m_foco = col_m1.radio("¿Foco?", ["Existente", "Nuevo"], horizontal=True, key=f"f_{st.session_state.form_reset}")
    m_nom = col_m2.radio("¿Participante?", ["Existente", "Nuevo"], horizontal=True, key=f"n_{st.session_state.form_reset}")

    with st.form(key=f"frm_{st.session_state.form_reset}"):
        c1, c2 = st.columns(2)
        dim = c1.selectbox("Pilar:", dimensiones)
        foc = c2.selectbox("Foco:", f_ex) if m_foco == "Existente" and f_ex else c2.text_input("Nuevo Foco:", "General")
        
        ca, cb, cc = st.columns([2, 1, 1])
        nom = ca.selectbox("Nombre:", n_ex) if m_nom == "Existente" and n_ex else ca.text_input("Nuevo Nombre:")
        act = cb.slider("Hoy", 1, 10, 5)
        obj = cc.slider("Meta", 1, 10, 8)
        
        t1, t2 = st.columns(2)
        f_fac = t1.text_area("Facilita", height=70)
        f_dif = t1.text_area("Dificulta", height=70)
        f_no = t2.text_area("Pendientes", height=155)
        a1 = st.text_input("Acción 1")
        a2 = st.text_input("Acción 2")
        
        if st.form_submit_button("💾 Guardar"):
            if nom and foc:
                res = guardar_fila_google({"Empresa": empresa_sel, "Dimensión": dim, "Foco": foc, "Nombre": nom, "Actual": act, "Objetivo": obj, "Brecha": obj-act, "Facilita": f_fac, "Dificulta": f_dif, "No_Hacemos": f_no, "Accion_1": a1, "Accion_2": a2})
                if res:
                    st.session_state.form_reset += 1
                    st.rerun()

# --- TAB 2 ---
fig_radar = None
with tab2:
    if not df_empresa.empty:
        res_radar = []
        for d in dimensiones:
            sub = df_empresa[df_empresa['Dimensión'] == d]
            res_radar.append({"Dimensión": d, "Actual": round(sub['Actual'].mean(), 1) if not sub.empty else 0, "Objetivo": round(sub['Objetivo'].mean(), 1) if not sub.empty else 0})
        df_p = pd.DataFrame(res_radar)
        df_p["Brecha"] = df_p["Objetivo"] - df_p["Actual"]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=df_p['Objetivo'], theta=df_p['Dimensión'], fill='toself', name='Meta'))
        fig_radar.add_trace(go.Scatterpolar(r=df_p['Actual'], theta=df_p['Dimensión'], fill='toself', name='Hoy'))
        st.plotly_chart(fig_radar, use_container_width=True)

        def estilo_brecha(val):
            return f'background-color: {"#fecaca" if val > 2.0 else "#bbf7d0"}'

        # AQUÍ ESTÁ EL CAMBIO DE applymap -> map
        st.table(df_p.style.map(estilo_brecha, subset=['Brecha']).format({"Actual": "{:.1f}", "Objetivo": "{:.1f}", "Brecha": "{:.1f}"}))

# --- TAB 3 ---
with tab3:
    if not df_empresa.empty:
        col_t, col_b = st.columns([3, 1])
        with col_b:
            w_bin = generar_word(empresa_sel, df_empresa, fig_radar, logo_file)
            st.download_button("📄 Word", data=w_bin, file_name=f"Informe_{empresa_sel}.docx")
        st.dataframe(df_empresa[["Nombre", "Foco", "Dimensión", "Actual", "Brecha", "Accion_1"]].sort_values(by="Brecha", ascending=False))