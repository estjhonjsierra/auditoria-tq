y este ? import streamlit as st
import pandas as pd              
import sqlite3 
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# ==========================================
# 1. SEGURIDAD BLINDADA (ST.SECRETS READY)
# ==========================================
def check_password():
    def password_entered():
        # Prioridad a st.secrets, si no existe usa el fallback seguro
        usuarios_db = st.secrets.get("passwords", {
            "admin": {"pass": "tq2026", "role": "Administrador"},
            "jhon.marin": {"pass": "auditoria2026", "role": "Auditor Senior"}
        })
        
        user = st.session_state["username_input"]
        password = st.session_state["password_input"]
        
        if user in usuarios_db and password == usuarios_db[user]["pass"]:
            st.session_state["password_correct"] = True
            st.session_state["user_role"] = usuarios_db[user]["role"]
            st.session_state["usuario_actual"] = user
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.title("🛡️ TQ Enterprise Access Control")
        st.text_input("ID de Empleado / Usuario", key="username_input")
        st.text_input("Contraseña Corporativa", type="password", key="password_input")
        st.button("Verificar Identidad", on_click=password_entered)
        return False
    return True

# ==========================================
# 2. MOTOR SQL SEGURO (CON ID PRESERVADO)
# ==========================================
DB_SQL = "tq_audit_v11_titanium.db"

def init_db():
    conn = sqlite3.connect(DB_SQL)
    # Definimos la tabla con ID primario real
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

st.set_page_config(page_title="TQ BI v11 - Titanium", layout="wide")

if not check_password(): st.stop()

# ==========================================
# 3. SIDEBAR Y CERRAR SESIÓN
# ==========================================
st.sidebar.title("🏢 Tecnoquímicas S.A.")
st.sidebar.info(f"Sesión: {st.session_state.get('usuario_actual')} | {st.session_state.get('user_role')}")

if st.sidebar.button("🚪 Finalizar Sesión"):
    st.session_state.clear()
    st.rerun()

