import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.express as px
import hashlib
from datetime import date
from fpdf import FPDF 

# ==========================================
# 1. SEGURIDAD Y ESTILO EMPRESARIAL
# ==========================================
st.set_page_config(page_title="TQ BI Enterprise v17.0", layout="wide", page_icon="💊")

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def check_password():
    if not st.session_state.get("password_correct", False):
        st.title("🔐 TECNOQUIMICAS S.A. - Control de Acceso")
        col1, _ = st.columns([1, 1])
        with col1:
            user = st.text_input("ID Auditor")
            password = st.text_input("Clave Corporativa", type="password")
            if st.button("Autenticar"):
                usuarios = {
                    "admin": {"pass": hash_pass("tq2026"), "role": "Administrador"},
                    "jhonmarin": {"pass": hash_pass("Jhonmarin31."), "role": "Auditor Senior"}
                }
                if user in usuarios and hash_pass(password) == usuarios[user]["pass"]:
                    st.session_state.update({"password_correct": True, "usuario": user, "rol": usuarios[user]["role"]})
                    st.rerun()
                else: st.error("Acceso Denegado")
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. GESTIÓN DE DATOS Y GEOLOCALIZACIÓN
# ==========================================
DB = "tq_pro_v17.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT, Fecha TEXT, Nombre TEXT, 
        Ciudad TEXT, Region TEXT, Canal TEXT, Satisfaccion REAL, 
        Reclamos INTEGER, Motivo TEXT, Observaciones TEXT, Lat REAL, Lon REAL
    )""")
    conn.commit(); conn.close()

# Diccionario de coordenadas para el Mapa
COORDENADAS = {
    "Bogotá": (4.711, -74.072), "Medellín": (6.244, -75.581), "Cali": (3.451, -76.532),
    "Barranquilla": (10.963, -74.796), "Cartagena": (10.391, -75.479), "Cúcuta": (7.893, -72.507),
    "Bucaramanga": (7.119, -73.122), "Pereira": (4.813, -75.694), "Ibagué": (4.438, -75.232),
    "Santa Marta": (11.240, -74.199), "Pasto": (1.213, -77.281), "Manizales": (5.068, -75.517),
    "Neiva": (2.927, -75.281), "Villavicencio": (4.142, -73.626), "Armenia": (4.533, -75.681),
    "Valledupar": (10.463, -73.253), "Montería": (8.747, -75.881), "Sincelejo": (9.304, -75.397),
    "Popayán": (2.441, -76.606), "Tunja": (5.535, -73.367), "Riohacha": (11.544, -72.906),
    "Quibdó": (5.691, -76.658), "Florencia": (1.614, -75.606), "Yopal": (5.337, -72.395),
    "Arauca": (7.084, -70.759), "Mocoa": (1.147, -76.646), "San José del Guaviare": (2.565, -72.641),
    "Leticia": (-4.215, -69.940), "Inírida": (3.865, -67.923), "Puerto Carreño": (6.189, -67.485),
    "Mitú": (1.198, -70.173), "San Andrés": (12.584, -81.700)
}

init_db()

@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect(DB); df = pd.read_sql("SELECT * FROM auditoria", conn); conn.close()
    if not df.empty: df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
    return df

# ==========================================
# 3. PDF Y REPORTING
# ==========================================
def generar_pdf_pro(df_filtrado, nps, avg_sat, usuario):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "TECNOQUIMICAS S.A. - INFORME ESTRATEGICO DE AUDITORIA", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Auditor: {usuario} | Generado: {date.today()}", ln=True, align="C")
    pdf.ln(10)
    
    # KPIs
    pdf.set_fill_color(0, 51, 153); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 12); pdf.cell(190, 10, " 1. INDICADORES DE DESEMPEÑO (KPI)", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 11)
    pdf.cell(95, 10, f"NPS: {nps:.1f}"); pdf.cell(95, 10, f"Satisfacción: {avg_sat:.1f}%", ln=True)
    
    # Hallazgos
    pdf.ln(5); pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, " 2. NO CONFORMIDADES ISO 9001", ln=True, fill=True)
    pdf.set_font("Arial", "", 9)
    if not df_filtrado.empty:
        for _, r in df_filtrado[df_filtrado['Motivo'] != 'Ninguna'].iterrows():
            pdf.multi_cell(0, 7, f"ID {r['id']} | {r['Ciudad']} | Falla: {r['Motivo']} | Obs: {str(r['Observaciones'])}")
            pdf.ln(1)
    return pdf.output(dest="S").encode("latin-1")

# ==========================================
# 4. SIDEBAR - CAPTURA TÉCNICA
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5a/Logo_Tecnoqu%C3%ADmicas.png", width=150)
st.sidebar.markdown(f"**Auditor:** {st.session_state.usuario} \n **Rol:** {st.session_state.rol}")

with st.sidebar.form("form_tq"):
    st.subheader("📝 Registro de Hallazgo")
    f_nombre = st.text_input("Punto de Venta / Cliente")
    f_ciudad = st.selectbox("Ciudad", sorted(COORDENADAS.keys()))
    f_canal = st.selectbox("Canal", ["Farma", "Institucional", "Ventas", "Digital"])
    f_sat = st.slider("Satisfacción (%)", 0, 100, 85)
    f_pqrs = st.number_input("Número de Reclamos", 0, 20, 0)
    f_motivo = st.selectbox("Motivo Falla", ["Ninguna", "Calidad", "Precios", "Logística", "Agotados", "Atención"])
    f_obs = st.text_area("Observaciones de Auditoría")
    
    if st.form_submit_button("💾 GUARDAR REGISTRO"):
        lat, lon = COORDENADAS[f_ciudad]
        regiones = {"Andina": ["Bogotá", "Medellín", "Cali", "Pereira", "Ibagué", "Manizales", "Neiva", "Armenia", "Popayán", "Tunja", "Bucaramanga", "Cúcuta"], "Caribe": ["Barranquilla", "Cartagena", "Santa Marta", "Valledupar", "Montería", "Sincelejo", "Riohacha"], "Pacífica": ["Quibdó"], "Amazonía": ["Leticia", "Florencia", "Mocoa", "San José del Guaviare", "Inírida", "Mitú"], "Orinoquía": ["Villavicencio", "Yopal", "Arauca", "Puerto Carreño"], "Insular": ["San Andrés"]}
        f_region = next((r for r, cities in regiones.items() if f_ciudad in cities), "Andina")
        
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO auditoria (Fecha,Nombre,Ciudad,Region,Canal,Satisfaccion,Reclamos,Motivo,Observaciones,Lat,Lon) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     (str(date.today()), f_nombre, f_ciudad, f_region, f_canal, f_sat, f_pqrs, f_motivo, f_obs, lat, lon))
        conn.commit(); conn.close(); st.cache_data.clear(); st.rerun()

if st.sidebar.button("🚪 Cerrar Sesión Segura"):
    st.session_state.clear(); st.rerun()

# ==========================================
# 5. DASHBOARD ELITE (MAPA + SEMÁFOROS)
# ==========================================
st.title("📊 Dashboard de Inteligencia de Calidad TQ")
df = load_data()

if df.empty:
    st.info("Esperando registros iniciales para activar analítica...")
else:
    # Filtros Pro
    c1, c2, c3 = st.columns(3)
    reg_sel = c1.multiselect("Regiones", df["Region"].unique(), default=df["Region"].unique())
    can_sel = c2.multiselect("Canales", df["Canal"].unique(), default=df["Canal"].unique())
    df_f = df[(df["Region"].isin(reg_sel)) & (df["Canal"].isin(can_sel))]
    
    # 🚥 SEMÁFOROS DE RIESGO
    nps = ((len(df_f[df_f["Satisfaccion"]>=90]) - len(df_f[df_f["Satisfaccion"]<70])) / len(df_f)) * 100 if len(df_f)>0 else 0
    avg_sat = df_f["Satisfaccion"].mean()
    
    k1, k2, k3, k4 = st.columns(4)
    # Lógica de colores de semáforo
    nps_color = "normal" if nps > 50 else "inverse"
    k1.metric("NPS Corporativo", f"{nps:.1f}", delta="OBJETIVO > 50", delta_color=nps_color)
    k2.metric("Satisfacción Promedio", f"{avg_sat:.1f}%")
    k3.metric("PQRS Totales", int(df_f["Reclamos"].sum()))
    k4.metric("Casos Analizados", len(df_f))
    
    # 🗺️ MAPA DE CALIDAD COLOMBIA
    st.subheader("📍 Georreferenciación de Calidad Nacional")
    fig_map = px.scatter_mapbox(df_f, lat="Lat", lon="Lon", color="Satisfaccion", size="Reclamos",
                                hover_name="Ciudad", hover_data=["Nombre", "Motivo"],
                                color_continuous_scale="RdYlGn", size_max=15, zoom=4.5,
                                mapbox_style="carto-positron", height=500)
    st.plotly_chart(fig_map, use_container_width=True)

    # 📈 ANÁLISIS DE TENDENCIAS
    st.plotly_chart(px.line(df_f.sort_values("Fecha"), x="Fecha", y="Satisfaccion", color="Region", title="Evolución de Satisfacción por Zona"), use_container_width=True)

# ==========================================
# 6. PESTAÑAS ISO PROFUNDAS
# ==========================================
st.markdown("---")
t_gest, t_iso = st.tabs(["🛠️ GESTIÓN DE MAESTROS", "📑 AUDITORÍA ISO 9001:2015"])

with t_gest:
    if not df.empty:
        st.subheader("Edición de Datos de Auditoría")
        edit_df = st.data_editor(df, use_container_width=True)
        if st.button("Sincronizar Cambios con Nube"):
            conn = sqlite3.connect(DB)
            for _, r in edit_df.iterrows():
                conn.execute("UPDATE auditoria SET Nombre=?, Ciudad=?, Satisfaccion=?, Reclamos=?, Motivo=?, Observaciones=? WHERE id=?", 
                             (r["Nombre"], r["Ciudad"], r["Satisfaccion"], r["Reclamos"], r["Motivo"], r["Observaciones"], r["id"]))
            conn.commit(); conn.close(); st.success("Base de datos actualizada"); st.rerun()
    else: st.write("No hay datos.")

with t_iso:
    st.subheader("Sistema de Alerta Temprana ISO")
    pdf_bytes = generar_pdf_pro(df_f if 'df_f' in locals() else pd.DataFrame(), nps if 'nps' in locals() else 0, avg_sat if 'avg_sat' in locals() else 0, st.session_state.usuario)
    st.download_button("📥 DESCARGAR INFORME TÉCNICO PDF", pdf_bytes, f"Reporte_TQ_ISO_{date.today()}.pdf", "application/pdf")
    
    if not df_f.empty:
        fallas = df_f[df_f["Motivo"] != "Ninguna"]
        MATRIZ = {
            "Calidad": ("8.7", "Rojo", "CRÍTICO", "Bloqueo inmediato de inventario.", "Jefe Planta"),
            "Logística": ("8.4", "Naranja", "ALTO", "Auditoría a transportador externo.", "Jefe Logística"),
            "Precios": ("8.2.1", "Amarillo", "MEDIO", "Revisión de márgenes en sistema.", "Dir. Comercial"),
            "Agotados": ("8.1", "Naranja", "ALTO", "Ajuste de MRP y stock seguridad.", "Planeación"),
            "Atención": ("7.2", "Amarillo", "MEDIO", "Plan de re-entrenamiento técnico.", "Gestión Humana")
        }
        
        for m, count in fallas["Motivo"].value_counts().items():
            num, col, nivel, accion, resp = MATRIZ.get(m, ("-", "Gris", "Bajo", "Revisar", "Auditor"))
            # Colores para el semáforo visual
            hex_col = {"Rojo": "#ffcccc", "Naranja": "#ffe5cc", "Amarillo": "#ffffcc", "Gris": "#f2f2f2"}[col]
            border = {"Rojo": "#cc0000", "Naranja": "#ff8000", "Amarillo": "#cccc00", "Gris": "#666666"}[col]
            
            st.markdown(f"""
            <div style="padding:15px; border-radius:8px; border-left: 10px solid {border}; background-color:{hex_col}; margin-bottom:10px">
                <h4 style="margin:0;">🔴 SEMÁFORO {nivel}: {m} (Numeral {num})</h4>
                <b>Incidencias:</b> {count} | <b>Acción Requerida:</b> {accion}<br>
                <b>Responsable Primario:</b> {resp} | <b>Tiempo de Cierre:</b> 48-72 Horas
            </div>
            """, unsafe_allow_html=True)

st.caption("v17.0 Gold Standard | Proyecto TQ Final | Jhon Marin")
