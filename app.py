import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import hashlib
import io
from datetime import date

# =================================================================
# 1. IMPORT PDF SEGURO (FPDF)
# =================================================================
try:
    from fpdf import FPDF
    PDF_OK = True
except ImportError:
    PDF_OK = False

# =================================================================
# 2. CONFIGURACIÓN E INTERFAZ (UI/UX)
# =================================================================
st.set_page_config(
    page_title="TQ BI Enterprise v17.5 Platinum", 
    layout="wide", 
    page_icon="💊",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_with_html=True)

# 📊 MATRIZ TÉCNICA ISO 9001 AMPLIADA
MATRIZ_ISO = {
    "Calidad": {
        "numeral": "8.7 Control de las salidas no conformes",
        "hallazgo": "Desviación en los estándares técnicos del producto o empaque.",
        "solucion": "Bloqueo inmediato de lote, análisis de causa raíz (Ishikawa) y disposición final.",
        "riesgo": "ALTO 🔴",
        "causa": "Falla en control de procesos productivos o materias primas.",
        "responsable": "Gerente de Calidad / Planta",
        "sla": "24 Horas"
    },
    "Precios": {
        "numeral": "8.2.1 Comunicación con el cliente",
        "hallazgo": "Inconsistencia entre precio facturado y precio exhibido.",
        "solucion": "Auditoría de lista de precios en SAP y actualización de POP.",
        "riesgo": "MEDIO 🟡",
        "causa": "Desincronización de bases de datos comerciales.",
        "responsable": "Director Comercial / Facturación",
        "sla": "48 Horas"
    },
    "Logística": {
        "numeral": "8.4 Control de procesos externos",
        "hallazgo": "Incumplimiento en tiempos de entrega o averías.",
        "solucion": "Re-evaluación del transportador y optimización de ruta.",
        "riesgo": "ALTO 🔴",
        "causa": "Falla en la cadena de suministros o transporte tercero.",
        "responsable": "Jefe de Logística / Distribución",
        "sla": "72 Horas"
    },
    "Agotados": {
        "numeral": "8.1 Planificación y control operacional",
        "hallazgo": "Ruptura de stock que afecta la continuidad.",
        "solucion": "Ajuste de pronóstico de demanda y aceleración de reposición.",
        "riesgo": "ALTO 🔴",
        "causa": "Error en proyección de demanda o retraso de proveedores.",
        "responsable": "Gerente de Compras / Planeación",
        "sla": "48 Horas"
    },
    "Atención": {
        "numeral": "7.2 Competencia",
        "hallazgo": "Falta de conocimiento técnico del personal.",
        "solucion": "Plan de re-entrenamiento en Universidad TQ.",
        "riesgo": "BAJO 🟢",
        "causa": "Brecha de capacitación en nuevos protocolos.",
        "responsable": "Gestión Humana / Capacitación",
        "sla": "1 Semana"
    }
}

# =================================================================
# 4. SEGURIDAD Y ACCESO
# =================================================================
def hash_pass(p):
    return hashlib.sha256(p.strip().encode()).hexdigest()

def check_password():
    if not st.session_state.get("password_correct", False):
        st.title("🔐 Acceso Empresarial TQ")
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Ingresar Sistema Platinum"):
            usuarios_db = {
                "admin": {"pass": hash_pass("tq2026"), "role": "Administrador"},
                "jhonmarin": {"pass": hash_pass("Jhonmarin31."), "role": "Auditor Senior"},
                "equipotq": {"pass": hash_pass("tqcalidad2024"), "role": "Equipo Auditor"}
            }
            if user.strip() in usuarios_db and hash_pass(password) == usuarios_db[user.strip()]["pass"]:
                st.session_state["password_correct"] = True
                st.session_state["usuario"] = user
                st.session_state["rol"] = usuarios_db[user]["role"]
                st.rerun()
            else:
                st.error("❌ Credenciales inválidas")
        st.stop()
    return True

check_password()

