import streamlit as st
import pandas as pd
from datetime import date

# 1. Configuración de la página
st.set_page_config(page_title="App Auditoría TQ - Canal Ventas", layout="wide", initial_sidebar_state="expanded")

# 2. SISTEMA DE MEMORIA (Inicialización)
if 'datos_dashboard' not in st.session_state:
    st.session_state.datos_dashboard = pd.DataFrame(columns=[
        'Fecha', 'Nombre', 'Contacto', 'Region', 'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'
    ])

if 'datos_historico' not in st.session_state:
    st.session_state.datos_historico = pd.DataFrame(columns=[
        'Fecha', 'Nombre', 'Contacto', 'Region', 'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'
    ])

# Diccionario de soluciones ISO 9001 según el motivo
SOLUCIONES_ISO = {
    "1. Calidad": "Aplicar protocolo de Cuarentena (ISO 8.7). Realizar trazabilidad al lote de producción y ajustar controles en línea de empaque.",
    "2. Precios": "Auditoría de facturación (ISO 8.2). Sincronizar bases de datos de descuentos y actualizar lista de precios en el sistema ERP.",
    "3. Logística": "Revisión de la cadena de suministro (ISO 8.4). Optimizar rutas de última milla y verificar tiempos de carga en CEDI.",
    "4. Agotados": "Ajuste de pronósticos de demanda (ISO 8.1). Incrementar stock de seguridad y mejorar comunicación con planeación de demanda.",
    "5. Atención": "Plan de capacitación en servicio (ISO 7.2). Reforzar protocolos de comunicación asertiva y gestión de clientes críticos.",
    "6. Vencimientos": "Control de inventarios FEFO (ISO 8.5). Implementar alertas tempranas de rotación y planes de evacuación de producto próximo.",
    "7. Averías": "Evaluación de embalaje primario y secundario (ISO 8.5.4). Capacitar al personal logístico en manipulación de carga frágil.",
    "8. Cambios": "Simplificación del proceso de devoluciones (ISO 8.2.1). Establecer tiempos máximos de respuesta para notas crédito.",
    "9. Publicidad": "Revisión de requisitos de comunicación (ISO 8.2.1). Validar términos y condiciones antes de lanzar pautas comerciales.",
    "10. Otro": "Realizar análisis de causa raíz (Diagrama de Ishikawa) para identificar el factor humano o técnico no estandarizado."
}

# ==========================================
# BARRA LATERAL (INGRESO DE DATOS)
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #004aad;'>🏢 TECNOQUÍMICAS</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size: 14px; color: gray;'>Sistema de Gestión de Calidad</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.subheader("📝 Ingresar Nuevo Reclamo/PQRS")

with st.sidebar.form("formulario_encuesta_iso", clear_on_submit=True):
    nombre_cliente = st.text_input("Nombre del Cliente:")
    contacto_cliente = st.text_input("Celular/Correo:")
    
    region_colombia = st.selectbox("Región/Departamento:", [
        "Antioquia", "Atlantico", "Bogota D.C.", "Bolivar", "Boyaca", "Caldas",
        "Cauca", "Cesar", "Cundinamarca", "Huila", "La Guajira", "Magdalena",
        "Valle del Cauca", "Santander", "Norte de Santander", "Ninguno (No aplica)"
    ])
    
    canal_venta = st.selectbox("Canal de Contacto:", ["Fuerza de Ventas", "Mercadeo", "Digital/PQRS"])
    nivel_satisfaccion = st.slider("Satisfacción (0-100%):", 0, 100, 80)
    cantidad_reclamos = st.number_input("Cantidad de PQRS:", min_value=0, max_value=50, value=0)
    
    motivo_pqrs = st.selectbox("Motivo Principal de Reclamo:", [
        "Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística", 
        "4. Agotados", "5. Atención", "6. Vencimientos", "7. Averías", 
        "8. Cambios", "9. Publicidad", "10. Otro"
    ])
    
    feedback = st.text_area("Observaciones detalladas:")
    submit_button = st.form_submit_button(label="💾 Guardar Trazabilidad")

