import streamlit as st
import pandas as pd              
import sqlite3 
import numpy as np 
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# ==========================================
# 0. ESTILOS VISUALES
# ==========================================
st.set_page_config(page_title="TQ BI v11.2 Titanium", layout="wide")

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
        background-color: #eef2f7;
        padding: 15px;
        border-left: 5px solid #004aad;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. SEGURIDAD BLINDADA
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🛡️ TQ Enterprise Access Control")
        user = st.text_input("Usuario Corporativo", key="username_input")
        password = st.text_input("Contraseña", type="password", key="password_input")
        if st.button("Ingresar"):
            usuarios_db = {
                "admin": {"pass": "tq2026", "role": "Administrador"},
                "jhon.marin": {"pass": "auditoria2026", "role": "Auditor Senior"}
            }
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
# 2. MOTOR SQL SEGURO
# ==========================================
DB_SQL = "tq_audit_v11_fixed.db"

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
# 3. SIDEBAR
# ==========================================
st.sidebar.title("🏢 Tecnoquímicas S.A.")
st.sidebar.write(f"👤 {st.session_state.usuario_actual} | {st.session_state.user_role}")

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

with st.sidebar.form("form_v11", clear_on_submit=True):
    st.subheader("📝 Nuevo Registro")
    f_nombre = st.text_input("Nombre Consumidor")
    f_contacto = st.text_input("Contacto")
    f_ciudad = st.selectbox("Ciudad", ["Cali", "Bogotá", "Medellín", "Barranquilla", "Pereira"])
    f_region = st.selectbox("Región", ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Eje Cafetero"])
    f_canal = st.selectbox("Canal", ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa"])
    f_sat = st.slider("Satisfacción (%)", 0, 100, 85)
    f_pqrs = st.number_input("PQRS", 0, 100, 0)
    f_motivo = st.selectbox("Falla ISO", ["Ninguna", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención"])
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
# 4. DASHBOARD (KPIs + PLOTLY)
# ==========================================
st.title("📊 TQ Intelligence Master Suite")
db = cargar_datos_sql()

if db.empty:
    st.info("👋 Bienvenido. Ingrese el primer registro para activar el Dashboard.")
else:
    # FILTROS
    c_f1, c_f2 = st.columns(2)
    with c_f1: f_reg = st.multiselect("📍 Región", db['Region'].unique(), default=db['Region'].unique())
    with c_f2: f_can = st.multiselect("🔄 Canal", db['Canal'].unique(), default=db['Canal'].unique())

    df_f = db[(db['Region'].isin(f_reg)) & (db['Canal'].isin(f_can))]

    if not df_f.empty:
        k1, k2, k3, k4 = st.columns(4)
        prom = len(df_f[df_f['Satisfaccion'] >= 90])
        detr = len(df_f[df_f['Satisfaccion'] < 70])
        nps = ((prom - detr) / len(df_f)) * 100
        
        with k1:
            color = "#28a745" if nps > 30 else "#ffc107" if nps > 0 else "#dc3545"
            st.markdown(f"<div class='kpi-card' style='border-top: 5px solid {color}'><p class='kpi-label'>Net Promoter Score</p><p class='kpi-value' style='color:{color}'>{nps:.1f}</p></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>Satisfacción Avg</p><p class='kpi-value'>{df_f['Satisfaccion'].mean():.1f}%</p></div>", unsafe_allow_html=True)
        with k3:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>Total PQRS</p><p class='kpi-value'>{int(df_f['Reclamos'].sum())}</p></div>", unsafe_allow_html=True)
        with k4:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>Tasa de Falla</p><p class='kpi-value'>{(df_f['Reclamos'].sum()/len(df_f)):.2f}</p></div>", unsafe_allow_html=True)

        g1, g2 = st.columns(2)
        with g1:
            fig_bar = px.bar(df_f.groupby('Region')['Satisfaccion'].mean().reset_index(), 
                             x='Region', y='Satisfaccion', color='Satisfaccion', title="Desempeño Regional",
                             color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_bar, use_container_width=True)
        with g2:
            fig_scat = px.scatter(df_f, x='Satisfaccion', y='Reclamos', color='Region', size='Reclamos',
                                  title="Matriz de Riesgo: Reclamos vs Satisfacción")
            st.plotly_chart(fig_scat, use_container_width=True)

# ==========================================
# 5. GESTIÓN CRUD Y REPORTE ISO (MEJORADO)
# ==========================================
st.markdown("---")
tab1, tab2 = st.tabs(["🛠️ Gestión de Datos", "📑 Reporte de Hallazgos ISO 9001"])

with tab1:
    st.subheader("Editor Maestro (CRUD)")
    if not db.empty:
        csv = df_f.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte Filtrado (CSV)", csv, "tq_report.csv", "text/csv")
        edited = st.data_editor(db, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Guardar Cambios en SQL"):
            conn = sqlite3.connect(DB_SQL)
            edited.to_sql('auditoria', conn, if_exists='replace', index=False)
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.success("Cambios sincronizados.")
            st.rerun()
        
        id_del = st.number_input("ID a eliminar", min_value=1, step=1)
        if st.button("🗑️ Eliminar Definitivamente"):
            if st.session_state.user_role == "Administrador":
                conn = sqlite3.connect(DB_SQL)
                conn.execute("DELETE FROM auditoria WHERE id = ?", (id_del,))
                conn.commit()
                conn.close()
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Permiso denegado.")

with tab2:
    st.subheader("📋 Dictamen de Auditoría y Mejora Continua")
    
    if db.empty:
        st.write("No hay datos para generar el dictamen.")
    else:
        # 1. Análisis de No Conformidades (Problemas)
        hallazgos = db[db['Motivo_PQRS'] != "Ninguna"]
        
        if hallazgos.empty:
            st.success("✅ **Dictamen:** No se detectan no conformidades en el ciclo actual.")
        else:
            # Diccionario de soluciones ISO
            SOLUCIONES_ISO = {
                "1. Calidad": {"ref": "Numeral 8.7", "desc": "Control de salidas no conformes.", "accion": "Revisar cadena de frío y empaques en la ciudad afectada."},
                "2. Precios": {"ref": "Numeral 8.2.1", "desc": "Comunicación con el cliente.", "accion": "Auditoría de precios en PDV y ajuste de margen comercial."},
                "3. Logística": {"ref": "Numeral 8.4", "desc": "Control de procesos externos.", "accion": "Evaluación de desempeño del transportador (OTIF)."},
                "4. Agotados": {"ref": "Numeral 8.1", "desc": "Planificación operativa.", "accion": "Revisar stock de seguridad y frecuencias de reabastecimiento."},
                "5. Atención": {"ref": "Numeral 7.2", "desc": "Competencia del personal.", "accion": "Capacitación obligatoria en protocolo de servicio TQ."}
            }

            st.write(f"Se detectaron **{len(hallazgos)}** hallazgos críticos:")
            
            # Resumen dinámico por tipo de problema
            resumen_fallas = hallazgos['Motivo_PQRS'].value_counts()
            
            for falla, cant in resumen_fallas.items():
                info = SOLUCIONES_ISO.get(falla, {"ref": "Numeral 10.2", "desc": "No conformidad.", "accion": "Análisis de causa raíz."})
                
                st.markdown(f"""
                <div class="iso-box">
                    <h4 style="margin:0; color:#c0392b;">🔴 PROBLEMA: {falla.upper()} ({cant} casos)</h4>
                    <p style="margin:5px 0;"><b>Referencia ISO 9001:</b> {info['ref']} - {info['desc']}</p>
                    <p style="margin:5px 0; color:#2c3e50;"><b>✅ PLAN CORRECTIVO:</b> {info['accion']}</p>
                </div>
                """, unsafe_allow_html=True)

            # Recomendación General
            st.info("**Nota del Auditor:** Se recomienda iniciar el ciclo PHVA (Planear, Hacer, Verificar, Actuar) para mitigar la recurrencia en estos numerales.")

st.caption(f"TQ Titanium v11.2 | ISO Audit Expert | {date.today()}")