# =================================================================
# 5. BASE DE DATOS
# =================================================================
DB_NAME = "tq_pro.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT, Fecha TEXT, Nombre TEXT, Contacto TEXT, 
            Ciudad TEXT, Region TEXT, Canal TEXT, Satisfaccion REAL, 
            Reclamos INTEGER, Motivo TEXT, Observaciones TEXT)""")

def load_data():
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql("SELECT * FROM auditoria", conn)
        if not df.empty:
            df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
        return df

init_db()

# =================================================================
# 6. GENERACIÓN PDF (CORRECCIÓN DE CARACTERES)
# =================================================================
def generar_pdf(df_export, nps, avg_sat, usuario):
    if not PDF_OK: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(190, 15, "TECNOQUIMICAS S.A - REPORTE EJECUTIVO", ln=True, align="C")
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, f"Auditor: {usuario} | Fecha: {date.today()}", ln=True, align="C")
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "1. KPIs ESTRATEGICOS", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(95, 10, f"NPS: {nps:.1f}%")
    pdf.cell(95, 10, f"Satisfaccion: {avg_sat:.1f}%", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "2. DETALLE DE NO CONFORMIDADES", ln=True)
    
    fallas = df_export[df_export["Motivo"] != "Ninguna"] if "Motivo" in df_export.columns else pd.DataFrame()
    if not fallas.empty:
        pdf.set_font("Arial", "", 9)
        for _, r in fallas.iterrows():
            # EL PARCHE: encode/decode para que no explote con tildes
            txt = f"ID: {r['id']} | {r['Ciudad']} | Motivo: {r['Motivo']}".encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, txt)
            pdf.ln(2)
    
    return pdf.output(dest="S").encode("latin-1", "ignore")

# =================================================================
# 7. SIDEBAR (CORRECCIÓN DE BOTÓN BORRAR)
# =================================================================
st.sidebar.title("🏢 TQ BI PRO v17.5")
st.sidebar.markdown(f"**Usuario:** `{st.session_state.usuario}`")

CIUDADES = sorted(["Leticia","Medellín","Arauca","Barranquilla","Cartagena","Tunja","Manizales","Popayán","Valledupar","Quibdó","Montería","Bogotá","Neiva","Santa Marta","Villavicencio","Pasto","Cúcuta","Armenia","Pereira","Bucaramanga","Sincelejo","Ibagué","Cali","Soacha","Buenaventura","Palmira","Tuluá","Barrancabermeja"])
ZONAS = ["Antioquia", "Valle y Cauca", "Centro (Bogotá/Boyacá)", "Costa Norte", "Santanderes", "Eje Cafetero", "Sur (Huila/Nariño)", "Llanos/Amazonía"]

with st.sidebar.form("form_registro"):
    st.subheader("📝 Captura de Datos")
    f_nom = st.text_input("Punto / Cliente")
    f_con = st.text_input("Contacto")
    f_ciu = st.selectbox("Ciudad", CIUDADES)
    f_zon = st.selectbox("Zona Operativa", ZONAS)
    f_can = st.selectbox("Canal", ["Ventas","Digital","Farma","Institucional"])
    f_sat = st.slider("Satisfacción (%)", 0, 100, 85)
    f_pqr = st.number_input("Reclamos", 0, 50, 0)
    f_mot = st.selectbox("Motivo", ["Ninguna","Calidad","Precios","Logística","Agotados","Atención"])
    f_obs = st.text_area("Notas Técnicas")
    
    if st.form_submit_button("🚀 Guardar"):
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("INSERT INTO auditoria (Fecha, Nombre, Contacto, Ciudad, Region, Canal, Satisfaccion, Reclamos, Motivo, Observaciones) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (str(date.today()), f_nom, f_con, f_ciu, f_zon, f_can, f_sat, f_pqr, f_mot, f_obs))
        st.rerun()

st.sidebar.markdown("---")
# PARCHE: Borrar último con confirmación para que no falle el estado
if st.sidebar.button("🗑️ Borrar Último"):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM auditoria WHERE id = (SELECT MAX(id) FROM auditoria)")
    st.sidebar.warning("Registro eliminado")
    st.rerun()

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

# =================================================================
# 8. DASHBOARD
# =================================================================
st.title("🏢 TQ Business Intelligence Enterprise")
df_master = load_data()

if not df_master.empty:
    col_f1, col_f2 = st.columns(2)
    sel_zona = col_f1.multiselect("📍 Zona Operativa", ZONAS, default=ZONAS)
    sel_can = col_f2.multiselect("📦 Canal", ["Ventas","Digital","Farma","Institucional"], default=["Ventas","Digital","Farma","Institucional"])
    
    df_f = df_master[(df_master["Region"].isin(sel_zona)) & (df_master["Canal"].isin(sel_can))]
    
    if not df_f.empty:
        # KPIs
        prom = len(df_f[df_f["Satisfaccion"] >= 90])
        detr = len(df_f[df_f["Satisfaccion"] < 70])
        nps_val = ((prom - detr) / len(df_f)) * 100
        avg_sat = df_f["Satisfaccion"].mean()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Loyalty NPS", f"{nps_val:.1f}%")
        m2.metric("Customer Sat", f"{avg_sat:.1f}%")
        m3.metric("Total PQRS", int(df_f["Reclamos"].sum()))
        m4.metric("Tasa Falla", f"{(df_f['Reclamos'].sum()/len(df_f)):.2f}")

        # Gráfico
        fig = px.bar(df_f.groupby("Region")["Satisfaccion"].mean().reset_index(), 
                     x="Region", y="Satisfaccion", color="Satisfaccion", color_continuous_scale="RdYlGn", title="🎯 Desempeño por Zona")
        st.plotly_chart(fig, use_container_width=True)

# =================================================================
# 9. TABS (ELIMINACIÓN POR ID MULTISELECT)
# =================================================================
tab1, tab2 = st.tabs(["🛠️ Gestión e Histórico", "📑 Auditoría ISO 9001 PRO"])

with tab1:
    if not df_master.empty:
        st.subheader("🗑️ Eliminación Definitiva")
        ids_to_del = st.multiselect("Seleccione IDs para borrar:", df_master["id"].unique())
        if st.button("🚨 EJECUTAR ELIMINACIÓN"):
            if ids_to_del:
                with sqlite3.connect(DB_NAME) as conn:
                    for i in ids_to_del:
                        conn.execute("DELETE FROM auditoria WHERE id = ?", (i,))
                st.success("Registros eliminados")
                st.rerun()
        
        st.dataframe(df_master, use_container_width=True)

with tab2:
    if not df_master.empty:
        if PDF_OK:
            reporte = generar_pdf(df_f if 'df_f' in locals() else df_master, nps_val if 'nps_val' in locals() else 0, avg_sat if 'avg_sat' in locals() else 0, st.session_state.usuario)
            st.download_button("📥 Descargar Reporte PDF", reporte, "Reporte_TQ.pdf")
        
        for m in df_master[df_master["Motivo"] != "Ninguna"]["Motivo"].unique():
            info = MATRIZ_ISO.get(m, {})
            with st.expander(f"📌 {m.upper()} - Riesgo: {info.get('riesgo')}"):
                st.write(f"**Numeral:** {info.get('numeral')}")
                st.write(f"**Solución:** {info.get('solucion')}")
                st.write(f"**Responsable:** {info.get('responsable')}")

st.caption(f"SGC TQ v19.8 Platinum | Jhon Marin | {date.today().year}")
