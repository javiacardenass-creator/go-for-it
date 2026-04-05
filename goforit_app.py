# --- BUSCAR DATOS PREVIOS (Lógica Reforzada) ---
# Buscamos en el DataFrame de la empresa seleccionada
match = df_emp[
    (df_emp['Dimensión'] == dim_f) & 
    (df_emp['Foco'] == foc_f) & 
    (df_emp['Nombre'] == nom_f)
]

row = match.iloc[0] if not match.empty else None

with st.form("form_smart"):
    st.subheader("✏️ Evaluación" if row is not None else "➕ Nuevo Registro")
    
    # ... (Sliders de Hoy y Meta se mantienen igual) ...

    # Lógica de extracción segura para evitar que se pierda el dato al cargar
    def obtener_valor(fila, col_nueva, col_vieja):
        if fila is None: return ""
        if col_nueva in fila and pd.notna(fila[col_nueva]): return str(fila[col_nueva])
        if col_vieja in fila and pd.notna(fila[col_vieja]): return str(fila[col_vieja])
        return ""

    val_cap = obtener_valor(row, 'Capacidades_Distintivas', 'Distintos')
    
    st.markdown("---")
    tx1, tx2 = st.columns(2)
    f_fac = tx1.text_area("¿Qué facilita?", value=obtener_valor(row, 'Facilita', 'Facilita'))
    f_dif = tx1.text_area("¿Qué dificulta?", value=obtener_valor(row, 'Dificulta', 'Dificulta'))
    f_no = tx2.text_area("¿Qué NO hacemos?", value=obtener_valor(row, 'No_Hacemos', 'No_Hacemos'))
    
    # Casilla crítica:
    f_cap = tx2.text_area("Capacidades Distintivas:", value=val_cap, help="Habilidades o recursos únicos.")
    
    # ... (Acciones 1 y 2 se mantienen igual) ...

    if st.form_submit_button("💾 Guardar Cambios"):
        payload = {
            "Empresa": emp_sel,
            "Dimensión": dim_f,
            "Foco": foc_f,
            "Nombre": nom_f,
            "Actual": v_act,
            "Objetivo": v_obj,
            "Brecha": v_obj - v_act,
            "Facilita": f_fac,
            "Dificulta": f_dif,
            "No_Hacemos": f_no,
            "Capacidades_Distintivas": f_cap, # Enviamos con el nombre nuevo
            "Distintos": f_cap,               # Enviamos también con el nombre viejo por si el Script no se ha actualizado
            "Accion_1": a1,
            "Accion_2": a2
        }
        if enviar_datos(payload):
            st.success("Información sincronizada correctamente.")
            st.cache_data.clear()
            st.rerun()