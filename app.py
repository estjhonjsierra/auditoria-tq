import streamlit as st
import pandas as pd              
import os
from datetime import date, timedelta

# ==========================================
# 1. PERSISTENCIA DE DATOS (ARCHIVO FÍSICO)
# ==========================================
DB_FILE = "database_tq.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        return df
    else:
        # Semillas iniciales si el archivo no existe
        return pd.DataFrame(columns=['Fecha', 'Nombre Consumidor', 'Contacto', 'Ciudad Residencia', 'Region', 'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

# ==========================================
# 2. CONFIGURACIÓN Y ESTILO
# ==========================================
st.set_page_config(page_title="TQ Auditoría Enterprise", layout="wide")

if 'db' not in st.session_state:
    st.session_state.db = cargar_datos()

# Listas de Selección
CIUDADES_COL = ["Cali", "Bogotá", "Medellín", "Barranquilla", "Bucaramanga", "Pereira", "Manizales", "Pasto"]
REGIONES = ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Santanderes", "Eje Cafetero", "Pacífico"]
CANALES = ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa"]

# ==========================================
# 3. SIDEBAR (INGRESO CON UX MEJORADA)
# ==========================================
st.sidebar.title("🏢 Tecnoquímicas S.A.")
st.sidebar.subheader("Panel de Carga")

with st.sidebar.form("form_registro", clear_on_submit=True):
    nombre = st.text_input("Nombre Consumidor")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad Residencia", CIUDADES_COL)
    region = st.selectbox("Región", REGIONES)
    canal = st.selectbox("Canal de Atención", CANALES)
    sat = st.slider("Satisfacción (%)", 0, 100, 80)
    reclamos = st.number_input("Cantidad PQRS", 0, 50, 0)
    motivo = st.selectbox("Motivo PQRS", ["Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención", "10. Otro"])
    obs = st.text_area("Observaciones")
    
    btn_guardar = st.form_submit_button("🚀 REGISTRAR")

if btn_guardar:
    if nombre and contacto:
        nuevo = pd.DataFrame([[date.today(), nombre, contacto, ciudad, region, canal, sat, reclamos, motivo, obs]], 
                             columns=st.session_state.db.columns)
        st.session_state.db = pd.concat([st.session_state.db, nuevo], ignore_index=True)
        guardar_datos(st.session_state.db) # PERSISTENCIA REAL
        st.sidebar.success(f"✅ Guardado: {nombre} en {region}")
        st.balloons()
    else:
        st.sidebar.error("❌ Falta Nombre o Contacto")

# ==========================================
# 4. DASHBOARD (INTELIGENCIA BI)
# ==========================================
st.title("🛡️ Sistema TQ Intelligence - Dashboard Maestro")

if st.session_state.db.empty:
    st.info("No hay datos en el archivo CSV. Comience registrando en el panel lateral.")
else:
    # FILTROS
    c1, c2, c3 = st.columns(3)
    with c1:
        f_reg = st.multiselect("📍 Filtrar Región", REGIONES, default=REGIONES)
    with c2:
        f_can = st.multiselect("🔄 Filtrar Canal", CANALES, default=CANALES)
    with c3:
        f_tiempo = st.selectbox("📅 Tiempo", ["Todo", "Hoy", "Últimos 7 días"])

    # Lógica de Filtrado (CORREGIDA)
    df_f = st.session_state.db.copy()
    if f_reg: df_f = df_f[df_f['Region'].isin(f_reg)]
    if f_can: df_f = df_f[df_f['Canal'].isin(f_can)]
    
    # MÉTRICAS CON DELTA (INDICADOR DE TENDENCIA)
    avg_nacional = st.session_state.db['Satisfaccion'].mean()
    avg_filtrado = df_f['Satisfaccion'].mean() if not df_f.empty else 0
    
    m1, m2, m3, m4 = st.columns(4)
    # Delta comparado contra meta del 80%
    m1.metric("Satisfacción Actual", f"{avg_filtrado:.1f}%", delta=f"{avg_filtrado - 80:.1f}% vs Meta")
    m2.metric("Nivel Nacional", f"{avg_nacional:.1f}%")
    m3.metric("PQRS en Filtro", int(df_f['Reclamos'].sum()))
    
    status = "🔴 CRÍTICO" if avg_filtrado < 60 else "🟡 RIESGO" if avg_filtrado < 80 else "🟢 ÓPTIMO"
    m4.write(f"**Estado del Segmento:** \n # {status}")

    # --- GRÁFICA COMPARATIVA PRO (NACIONAL VS FILTRADO) ---
    st.markdown("### 📊 Comparativa de Satisfacción: Nacional vs Segmento Seleccionado")
    
    # Construcción de tabla comparativa
    comparativa = pd.DataFrame({
        'Nacional': [avg_nacional],
        'Segmento Filtrado': [avg_filtrado]
    }, index=['Promedio %'])
    
    st.bar_chart(comparativa.T) # .T transpone para ver las dos barras juntas

    # --- TENDENCIA TEMPORAL REAL ---
    st.markdown("### 📈 Evolución de Calidad en el Tiempo")
    df_tiempo = df_f.groupby('Fecha')['Satisfaccion'].mean().reset_index()
    st.area_chart(df_tiempo.set_index('Fecha'))

# ==========================================
# 5. GESTIÓN Y CONTROL
# ==========================================
st.markdown("---")
with st.expander("📁 Gestión de Base de Datos y Trazabilidad"):
    # Editor con Persistencia Sincronizada
    edited_db = st.data_editor(st.session_state.db, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Sincronizar y Guardar Cambios en CSV"):
        st.session_state.db = edited_db
        guardar_datos(edited_db)
        st.success("Archivo CSV actualizado correctamente.")

    if st.button("🚨 BORRAR TODA LA BASE DE DATOS"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.session_state.db = pd.DataFrame(columns=COLUMNAS)
            st.rerun()

st.caption("Tecnoquímicas S.A. | Auditoría BI v4.0 | Datos Persistentes en Disco")
