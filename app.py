import streamlit as st
import pandas as pd              
import os
from datetime import date, timedelta

# ==========================================
# 1. PERSISTENCIA Y CONFIGURACIÓN (ISO 9001)
# ==========================================
DB_FILE = "database_tq_final.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Asegurar que la fecha sea objeto date
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    return pd.DataFrame(columns=['Fecha', 'Nombre Consumidor', 'Contacto', 'Ciudad Residencia', 'Region', 'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

st.set_page_config(page_title="Plan de Mejora Continua TQ", layout="wide")

# Inteligencia ISO 9001: Numerales y Acciones
DICCIONARIO_ISO = {
    "1. Calidad": {"numeral": "8.7 (Control de salidas no conformes)", "plan": "Segregación inmediata, análisis de lote y disposición final (ISO 9001:2015)."},
    "2. Precios": {"numeral": "8.2.1 (Comunicación con el cliente)", "plan": "Auditoría de precios en PDV y actualización masiva de listas en CRM."},
    "3. Logística": {"numeral": "8.4 (Control de suministros externos)", "plan": "Evaluación de desempeño del operador logístico y rediseño de rutas."},
    "4. Agotados": {"numeral": "8.1 (Planificación operacional)", "plan": "Ajuste de niveles de stock de seguridad y revisión de lead times."},
    "5. Atención": {"numeral": "7.2 (Competencia del personal)", "plan": "Plan de capacitación técnica en atención al consumidor y gestión de crisis."},
    "10. Otro": {"numeral": "10.2 (No conformidad y acción correctiva)", "plan": "Ejecución de metodología Ishikawa para hallar causa raíz sistémica."}
}

# ==========================================
# 2. GESTIÓN DE SESIÓN
# ==========================================
if 'db' not in st.session_state:
    st.session_state.db = cargar_datos()

# ==========================================
# 3. SIDEBAR: PANEL DE CARGA TQ
# ==========================================
st.sidebar.title("🏢 Tecnoquímicas S.A.")
st.sidebar.subheader("Registro Plan de Mejora")

with st.sidebar.form("form_registro", clear_on_submit=True):
    nombre = st.text_input("Nombre Consumidor / Punto de Venta")
    contacto = st.text_input("Contacto (Celular/Email)")
    ciudad = st.selectbox("Ciudad Residencia", ["Cali", "Bogotá", "Medellín", "Barranquilla", "Bucaramanga", "Pereira", "Manizales", "Pasto"])
    region = st.selectbox("Región", ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Santanderes", "Eje Cafetero"])
    canal = st.selectbox("Canal de Atención", ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa"])
    
    st.markdown("---")
    sat = st.slider("Satisfacción (%)", 0, 100, 80)
    reclamos = st.number_input("Cantidad de PQRS", 0, 100, 0)
    motivo = st.selectbox("Motivo PQRS", ["Ninguna (0 PQRS)"] + list(DICCIONARIO_ISO.keys()))
    obs = st.text_area("Observaciones de Campo")
    
    btn_guardar = st.form_submit_button("🚀 REGISTRAR AUDITORÍA")

if btn_guardar:
    if nombre and contacto:
        nuevo = pd.DataFrame([[date.today(), nombre, contacto, ciudad, region, canal, sat, reclamos, motivo, obs]], 
                             columns=st.session_state.db.columns)
        st.session_state.db = pd.concat([st.session_state.db, nuevo], ignore_index=True)
        guardar_datos(st.session_state.db)
        st.sidebar.success(f"✅ Guardado en {region} - Canal {canal}")
        st.balloons()
    else:
        st.sidebar.error("❌ Nombre y Contacto obligatorios")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Control de Datos")

# BOTÓN DE BORRADO ÚLTIMO REGISTRO (RECUPERADO)
if st.sidebar.button("🗑️ Eliminar Último Registro"):
    if not st.session_state.db.empty:
        st.session_state.db = st.session_state.db.iloc[:-1]
        guardar_datos(st.session_state.db)
        st.sidebar.warning("Registro eliminado de la base de datos.")
        st.rerun()

# DESCARGA
csv = st.session_state.db.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Descargar Base de Datos", csv, "base_tq_master.csv")

# ==========================================
# 4. DASHBOARD: ANALÍTICA EJECUTIVA
# ==========================================
st.title("📊 Plan de Mejora Continua: Canal de Ventas TQ")
st.markdown("---")

if st.session_state.db.empty:
    st.info("Sistema listo. Ingrese datos para generar análisis del Plan de Mejora.")
else:
    # FILTROS DINÁMICOS (CORREGIDOS: Solo muestran lo que hay en datos filtrados)
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        regiones_disp = st.session_state.db['Region'].unique()
        f_reg = st.multiselect("📍 Filtrar Región", regiones_disp, default=regiones_disp)
    with f_col2:
        canales_disp = st.session_state.db['Canal'].unique()
        f_can = st.multiselect("🔄 Filtrar Canal", canales_disp, default=canales_disp)

    df_f = st.session_state.db[(st.session_state.db['Region'].isin(f_reg)) & (st.session_state.db['Canal'].isin(f_can))]

    # MÉTRICAS CON INDICADOR DELTA
    m1, m2, m3, m4 = st.columns(4)
    avg_sat = df_f['Satisfaccion'].mean() if not df_f.empty else 0
    avg_nac = st.session_state.db['Satisfaccion'].mean()
    total_pqrs = df_f['Reclamos'].sum()

    m1.metric("Satisfacción Segmento", f"{avg_sat:.1f}%", delta=f"{avg_sat-80:.1f}% vs Meta")
    m2.metric("Total PQRS", int(total_pqrs))
    m3.metric("Auditorías", len(df_f))
    
    semaforo = "🟢 ÓPTIMO" if avg_sat >= 80 else "🟡 RIESGO" if avg_sat >= 60 else "🔴 CRÍTICO"
    m4.markdown(f"**Estado Gerencial:**\n### {semaforo}")

    # --- DOBLE GRÁFICA COMPARATIVA (NACIONAL VS FILTRADO) ---
    st.markdown("### 📈 Análisis Comparativo de Desempeño")
    g1, g2 = st.columns(2)
    
    with g1:
        st.write("**Selección vs Promedio Nacional**")
        df_comp = pd.DataFrame({
            'Valor %': [avg_nac, avg_sat]
        }, index=['Promedio Nacional', 'Tu Filtro'])
        st.bar_chart(df_comp)

    with g2:
        st.write("**Evolución de Satisfacción en el Tiempo**")
        df_ev = df_f.groupby('Fecha')['Satisfaccion'].mean()
        st.line_chart(df_ev)

# ==========================================
# 5. PESTAÑAS DE GESTIÓN E ISO (PLAN DE MEJORA)
# ==========================================
st.markdown("---")
tab_data, tab_iso = st.tabs(["🗄️ TRAZABILIDAD DE DATOS", "📑 PLAN DE ACCIÓN ISO 9001"])

with tab_data:
    st.subheader("Control Maestro de Registros")
    st.info("💡 Puedes editar celdas directamente o borrar filas seleccionándolas y presionando 'Delete'.")
    edited_db = st.data_editor(st.session_state.db, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Sincronizar Cambios Manuales"):
        st.session_state.db = edited_db
        guardar_datos(edited_db)
        st.success("Cambios sincronizados con el archivo CSV.")

with tab_iso:
    st.subheader("📋 Plan de Acción para Mejora Continua")
    df_pqrs = st.session_state.db[st.session_state.db['Motivo PQRS'] != "Ninguna (0 PQRS)"]
    
    if df_pqrs.empty:
        st.success("✅ **Sistema Conforme:** No se reportan hallazgos. Se recomienda continuar con el monitoreo preventivo.")
    else:
        # Validación de Moda (Evita el error potencial)
        moda_serie = df_pqrs['Motivo PQRS'].mode()
        
        if not moda_serie.empty:
            falla_principal = moda_serie[0]
            plan = DICCIONARIO_ISO.get(falla_principal, {"numeral": "General", "plan": "Análisis técnico requerido."})
            
            # Formato de Informe de Auditoría
            st.error(f"### Hallazgo de Auditoría: {falla_principal}")
            col_inf1, col_inf2 = st.columns(2)
            with col_inf1:
                st.markdown(f"**Referencia Normativa:**\n{plan['numeral']}")
            with col_inf2:
                st.markdown(f"**Acción Correctiva Sugerida:**\n{plan['plan']}")
            
            st.markdown("---")
            st.warning("**Sugerencia Estratégica:** Realizar comité de calidad enfocado en este numeral para evitar recurrencia.")
        else:
            st.info("Registra más quejas para generar un plan de acción estadístico.")

st.caption(f"Tecnoquímicas S.A. | Plan de Mejora v5.0 | {date.today()}")
