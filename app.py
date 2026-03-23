import streamlit as st
import pandas as pd
from datetime import date, timedelta

# ==========================================
# CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="App Auditoría TQ - PRO", layout="wide")

# Columnas actualizadas con "Ciudad"
COLUMNAS = [
    'Fecha', 'Nombre', 'Contacto', 'Ciudad', 'Region', 'Canal',
    'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'
]

# ==========================================
# MEMORIA SEGURA (ESTADO)
# ==========================================
if 'datos_historico' not in st.session_state:
    st.session_state.datos_historico = pd.DataFrame(columns=COLUMNAS)

if 'datos_dashboard' not in st.session_state:
    st.session_state.datos_dashboard = pd.DataFrame(columns=COLUMNAS)

# ==========================================
# DICCIONARIO ISO 
# ==========================================
SOLUCIONES_ISO = {
    "1. Calidad": "Aplicar protocolo de Cuarentena (ISO 8.7).",
    "2. Precios": "Auditoría de facturación (ISO 8.2).",
    "3. Logística": "Optimizar rutas y tiempos (ISO 8.4).",
    "4. Agotados": "Ajustar pronóstico de demanda.",
    "5. Atención": "Capacitación en servicio al cliente.",
    "6. Vencimientos": "Implementar FEFO.",
    "7. Averías": "Mejorar embalaje.",
    "8. Cambios": "Optimizar devoluciones.",
    "9. Publicidad": "Validar comunicación comercial.",
    "10. Otro": "Análisis de causa raíz."
}

# ==========================================
# SIMULADOR DE LOGIN / ROLES (Nivel Empresa)
# ==========================================
col_login1, col_login2 = st.columns([8, 2])
with col_login2:
    rol_usuario = st.selectbox("🔐 Perfil Activo:", ["Supervisor", "Auditor", "Gerencia"])

# ==========================================
# SIDEBAR: INGRESO DE DATOS
# ==========================================
st.sidebar.title("🏢 TECNOQUÍMICAS")
st.sidebar.markdown("Sistema de Gestión - Ingreso")

with st.sidebar.form("formulario", clear_on_submit=True):
    nombre = st.text_input("Nombre Cliente")
    contacto = st.text_input("Contacto")
    ciudad = st.text_input("Ciudad / Municipio") # NUEVO CAMPO
    region = st.selectbox("Región", ["Antioquia", "Bogotá", "Valle", "Costa", "Otro"])
    canal = st.selectbox("Canal", ["Ventas", "Mercadeo", "Digital"]) # CORRECCIÓN LÓGICA
    satisfaccion = st.slider("Satisfacción", 0, 100, 80)
    reclamos = st.number_input("Cantidad PQRS", 0, 50, 0)
    motivo = st.selectbox("Motivo PQRS", [
        "Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística",
        "4. Agotados", "5. Atención", "6. Vencimientos",
        "7. Averías", "8. Cambios", "9. Publicidad", "10. Otro"
    ])
    obs = st.text_area("Observaciones")
    guardar = st.form_submit_button("Guardar Registro")

if guardar:
    nuevo = pd.DataFrame([[
        str(date.today()), nombre, contacto, ciudad, region,
        canal, satisfaccion, reclamos, motivo, obs
    ]], columns=COLUMNAS)

    # Guarda en ambos para mantener sincronía inicial
    st.session_state.datos_historico = pd.concat([st.session_state.datos_historico, nuevo], ignore_index=True)
    st.session_state.datos_dashboard = pd.concat([st.session_state.datos_dashboard, nuevo], ignore_index=True)
    st.sidebar.success("✅ Registro guardado")

# ==========================================
# MAIN APP
# ==========================================
st.title("🛡️ Panel de Auditoría BI")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Analítico", "📁 Base de Datos (Editable)", "📑 Informe Ejecutivo"])