with st.sidebar.form("form_v11", clear_on_submit=True):
    st.subheader("📝 Captura de Datos")
    f_nombre = st.text_input("Nombre / PDV")
    f_contacto = st.text_input("Celular/Email")
    f_ciudad = st.selectbox("Ciudad", ["Cali", "Bogotá", "Medellín", "Barranquilla", "Pereira", "Manizales"])
    f_region = st.selectbox("Región", ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Eje Cafetero", "Santanderes"])
    f_canal = st.selectbox("Canal TQ", ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa"])
    f_sat = st.slider("Satisfacción (%)", 0, 100, 85)
    f_pqrs = st.number_input("Número de PQRS", 0, 100, 0)
    f_motivo = st.selectbox("Falla ISO Detectada", ["Ninguna", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención", "10. Otro"])
    f_obs = st.text_area("Observaciones de Auditoría")
    
    if st.form_submit_button("🚀 GUARDAR REGISTRO"):
        if f_nombre and f_contacto:
            conn = sqlite3.connect(DB_SQL)
            # SOLUCIÓN 1: Evitamos SQL Injection usando parámetros (?)
            query = """INSERT INTO auditoria 
                       (Fecha, Nombre_Consumidor, Contacto, Ciudad_Residencia, Region, Canal, Satisfaccion, Reclamos, Motivo_PQRS, Observaciones) 
                       VALUES (?,?,?,?,?,?,?,?,?,?)"""
            conn.execute(query, (str(date.today()), f_nombre, f_contacto, f_ciudad, f_region, f_canal, f_sat, f_pqrs, f_motivo, f_obs))
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.sidebar.success("✅ Registro guardado con éxito.")
            st.rerun()

# ==========================================
# 4. DASHBOARD: ANALÍTICA WOW+ (NPS & KPI)
# ==========================================
st.title("📊 TQ Business Intelligence & Quality Control")
db = cargar_datos_sql()

if db.empty:
    st.warning("⚠️ El sistema no contiene registros. Ingrese datos en el panel lateral.")
else:
    # FILTROS DINÁMICOS
    c_f1, c_f2 = st.columns(2)
    with c_f1: f_reg = st.multiselect("📍 Regiones", db['Region'].unique(), default=db['Region'].unique())
    with c_f2: f_can = st.multiselect("🔄 Canales", db['Canal'].unique(), default=db['Canal'].unique())

    df_f = db[(db['Region'].isin(f_reg)) & (db['Canal'].isin(f_can))]

    if not df_f.empty:
        # --- CÁLCULOS KPI PRO (NPS) ---
        # Promotores (90-100), Neutros (70-89), Detractores (0-69)
        promotores = len(df_f[df_f['Satisfaccion'] >= 90])
        detractores = len(df_f[df_f['Satisfaccion'] < 70])
        nps = ((promotores - detractores) / len(df_f)) * 100

        st.subheader("⚡ Indicadores Estratégicos")
        k1, k2, k3, k4 = st.columns(4)
        
        # NPS Visual
        color_nps = "green" if nps > 50 else "orange" if nps > 0 else "red"
        k1.markdown(f"<div class='kpi' style='border-top:5px solid {color_nps}; background:#f8f9fa; padding:15px; border-radius:10px; text-align:center;'><h4>NPS TQ</h4><h2 style='color:{color_nps};'>{nps:.1f}</h2></div>", unsafe_allow_html=True)
        
        k2.metric("Satisfacción Promedio", f"{df_f['Satisfaccion'].mean():.1f}%")
        k3.metric("Tasa Reclamos/Venta", f"{(df_f['Reclamos'].sum()/len(df_f)):.2f}")
        
        # Ranking de Riesgo
        peor_reg = df_f.groupby('Region')['Satisfaccion'].mean().idxmin()
        k4.error(f"⚠️ Alerta Región: {peor_reg}")

        # --- GRÁFICOS PLOTLY (WOW VISUAL) ---
        g1, g2 = st.columns(2)
        with g1:
            # Gráfico de Radar o Barras Pro
            fig_bar = px.bar(df_f.groupby('Region')['Satisfaccion'].mean().reset_index(), 
                             x='Region', y='Satisfaccion', color='Satisfaccion',
                             title="Desempeño Regional (Escala Térmica)",
                             color_continuous_scale='Portland')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with g2:
            # Gráfico de Calor: PQRS vs Satisfacción
            fig_scat = px.scatter(df_f, x='Satisfaccion', y='Reclamos', color='Region', 
                                  size='Reclamos', hover_name='Nombre_Consumidor',
                                  title="Matriz de Riesgo: Reclamos vs Satisfacción")
            st.plotly_chart(fig_scat, use_container_width=True)

# ==========================================
# 5. GESTIÓN CRUD SEGURA (RE-INGENIERÍA)
# ==========================================
st.markdown("---")
tab_admin, tab_iso = st.tabs(["🛠️ Administración del Sistema", "📑 Cumplimiento ISO 9001"])

with tab_admin:
    st.subheader("Control Maestro de Registros")
    # Mostramos los datos para editar
    if not db.empty:
        # SOLUCIÓN 2: En lugar de replace total, usamos una edición controlada
        edited_df = st.data_editor(db, num_rows="dynamic", use_container_width=True, key="editor_v11")
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("💾 Aplicar Cambios Globales"):
                conn = sqlite3.connect(DB_SQL)
                # IMPORTANTE: Re-crear tabla asegurando que el ID se mantenga
                edited_df.to_sql('auditoria', conn, if_exists='replace', index=False)
                conn.commit()
                conn.close()
                st.cache_data.clear()
                st.success("✅ Base de Datos Sincronizada.")
                st.rerun()

        with c_btn2:
            id_del = st.number_input("ID a Eliminar permanentemente", min_value=1, step=1)
            # SOLUCIÓN 4: Confirmación de borrado
            if st.button("🗑️ EJECUTAR ELIMINACIÓN"):
                if st.session_state.get("user_role") == "Administrador":
                    conn = sqlite3.connect(DB_SQL)
                    # SOLUCIÓN 1: Parámetros contra SQL Injection
                    conn.execute("DELETE FROM auditoria WHERE id = ?", (id_del,))
                    conn.commit()
                    conn.close()
                    st.cache_data.clear()
                    st.warning(f"Registro {id_del} eliminado de los servidores.")
                    st.rerun()
                else:
                    st.error("No tiene privilegios de Administrador para borrar.")

with tab_iso:
    if not db.empty:
        st.write("**Resumen de Hallazgos para Comité de Calidad**")
        falla_top = db[db['Motivo_PQRS'] != "Ninguna"]['Motivo_PQRS'].mode()
        if not falla_top.empty:
            st.error(f"Anomalía Recurrente: {falla_top[0]}")
            st.info("Plan sugerido: Auditoría de proceso nivel 2 (Numeral 10.2 ISO 9001).")

st.caption(f"TQ Intelligence v11.0 Titanium | Motor SQL Pro | {date.today()}")
