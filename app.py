import streamlit as st
import pandas as pd              
import sqlite3 
import numpy as np
import plotly.express as px # Gráficos nivel Pro
import plotly.graph_objects as go
from datetime import date, timedelta
import io

# ==========================================
# 1. SEGURIDAD Y ROLES
# ==========================================
def check_password():
    def password_entered():
        usuarios_db = {
            "admin": {"pass": "tq2026", "role": "Administrador"},
            "jhon.marin": {"pass": "auditoria2026", "role": "Auditor Senior"}
        }
        user = st.session_state["username_input"]
        password = st.session_state["password_input"]
        if user in usuarios_db and password == usuarios_db[user]["pass"]:
            st.session_state["password_correct"] = True
            st.session_state["user_role"] = usuarios_db[user]["role"]
            st.session_state["usuario_actual"] = user
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.title("🔐 TQ Enterprise Suite")
        st.text_input("Usuario", key="username_input")
        st.text_input("Contraseña", type="password", key="password_input")
        st.button("Entrar", on_click=password_entered)
        return False
    return True

# ==========================================
# 2. MOTOR SQL CON ID ÚNICO (NIVEL EMPRESA)
# ==========================================
DB_SQL = "tq_audit_v10_final.db"

def init_db():
    conn = sqlite3.connect(DB_SQL)
    # AGREGAMOS ID AUTOINCREMENTAL (CLAVE PARA CRUD)
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

# ==========================================
# 3. INTERFAZ Y SIDEBAR
# ==========================================
st.set_page_config(page_title="TQ BI v10 - Ultimate", layout="wide")

if not check_password(): st.stop()

st.sidebar.title("🏢 Tecnoquímicas S.A.")
st.sidebar.write(f"👤 {st.session_state.get('usuario_actual')} | 🛡️ {st.session_state.get('user_role')}")

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

