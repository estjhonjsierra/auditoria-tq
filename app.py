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
    page_title="SGC TQ - Sistema de Gestión de Calidad",
    layout="wide",
    page_icon="💊",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado para métricas y alertas
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_with_html=True)

# =================================================================
# 3. MATRIZ ISO 9001:2015 (Cerebro de la Auditoría)
# =================================================================
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
        st.title("🔐 SGC TQ - Acceso Corporativo")
        col1, col2 = st.columns([1, 1])
        with col1:
            user = st.text_input("Usuario (Equipo Auditor)")
            password = st.text_input("Contraseña Corporativa", type="password")
            if st.button("Ingresar al Sistema"):
                usuarios_db = {"equipotq": {"pass": hash_pass("tqcalidad2024"), "role": "Equipo Auditor"}}
                if user.strip() in usuarios_db and hash_pass(password) == usuarios_db[user.strip()]["pass"]:
                    st.session_state["password_correct"] = True
                    st.session_state["usuario"] = user
                    st.session_state["rol"] = usuarios_db[user]["role"]
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas.")
        st.stop()
    return True

check_password()

# =================================================================
# 5. GESTIÓN DE BASE DE DATOS (SQLite)
# =================================================================
DB_NAME = "tq_pro.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Fecha TEXT, Nombre TEXT, Contacto TEXT, Ciudad TEXT,
                Region TEXT, Canal TEXT, Satisfaccion REAL,
                Reclamos INTEGER, Motivo TEXT, Observaciones TEXT
            )
        """)

def load_data():
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql("SELECT * FROM auditoria", conn)
        if not df.empty:
            df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
        return df

init_db()

# =================================================================
# 6. GENERACIÓN DE REPORTES PDF
# =================================================================
def generar_pdf(df_export, nps, avg_sat, usuario):
    if not PDF_OK: return None
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_fill_color(0, 51, 102)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 25, "SGC TECNOQUIMICAS S.A.", ln=True, align="C")
    
    # Datos de Auditoría
    pdf.set_y(45)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"REPORTE ESTRATEGICO DE CALIDAD - {date.today()}", ln=True, align="L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 7, f"Responsable: {usuario} | Region: Nacional", ln=True)
    pdf.ln(5)

    # Resumen Ejecutivo (KPIs)
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(190, 10, " 1. RESUMEN DE INDICADORES", ln=True, fill=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(95, 10, f"Loyalty NPS: {nps:.1f}%")
    pdf.cell(95, 10, f"Nivel Satisfaccion: {avg_sat:.1f}%", ln=True)
    pdf.ln(5)

    # Tabla de Hallazgos
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, " 2. DETALLE DE NO CONFORMIDADES ISO 9001", ln=True, fill=True)
    pdf.ln(2)
    
    fallas = df_export[df_export["Motivo"] != "Ninguna"]
    if not fallas.empty:
        pdf.set_font("Arial", "", 9)
        for _, r in fallas.iterrows():
            info = MATRIZ_ISO.get(r['Motivo'], {})
            linea = f"[{r['id']}] {r['Ciudad']} - {r['Motivo']}: {info.get('numeral')} | Riesgo: {info.get('riesgo')}"
            pdf.multi_cell(0, 6, linea.encode('latin-1', 'replace').decode('latin-1'))
            pdf.set_font("Arial", "I", 8)
            pdf.multi_cell(0, 5, f"Accion: {info.get('solucion')}".encode('latin-1', 'replace').decode('latin-1'))
            pdf.set_font("Arial", "", 9)
            pdf.ln(2)
    
    return pdf.output(dest="S").encode("latin-1", "ignore")

# =================================================================
# 7. BARRA LATERAL (SIDEBAR) - CAPTURA Y CONTROL
# =================================================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Logo_Tecnoqu%C3%ADmicas.svg/1200px-Logo_Tecnoqu%C3%ADmicas.svg.png", width=200)
st.sidebar.title("🛠️ Panel de Control")

CIUDADES = sorted(["Leticia","Medellín","Barranquilla","Cartagena","Tunja","Manizales","Popayán","Valledupar","Montería","Bogotá","Neiva","Santa Marta","Villavicencio","Pasto","Cúcuta","Armenia","Pereira","Bucaramanga","Sincelejo","Ibagué","Cali","Soacha","Buenaventura","Palmira","Tuluá","Barrancabermeja"])
ZONAS = ["Antioquia", "Valle y Cauca", "Centro (Bogotá/Boyacá)", "Costa Norte", "Santanderes", "Eje Cafetero", "Sur (Huila/Nariño)", "Llanos/Amazonía"]

with st.sidebar.form("form_registro"):
    st.subheader("📝 Nuevo Registro")
    f_nombre = st.text_input("Punto / Cliente", placeholder="Ej: Droguería TQ 01")
    f_contacto = st.text_input("Contacto")
    f_ciudad = st.selectbox("Ciudad", CIUDADES)
    f_zona = st.selectbox("Zona Operativa", ZONAS)
    f_canal = st.selectbox("Canal", ["Ventas","Digital","Farma","Institucional"])
    f_sat = st.slider("Satisfacción (%)", 0, 100, 85)
    f_pqrs = st.number_input("Reclamos", 0, 50, 0)
    f_motivo = st.selectbox("No Conformidad", ["Ninguna","Calidad","Precios","Logística","Agotados","Atención"])
    f_obs = st.text_area("Notas Técnicas")
    
    if st.form_submit_button("🚀 Registrar Hallazgo"):
        if f_nombre:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("""INSERT INTO auditoria 
                    (Fecha, Nombre, Contacto, Ciudad, Region, Canal, Satisfaccion, Reclamos, Motivo, Observaciones) 
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (str(date.today()), f_nombre, f_contacto, f_ciudad, f_f_zona if 'f_f_zona' in locals() else f_zona, f_canal, f_sat, f_pqrs, f_motivo, f_obs))
            st.sidebar.success("✅ Guardado con éxito")
            st.rerun()
        else:
            st.sidebar.error("⚠️ Ingrese el nombre del cliente")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Borrar Último Ingreso"):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM auditoria WHERE id = (SELECT MAX(id) FROM auditoria)")
    st.sidebar.warning("Registro eliminado")
    st.rerun()

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

