import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página para que se vea como una App real
st.set_page_config(page_title="Innovación TQ - Canal Ventas", layout="wide")

st.title("🛡️ Plan de Mejora: Transformación Digital TQ")
st.markdown("---")

# Creamos dos columnas para el ANTES y el DESPUÉS
col_antes, col_despues = st.columns(2)

with col_antes:
    st.error("### EL ANTES: Proceso Manual")
    st.write("❌ Datos dispersos en WhatsApp y papel.")
    st.write("❌ Tabulación lenta (riesgo de error humano).")
    
    # Un gráfico "aburrido" que representa el caos
    data_caos = {'Estado': ['Perdido', 'Incompleto', 'Manual'], 'Cantidad': [40, 30, 30]}
    fig_caos = px.pie(data_caos, values='Cantidad', names='Estado', title="Estado de datos antes", color_discrete_sequence=['gray', 'black', 'silver'])
    st.plotly_chart(fig_caos, use_container_width=True)

with col_despues:
    st.success("### EL DESPUÉS: Automatización con Python")
    st.write("✅ Captura digital en tiempo real.")
    st.write("✅ Análisis automático (Cumplimiento ISO 9.1.2).")
    
    # Métricas brillantes de éxito
    st.metric(label="Precisión de los Datos", value="100%", delta="+70%")
    
    # Un gráfico moderno y colorido de satisfacción
    data_exito = {'Mes': ['Mar', 'Abr', 'May'], 'Satisfacción': [85, 90, 95]}
    fig_exito = px.bar(data_exito, x='Mes', y='Satisfacción', title="Reporte Gerencial Automático", color='Satisfacción', color_continuous_scale='Viridis')
    st.plotly_chart(fig_exito, use_container_width=True)

st.info("💡 Conclusión: Esta herramienta elimina la No Conformidad al asegurar la trazabilidad total.")streamlit run app_tq.py