# --- FORMULARIO DE CARGA ---
with st.sidebar.form("form_v10", clear_on_submit=True):
    st.subheader("📝 Nuevo Registro")
    f_nombre = st.text_input("Nombre")
    f_contacto = st.text_input("Contacto")
    f_ciudad = st.selectbox("Ciudad", ["Cali", "Bogotá", "Medellín", "Barranquilla", "Pereira", "Bucaramanga"])
    f_region = st.selectbox("Región", ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Eje Cafetero"])
    f_canal = st.selectbox("Canal", ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa"])
    f_sat = st.slider("Satisfacción (%)", 0, 100, 85)
    f_pqrs = st.number_input("PQRS", 0, 100, 0)
    f_motivo = st.selectbox("Falla ISO", ["Ninguna", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención"])
    f_obs = st.text_area("Notas")
    
    if st.form_submit_button("🚀 REGISTRAR"):
        if f_nombre and f_contacto:
            conn = sqlite3.connect(DB_SQL)
            conn.execute("INSERT INTO auditoria (Fecha, Nombre_Consumidor, Contacto, Ciudad_Residencia, Region, Canal, Satisfaccion, Reclamos, Motivo_PQRS, Observaciones) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (str(date.today()), f_nombre, f_contacto, f_ciudad, f_region, f_canal, f_sat, f_pqrs, f_motivo, f_obs))
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.rerun()

# ==========================================
# 4. DASHBOARD PRO (PLOTLY + INSIGHTS)
# ==========================================
st.title("🛡️ TQ Intelligence Master Suite")
db = cargar_datos_sql()

if not db.empty:
    # FILTROS
    c_f1, c_f2 = st.columns(2)
    regiones = db['Region'].unique()
    with c_f1: f_reg = st.multiselect("📍 Filtrar Región", regiones, default=regiones)
    with c_f2: f_can = st.multiselect("🔄 Filtrar Canal", db['Canal'].unique(), default=db['Canal'].unique())

    df_f = db[(db['Region'].isin(f_reg)) & (db['Canal'].isin(f_can))]

    if not df_f.empty:
        # --- KPIs VISUALES CON PLOTLY ---
        st.subheader("🚀 Indicadores de Desempeño Crítico")
        k1, k2, k3, k4 = st.columns(4)
        
        avg_sat = df_f['Satisfaccion'].mean()
        # Color dinámico para Satisfacción
        color_sat = "green" if avg_sat >= 80 else "orange" if avg_sat >= 60 else "red"
        
        k1.markdown(f"<div style='text-align:center; padding:10px; border-radius:10px; background-color:#f0f2f6; border-top:5px solid {color_sat};'><h5>Satisfacción Avg</h5><h2 style='color:{color_sat};'>{avg_sat:.1f}%</h2></div>", unsafe_allow_html=True)
        k2.metric("Auditorías", len(df_f))
        k3.metric("Total PQRS", int(df_f['Reclamos'].sum()))
        
        # Insight de tendencia % (Wow 2.0)
        hace_7 = date.today() - timedelta(days=7)
        reciente = df_f[df_f['Fecha'] >= hace_7]['Satisfaccion'].mean()
        historico = df_f[df_f['Fecha'] < hace_7]['Satisfaccion'].mean()
        if not np.isnan(historico) and not np.isnan(reciente):
            delta_p = reciente - historico
            k4.metric("Crecimiento Semanal", f"{delta_p:+.1f}%", delta=f"{delta_p:.1f}%")

        # --- GRÁFICOS INTERACTIVOS PLOTLY ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.write("**🏆 Desempeño por Ciudad (Satisfacción)**")
            fig_bar = px.bar(df_f.groupby('Ciudad_Residencia')['Satisfaccion'].mean().reset_index(), 
                             x='Ciudad_Residencia', y='Satisfaccion', color='Satisfaccion',
                             color_continuous_scale='RdYlGn', range_color=[50, 100])
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            st.write("**📈 Evolución Temporal Detallada**")
            fig_line = px.area(df_f.groupby('Fecha')['Satisfaccion'].mean().reset_index(), 
                               x='Fecha', y='Satisfaccion', line_shape='spline')
            st.plotly_chart(fig_line, use_container_width=True)

        # --- EXPORTACIÓN FILTRADA (NUEVO) ---
        st.markdown("---")
        st.subheader("📥 Exportación Inteligente")
        csv_data = df_f.to_csv(index=False).encode('utf-8')
        st.download_button(f"Descargar Reporte ({len(df_f)} registros filtrados)", csv_data, "reporte_tq_filtrado.csv", "text/csv")

# ==========================================
# 5. CRUD COMPLETO (EDITAR / BORRAR INDIVIDUAL)
# ==========================================
st.markdown("---")
tab_edit, tab_iso = st.tabs(["⚙️ GESTIÓN DE DATOS (CRUD)", "📑 PLAN DE ACCIÓN"])

with tab_edit:
    st.subheader("Control Maestro de Registros (SQL Directo)")
    # Data Editor con ID Único
    edited_df = st.data_editor(db, num_rows="dynamic", use_container_width=True, key="data_editor_v10")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("💾 SINCRONIZAR CAMBIOS (EDITAR)"):
            conn = sqlite3.connect(DB_SQL)
            # Reescribir la tabla para aplicar cambios del editor
            edited_df.to_sql('auditoria', conn, if_exists='replace', index=False)
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.success("Base de Datos actualizada con éxito.")
            st.rerun()

    with col_c2:
        id_borrar = st.number_input("ID a eliminar", min_value=1, step=1)
        if st.button("🗑️ BORRAR REGISTRO POR ID"):
            if st.session_state.user_role == "Administrador":
                conn = sqlite3.connect(DB_SQL)
                conn.execute(f"DELETE FROM auditoria WHERE id = {id_borrar}")
                conn.commit()
                conn.close()
                st.cache_data.clear()
                st.warning(f"Registro ID {id_borrar} eliminado.")
                st.rerun()
            else:
                st.error("No tienes permisos para borrar.")

with tab_iso:
    # Insight de Concentración Pro
    if not db.empty:
        total_pq = db['Reclamos'].sum()
        if total_pq > 0:
            reg_top = db.groupby('Region')['Reclamos'].sum().idxmax()
            perc = (db.groupby('Region')['Reclamos'].sum().max() / total_pq) * 100
            st.error(f"🚩 **Hallazgo Crítico:** La región **{reg_top}** concentra el **{perc:.1f}%** de los reclamos totales.")

st.caption(f"Tecnoquímicas S.A. | Enterprise BI Suite v10.0 | Engine: SQLite3 & Plotly")