# ==========================================
# PESTAÑA 1: DASHBOARD ANALÍTICO
# ==========================================
with tab1:
    st.subheader("Filtros Avanzados 📌")
    
    # 7. FILTROS POR FECHA Y AVANZADOS
    f_col1, f_col2, f_col3 = st.columns(3)
    filtro_fecha = f_col1.selectbox("📅 Periodo", ["Historico Total", "Hoy", "Últimos 7 días", "Este Mes"])
    filtro_region = f_col2.selectbox("📍 Filtrar Región", ["Todas"] + list(st.session_state.datos_dashboard['Region'].unique()))
    filtro_canal = f_col3.selectbox("🔄 Filtrar Canal", ["Todos"] + list(st.session_state.datos_dashboard['Canal'].unique()))

    # Aplicar filtros al DataFrame del Dashboard
    df_dash = st.session_state.datos_dashboard.copy()
    
    # Lógica de Fechas
    if not df_dash.empty:
        df_dash['Fecha'] = pd.to_datetime(df_dash['Fecha']).dt.date
        hoy = date.today()
        if filtro_fecha == "Hoy":
            df_dash = df_dash[df_dash['Fecha'] == hoy]
        elif filtro_fecha == "Últimos 7 días":
            df_dash = df_dash[df_dash['Fecha'] >= (hoy - timedelta(days=7))]
        elif filtro_fecha == "Este Mes":
            df_dash = df_dash[df_dash['Fecha'].apply(lambda x: x.month == hoy.month and x.year == hoy.year)]

    if filtro_region != "Todas":
        df_dash = df_dash[df_dash['Region'] == filtro_region]
    if filtro_canal != "Todos":
        df_dash = df_dash[df_dash['Canal'] == filtro_canal]

    # BOTÓN INTELIGENTE (Solo afecta Dashboard)
    if st.button("🗑️ Eliminar último registro del Dashboard"):
        if not st.session_state.datos_dashboard.empty:
            st.session_state.datos_dashboard = st.session_state.datos_dashboard.iloc[:-1]
            st.rerun()

    st.markdown("---")

    if df_dash.empty:
        st.warning("No hay datos para los filtros seleccionados.")
    else:
        # 5. INDICADOR VISUAL DE DESEMPEÑO
        sat_promedio = df_dash['Satisfaccion'].mean()
        if sat_promedio > 80:
            color_sat = "🟢 Excelente"
        elif sat_promedio >= 60:
            color_sat = "🟡 Regular"
        else:
            color_sat = "🔴 Crítico"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Registros Visibles", len(df_dash))
        c2.metric("Satisfacción", f"{sat_promedio:.1f}%", color_sat)
        c3.metric("Total PQRS", int(df_dash['Reclamos'].sum()))
        c4.metric("Canal Principal", df_dash['Canal'].mode()[0] if not df_dash.empty else "N/A")

        st.markdown("---")
        
        # 4. DOBLE GRÁFICA COMPARATIVA (PRO)
        st.subheader("📈 Comparativa: Selección vs Nacional")
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown(f"**Datos Filtrados (Región: {filtro_region})**")
            st.line_chart(df_dash.groupby('Fecha')['Satisfaccion'].mean())
            
        with g2:
            st.markdown("**Datos Nacionales (Sin Filtro)**")
            st.line_chart(st.session_state.datos_historico.groupby('Fecha')['Satisfaccion'].mean())

# ==========================================
# PESTAÑA 2: HISTÓRICO Y EDICIÓN
# ==========================================
with tab2:
    st.subheader("Gestión de Base de Datos")
    st.info("💡 Haz doble clic en cualquier celda para editarla. Selecciona una fila a la izquierda para borrarla.")
    
    if rol_usuario in ["Auditor", "Gerencia"]:
        # 9. EDICIÓN DE REGISTROS Y BORRADO SELECCIONADO
        st.session_state.datos_historico = st.data_editor(
            st.session_state.datos_historico, 
            num_rows="dynamic", # Permite añadir o borrar filas seleccionadas
            use_container_width=True,
            key="editor_hist"
        )
    else:
        st.warning("Tu rol de Supervisor solo permite visualizar el histórico.")
        st.dataframe(st.session_state.datos_historico, use_container_width=True)

# ==========================================
# PESTAÑA 3: INFORME DESCARGABLE
# ==========================================
with tab3:
    st.subheader("📄 Generador de Informes Ejecutivos")
    
    if st.session_state.datos_historico.empty:
        st.info("Sin datos para generar informe.")
    else:
        df_p = st.session_state.datos_historico[st.session_state.datos_historico['Motivo PQRS'] != "Ninguna (0 PQRS)"]
        
        if not df_p.empty:
            top_motivo = df_p['Motivo PQRS'].mode()[0]
            causa_raiz = "Falla sistémica en el proceso" if len(df_p) > 5 else "Falla puntual u operativa"
            solucion = SOLUCIONES_ISO.get(top_motivo, "Revisión técnica.")
            
            informe_texto = f"""
            INFORME DE AUDITORÍA TECNOQUÍMICAS
            -----------------------------------
            Fecha de generación: {date.today()}
            Registros evaluados: {len(st.session_state.datos_historico)}
            
            📌 HALLAZGO PRINCIPAL:
            El principal motivo de PQRS es: {top_motivo} con un total de {len(df_p[df_p['Motivo PQRS'] == top_motivo])} incidencias.
            
            🔍 CAUSA RAÍZ SUGERIDA:
            {causa_raiz} relacionada con la categoría de {top_motivo.split('. ')[1] if '. ' in top_motivo else top_motivo}.
            
            ✅ SOLUCIÓN PROPUESTA (Basado en ISO 9001):
            {solucion}
            """
            
            st.code(informe_texto, language="markdown")
            
            # 8. INFORME DESCARGABLE
            st.download_button(
                label="📥 Descargar Informe Completo (.txt)",
                data=informe_texto,
                file_name=f"Informe_Auditoria_{date.today()}.txt",
                mime="text/plain"
            )
        else:
            st.success("No hay PQRS registradas. Operación al 100%.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>© 2026 Auditoría TQ - Nivel Empresarial</p>", unsafe_allow_html=True)