if submit_button:
    if motivo_pqrs == "10. Otro" and not feedback.strip():
        st.sidebar.error("❌ ERROR: Escriba el detalle en Observaciones.")
    else:
        nuevo = pd.DataFrame({
            'Fecha': [str(date.today())], 'Nombre': [nombre_cliente], 'Contacto': [contacto_cliente],
            'Region': [region_colombia], 'Canal': [canal_venta], 'Satisfaccion': [nivel_satisfaccion],
            'Reclamos': [cantidad_reclamos], 'Motivo PQRS': [motivo_pqrs], 'Observaciones': [feedback]
        })
        st.session_state.datos_dashboard = pd.concat([st.session_state.datos_dashboard, nuevo], ignore_index=True)
        st.session_state.datos_historico = pd.concat([st.session_state.datos_historico, nuevo], ignore_index=True)
        st.sidebar.success(f"✅ Registrado en sistema PQRS: {region_colombia}")

# ==========================================
# CUERPO PRINCIPAL
# ==========================================
st.title("🛡️ Sistema Integral de Auditoría: Canal Ventas TQ")
tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "🗄️ HISTÓRICO", "📑 INFORME ISO 9001"])

df_actual = st.session_state.datos_dashboard

with tab1:
    if df_actual.empty:
        st.warning("⚠️ Sin datos. Registre una encuesta en el panel izquierdo.")
    else:
        opciones_reg = ["Todas (Nacional)"] + list(df_actual['Region'].unique())
        filtro_region = st.selectbox("🔍 Selector Regional para Análisis:", opciones_reg)
        df_f = df_actual if filtro_region == "Todas (Nacional)" else df_actual[df_actual['Region'] == filtro_region]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("PQRS Digitalizadas", len(df_f))
        m2.metric("Satisfacción Promedio", f"{df_f['Satisfaccion'].mean():.1f}%")
        m3.metric("Total Reclamos", int(df_f['Reclamos'].sum()))

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**📈 Tendencia de Satisfacción ({filtro_region})**")
            st.line_chart(df_f.groupby('Fecha')['Satisfaccion'].mean())
        with c2:
            st.write("**⚠️ Motivos de Reclamo (PQRS)**")
            df_m = df_f[df_f['Motivo PQRS'] != "Ninguna (0 PQRS)"]
            if not df_m.empty:
                st.bar_chart(df_m['Motivo PQRS'].value_counts())
            else:
                st.success("🏆 Cero PQRS en esta zona")

with tab2:
    st.subheader("🗄️ Base de Datos Central - Trazabilidad")
    st.dataframe(st.session_state.datos_historico, use_container_width=True)
    
    col_del1, col_del2 = st.columns(2)
    with col_del1:
        if not st.session_state.datos_historico.empty:
            csv = st.session_state.datos_historico.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte CSV", data=csv, file_name='Historico_Auditoria_TQ.csv')
    
    with col_del2:
        if st.button("🗑️ ELIMINAR TODO EL HISTORIAL", type="secondary", help="Borra permanentemente los datos"):
            st.session_state.datos_historico = pd.DataFrame(columns=st.session_state.datos_historico.columns)
            st.session_state.datos_dashboard = pd.DataFrame(columns=st.session_state.datos_dashboard.columns)
            st.rerun()

with tab3:
    st.subheader("📑 Dictamen Automático y Mejora Continua")
    if not st.session_state.datos_historico.empty:
        st.success("**HALLAZGO:** Se cumple con el numeral 9.1.2 de la ISO 9001 al mantener evidencia digital.")
        
        df_p = st.session_state.datos_historico[st.session_state.datos_historico['Motivo PQRS'] != "Ninguna (0 PQRS)"]
        if not df_p.empty:
            top_motivo = df_p['Motivo PQRS'].mode()[0]
            st.error(f"**CAUSA RAÍZ PRINCIPAL:** {top_motivo}")
            
            # SOLUCIÓN VIABLE BASADA EN EL MOTIVO
            solucion = SOLUCIONES_ISO.get(top_motivo, "Realizar auditoría interna al proceso.")
            
            st.markdown("### 💡 Propuesta de Solución Técnica:")
            st.info(f"**Acción Sugerida:** {solucion}")
            
            st.markdown("---")
            st.markdown("**Nivel de Riesgo para la Marca:** 🔴 Alto" if df_p['Reclamos'].sum() > 5 else "🟡 Medio")
        else:
            st.success("**ESTADO:** Óptimo. No se identifican No Conformidades en los registros.")
    else:
        st.info("No hay datos para generar el dictamen técnico.")

st.markdown("<br><br><p style='text-align: center; color: gray;'>© 2026 Sistema de Auditoría Digital TQ</p>", unsafe_allow_html=True)
