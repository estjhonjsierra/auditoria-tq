import streamlit as st
import pandas as pd              
import sqlite3 
import numpy as np 
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# ==========================================
# 0. ESTILOS VISUALES Y CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="TQ BI v12.0 - Absolute Masterpiece", layout="wide")

st.markdown("""
    <style>
    .kpi-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .kpi-value {
        font-size: 32px;
        font-weight: bold;
        margin: 0;
    }
    .kpi-label {
        color: #6c757d;
        font-size: 14px;
        text-transform: uppercase;
    }
    .iso-box {
        background-color: #ffffff;
        padding: 20px;
        border-left: 5px solid #004aad;
        margin-bottom: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .ceo-insight {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. SEGURIDAD NIVEL EMPRESA (ST.SECRETS READY)
# ==========================================
def check_password():
    # DETALLE 1: Validación de estado de sesión profesional
    if not st.session_state.get("password_correct", False):
        st.title("🛡️ TQ Enterprise Access Control")
        user = st.text_input("Usuario Corporativo", key="username_input")
        password = st.text_input("Contraseña", type="password", key="password_input")
        
        if st.button("Ingresar"):
            # DETALLE 2: Integración con st.secrets para producción
            usuarios_db = st.secrets.get("users", {
                "admin": {"pass": "tq2026", "role": "Administrador"},
                "jhon.marin": {"pass": "auditoria2026", "role": "Auditor Senior"}
            })
            
            if user in usuarios_db and password == usuarios_db[user]["pass"]:
                st.session_state["password_correct"] = True
                st.session_state["user_role"] = usuarios_db[user]["role"]
                st.session_state["usuario_actual"] = user
                st.rerun()
            else:
                st.error("❌ Credenciales inválidas")
        return False
    return True

# ==========================================
# 2. MOTOR SQL SEGURO (CON ID PRESERVADO)
# ==========================================
DB_SQL = "tq_audit_final_v12.db"

def init_db():
    conn = sqlite3.connect(DB_SQL)
    conn.execute('''CREATE TABLE IF NOT EXISTS auditoria 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  Fecha TEXT, Nombre_Consumidor TEXT, Contacto TEXT, Ciudad_Residencia TEXT, 
                  Region TEXT, Canal TEXT, Satisfaccion REAL, Reclamos INTEGER, 
                  Motivo_PQRS TEXT, Observaciones TEXT)''')
    conn.commit()
    conn.close()

@st.cache_data(ttl=60)
def cargar_datos_sql():
    conn = sqlite3.connect(DB_SQL)
    df = pd.read_sql_query("SELECT * FROM auditoria", conn)
    conn.close()
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
    return df

init_db()

if not check_password():
    st.stop()

# ==========================================
# 3. DATOS DE COBERTURA NACIONAL
# ==========================================
CIUDADES_COL = sorted(["Cali", "Bogotá", "Medellín", "Barranquilla", "Cartagena", "Cúcuta", "Ibagué", "Bucaramanga", "Pereira", "Manizales", "Neiva", "Villavicencio", "Pasto", "Armenia", "Buenaventura", "Montería"])
REGIONES_COL = ["Región Andina", "Región Caribe", "Región Pacífica", "Región Orinoquía", "Región Amazonía"]

# ==========================================
# 4. SIDEBAR
# ==========================================
st.sidebar.title("🏢 Tecnoquímicas S.A.")
st.sidebar.write(f"👤 {st.session_state.get('usuario_actual')} | {st.session_state.get('user_role')}")

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

with st.sidebar.form("form_v12", clear_on_submit=True):
    st.subheader("📝 Registro Auditoría")
    f_nombre = st.text_input("Nombre Cliente")
    f_contacto = st.text_input("Contacto")
    f_ciudad = st.selectbox("Ciudad", CIUDADES_COL)
    f_region = st.selectbox("Región", REGIONES_COL)
    f_canal = st.selectbox("Canal", ["Ventas Directas", "Mercadeo", "Digital", "Farma", "Comunicación Directa"])
    f_sat = st.slider("Satisfacción (%)", 0, 100, 85)
    f_pqrs = st.number_input("PQRS", 0, 100, 0)
    f_motivo = st.selectbox("Falla ISO", ["Ninguna", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención", "10. Otro"])
    f_obs = st.text_area("Observaciones")
    
    if st.form_submit_button("🚀 GUARDAR"):
        if f_nombre and f_contacto:
            conn = sqlite3.connect(DB_SQL)
            query = "INSERT INTO auditoria (Fecha, Nombre_Consumidor, Contacto, Ciudad_Residencia, Region, Canal, Satisfaccion, Reclamos, Motivo_PQRS, Observaciones) VALUES (?,?,?,?,?,?,?,?,?,?)"
            conn.execute(query, (str(date.today()), f_nombre, f_contacto, f_ciudad, f_region, f_canal, f_sat, f_pqrs, f_motivo, f_obs))
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.rerun()

# ==========================================
# 5. DASHBOARD: ANALÍTICA Y RECOMENDACIÓN AUTO
# ==========================================
st.title("📊 TQ Business Intelligence Suite")
db = cargar_datos_sql()

if db.empty:
    st.info("👋 Ingrese el primer registro para activar el análisis ejecutivo.")
else:
    # FILTROS
    c_f1, c_f2 = st.columns(2)
    with c_f1: f_reg = st.multiselect("📍 Región", db['Region'].unique(), default=db['Region'].unique())
    with c_f2: f_can = st.multiselect("🔄 Canal", db['Canal'].unique(), default=db['Canal'].unique())
    
    df_f = db[(db['Region'].isin(f_reg)) & (db['Canal'].isin(f_can))]

    # DETALLE 4: RECOMENDACIÓN AUTOMÁTICA (NIVEL DIOS)
    if not df_f.empty:
        # Cálculo de NPS
        prom = len(df_f[df_f['Satisfaccion'] >= 90])
        detr = len(df_f[df_f['Satisfaccion'] < 70])
        nps = ((prom - detr) / len(df_f)) * 100 if len(df_f) > 0 else 0
        
        st.subheader("💡 Recomendación Estratégica Automática")
        if nps < 0:
            st.error("🚨 **CRÍTICO:** Se recomienda intervención URGENTE en la experiencia del cliente. El volumen de detractores supera a los promotores.")
        elif nps < 30:
            st.warning("⚠️ **ALERTA:** Se requiere plan de mejora en satisfacción. El nivel de lealtad está por debajo del estándar TQ.")
        else:
            st.success("✅ **ÓPTIMO:** La experiencia del cliente se encuentra en niveles de excelencia corporativa.")

        # KPIs Visuales
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            c = "#28a745" if nps > 30 else "#dc3545"
            st.markdown(f"<div class='kpi-card' style='border-top: 5px solid {c}'><p class='kpi-label'>Net Promoter Score</p><p class='kpi-value' style='color:{c}'>{nps:.1f}</p></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>Satisfacción Avg</p><p class='kpi-value'>{df_f['Satisfaccion'].mean():.1f}%</p></div>", unsafe_allow_html=True)
        with k3:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>Total PQRS</p><p class='kpi-value'>{int(df_f['Reclamos'].sum())}</p></div>", unsafe_allow_html=True)
        with k4:
            # DETALLE 3: Validación División por Cero
            tasa = (df_f['Reclamos'].sum()/len(df_f)) if len(df_f) > 0 else 0
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>Tasa de Falla</p><p class='kpi-value'>{tasa:.2f}</p></div>", unsafe_allow_html=True)

        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.bar(df_f.groupby('Region')['Satisfaccion'].mean().reset_index(), x='Region', y='Satisfaccion', color='Satisfaccion', title="Satisfacción por Región", color_continuous_scale='RdYlGn'), use_container_width=True)
        with g2:
            st.plotly_chart(px.scatter(df_f, x='Satisfaccion', y='Reclamos', color='Region', size='Reclamos', hover_name='Nombre_Consumidor', title="Matriz de Riesgo PQRS"), use_container_width=True)

# ==========================================
# 6. GESTIÓN Y REPORTE ISO (CRUD SEGURO)
# ==========================================
st.markdown("---")
tab1, tab2 = st.tabs(["🛠️ Gestión SQL Profesional", "📑 Reporte de Hallazgos ISO 9001"])

with tab1:
    st.subheader("Control Maestro de Registros")
    # DETALLE 1: Validación de existencia antes de exportar
    if 'df_f' in locals() and not df_f.empty:
        st.download_button("📥 Exportar Reporte Filtrado (CSV)", df_f.to_csv(index=False).encode('utf-8'), "tq_report_pro.csv", "text/csv")
        
        # DETALLE 3: Sincronización del Editor
        edited = st.data_editor(db, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Sincronizar Cambios Globales"):
            conn = sqlite3.connect(DB_SQL)
            # Recrea la tabla con los datos del editor
            edited.to_sql('auditoria', conn, if_exists='replace', index=False)
            conn.commit(); conn.close()
            st.cache_data.clear(); st.success("Base de Datos Actualizada"); st.rerun()
        
        # Borrado por ID con parámetros seguros
        id_del = st.number_input("Eliminar por ID Único", min_value=1, step=1)
        if st.button("🗑️ Eliminar Definitivamente"):
            if st.session_state.get("user_role") == "Administrador":
                conn = sqlite3.connect(DB_SQL)
                conn.execute("DELETE FROM auditoria WHERE id = ?", (id_del,))
                conn.commit(); conn.close()
                st.cache_data.clear(); st.rerun()
            else:
                st.error("No tiene permisos de Administrador.")

with tab2:
    st.subheader("📋 Auditoría y Plan de Acción ISO")
    if not db.empty:
        hallazgos = db[db['Motivo_PQRS'] != "Ninguna"]
        MATRIZ = {
            "1. Calidad": ("Numeral 8.7", "Control de productos no conformes.", "Plan: Auditoría de lotes inmediata."),
            "2. Precios": ("Numeral 8.2.1", "Comunicación comercial.", "Plan: Estandarización de precios PDV."),
            "3. Logística": ("Numeral 8.4", "Evaluación de proveedores externos.", "Plan: Auditoría al operador logístico."),
            "4. Agotados": ("Numeral 8.1", "Planificación operativa.", "Plan: Ajuste de stock de seguridad."),
            "5. Atención": ("Numeral 7.2", "Competencia y capacitación.", "Plan: Re-entrenamiento en protocolos TQ.")
        }
        for falla in hallazgos['Motivo_PQRS'].unique():
            info = MATRIZ.get(falla, ("ISO", "Impacto General", "Acción Correctiva"))
            st.markdown(f"""
            <div class="iso-box">
                <h4 style="margin:0; color:#c0392b;">🔴 FALLA: {falla}</h4>
                <b>Referencia:</b> {info[0]} | {info[1]}<br>
                <div style="color:#27ae60; font-weight:bold; margin-top:10px;">✅ {info[2]}</div>
            </div>
            """, unsafe_allow_html=True)

st.caption(f"Tecnoquímicas S.A. | Absolute Masterpiece v12.0 | Engine: SQLite & Plotly | {date.today()}")