# =================================================================
# 8. DASHBOARD ESTRATÉGICO
# =================================================================
st.title("💊 SGC TQ - Dashboard de Inteligencia de Calidad")
df_master = load_data()

if not df_master.empty:
    # Filtros dinámicos
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sel_zona = st.multiselect("📍 Filtrar por Zona", ZONAS, default=ZONAS)
    with col_f2:
        sel_canal = st.multiselect("📦 Filtrar por Canal", ["Ventas","Digital","Farma","Institucional"], default=["Ventas","Digital","Farma","Institucional"])
    
    df_f = df_master[(df_master["Region"].isin(sel_zona)) & (df_master["Canal"].isin(sel_canal))]
    
    if not df_f.empty:
        # Cálculos de KPI
        promotores = len(df_f[df_f["Satisfaccion"] >= 90])
        detractores = len(df_f[df_f["Satisfaccion"] < 70])
        nps_val = ((promotores - detractores) / len(df_f)) * 100
        avg_sat = df_f["Satisfaccion"].mean()
        total_pqrs = int(df_f["Reclamos"].sum())

        # Fila 1: Métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Loyalty NPS", f"{nps_val:.1f}%", f"{nps_val-50:.1f}%" if nps_val > 50 else f"{nps_val-50:.1f}%", delta_color="normal")
        m2.metric("Índice Satisfacción", f"{avg_sat:.1f}%")
        m3.metric("Total PQRS", total_pqrs)
        m4.metric("Tasa de Error", f"{(total_pqrs/len(df_f)):.2f}")

        # Fila 2: Gráficos y Semáforo
        g1, g2 = st.columns([2, 1])
        with g1:
            fig_bar = px.bar(
                df_f.groupby("Region")["Satisfaccion"].mean().reset_index().sort_values("Satisfaccion", ascending=False),
                x="Region", y="Satisfaccion", color="Satisfaccion",
                color_continuous_scale="RdYlGn", text_auto=".1f",
                title="🎯 Cumplimiento de Calidad por Zona"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with g2:
            st.markdown("#### 🚦 Semáforo ISO 9001")
            for z in sel_zona:
                sat_z = df_f[df_f["Region"] == z]["Satisfaccion"].mean()
                if pd.isna(sat_z): continue
                if sat_z >= 85: st.success(f"🟢 **{z}**: {sat_z:.1f}%")
                elif sat_z >= 70: st.warning(f"🟡 **{z}**: {sat_z:.1f}%")
                else: st.error(f"🔴 **{z}**: {sat_z:.1f}%")
    else:
        st.warning("⚠️ No hay datos para los filtros seleccionados.")
else:
    st.info("👋 Bienvenido. Comience registrando hallazgos en la barra lateral.")

# =================================================================
# 9. PESTAÑAS DE GESTIÓN (HISTÓRICO E ISO)
# =================================================================
st.markdown("---")
t_hist, t_iso = st.tabs(["🛠️ Gestión de Base de Datos", "📑 Auditoría ISO 9001 PRO"])

with t_hist:
    st.subheader("⚙️ Edición y Limpieza de Histórico")
    if not df_master.empty:
        # Editor interactivo
        df_edited = st.data_editor(df_master, use_container_width=True, key="main_editor", num_rows="dynamic")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Sincronizar Cambios de Texto"):
                with sqlite3.connect(DB_NAME) as conn:
                    for _, r in df_edited.iterrows():
                        conn.execute("""UPDATE auditoria SET 
                            Fecha=?, Nombre=?, Contacto=?, Ciudad=?, Region=?, Canal=?, 
                            Satisfaccion=?, Reclamos=?, Motivo=?, Observaciones=? WHERE id=?""",
                            (str(r["Fecha"]), r["Nombre"], r["Contacto"], r["Ciudad"], r["Region"], r["Canal"], r["Satisfaccion"], r["Reclamos"], r["Motivo"], r["Observaciones"], r["id"]))
                st.success("✅ Base de Datos actualizada")
                st.rerun()

        with col_btn2:
            st.markdown("---")
            st.write("🗑️ **Eliminación Definitiva**")
            ids_to_del = st.multiselect("Busque y seleccione los IDs a borrar:", df_master["id"].unique())
            if st.button("🚨 EJECUTAR ELIMINACIÓN"):
                if ids_to_del:
                    with sqlite3.connect(DB_NAME) as conn:
                        for i in ids_to_del:
                            conn.execute("DELETE FROM auditoria WHERE id = ?", (i,))
                    st.success(f"🔥 {len(ids_to_del)} registros eliminados.")
                    st.rerun()
                else:
                    st.error("Seleccione al menos un ID.")

with t_iso:
    st.subheader("📑 Análisis de No Conformidades")
    if not df_master.empty:
        # Generar PDF con los datos filtrados del dashboard
        if PDF_OK:
            reporte = generar_pdf(df_f if 'df_f' in locals() else df_master, 
                                 nps_val if 'nps_val' in locals() else 0, 
                                 avg_sat if 'avg_sat' in locals() else 0, 
                                 st.session_state.usuario)
            st.download_button("📥 Descargar Reporte PDF Corporativo", reporte, f"Reporte_SGC_TQ_{date.today()}.pdf", "application/pdf")
        
        # Desglose ISO
        fallas_iso = df_master[df_master["Motivo"] != "Ninguna"]
        if not fallas_iso.empty:
            for m in fallas_iso["Motivo"].unique():
                info = MATRIZ_ISO.get(m, {})
                with st.expander(f"📌 {m.upper()} - Riesgo: {info.get('riesgo')}"):
                    c_iso1, c_iso2 = st.columns(2)
                    with c_iso1:
                        st.markdown(f"**⚖️ Numeral:** {info.get('numeral')}")
                        st.markdown(f"**🔍 Causa:** {info.get('causa')}")
                    with c_iso2:
                        st.markdown(f"**👤 Responsable:** {info.get('responsable')}")
                        st.markdown(f"**⏱️ Tiempo (SLA):** {info.get('sla')}")
                    st.info(f"**🎯 Acción Correctiva:** {info.get('solucion')}")
        else:
            st.success("✨ No se encontraron desviaciones en los estándares ISO 9001.")

st.markdown("---")
st.caption(f"SGC TQ v19.8 | © {date.today().year} Sistema de Gestión de Calidad - Tecnoquímicas | Proyect Jhon Marin")
