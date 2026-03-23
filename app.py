import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import hashlib
from datetime import date

# ================================
# IMPORT PDF SEGURO
# ================================
try:
    from fpdf import FPDF
    PDF_OK = True
except:
    PDF_OK = False

# ================================
# CONFIGURACIÓN Y ESTILO UI
# ================================
st.set_page_config(page_title="SGC TQ - Gestión de Auditoría", layout="wide", page_icon="💊")

# 📊 MATRIZ TÉCNICA ISO 9001 AMPLIADA (Nivel Profesional)
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

# ================================
# SEGURIDAD (LOGIN)
# ================================
def hash_pass(p):
    return hashlib.sha256(p.strip().encode()).hexdigest()

def check_password():
    if not st.session_state.get("password_correct", False):
        st.title("🔐 SGC TQ - Acceso al Sistema de Auditoría")
        with st.container():
            user = st.text_input("Usuario (Auditor)")
            password = st.text_input("Contraseña Corporativa", type="password")
            if st.button("Ingresar al SGC"):
                usuarios_db = {
                    "admin": {"pass": hash_pass("tq2026"), "role": "Administrador"},
                    "jhonmarin": {"pass": hash_pass("Jhonmarin31."), "role": "Auditor Senior"}
                }
                if user.strip() in usuarios_db and hash_pass(password) == usuarios_db[user.strip()]["pass"]:
                    st.session_state["password_correct"] = True
                    st.session_state["usuario"] = user
                    st.session_state["rol"] = usuarios_db[user]["role"]
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas")
        return False
    return True

if not check_password():
    st.stop()

# ================================
# BASE DE DATOS
# ================================
DB = "tq_pro.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Fecha TEXT, Nombre TEXT, Contacto TEXT, Ciudad TEXT,
        Region TEXT, Canal TEXT, Satisfaccion REAL,
        Reclamos INTEGER, Motivo TEXT, Observaciones TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

def load_data():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM auditoria", conn)
    conn.close()
    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
    return df

# ================================
# PDF EJECUTIVO MEJORADO
# ================================
def generar_pdf(df, nps, avg, usuario):
    if not PDF_OK: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(190, 15, "SGC TQ - INFORME ESTRATEGICO DE AUDITORIA", ln=True, align="C")
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, f"Auditor Responsable: {usuario} | Fecha de Emisión: {date.today()}", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "1. RESUMEN ESTRATEGICO (KPIs)", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(95, 10, f"Net Promoter Score (NPS): {nps:.1f}%")
    pdf.cell(95, 10, f"Indice de Satisfaccion: {avg:.1f}%", ln=True)
    pdf.ln(5)

    fallas = df[df["Motivo"] != "Ninguna"]
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "2. ANALISIS DE NO CONFORMIDADES ISO 9001", ln=True)
    
    if not fallas.empty:
        pdf.set_font("Arial", "", 9)
        for _, r in fallas.iterrows():
            info = MATRIZ_ISO.get(r['Motivo'], {})
            txt = (f"ID: {r['id']} | CIUDAD: {r['Ciudad']} | RIESGO: {info.get('riesgo','')}\n"
                   f"NUMERAL: {info.get('numeral','')}\n"
                   f"ACCION: {info.get('solucion','')}\n"
                   f"RESPONSABLE: {info.get('responsable','')} | SLA: {info.get('sla','')}\n")
            pdf.multi_cell(0, 5, txt)
            pdf.ln(3)
            
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "3. CONCLUSION EJECUTIVA", ln=True)
    pdf.set_font("Arial", "I", 10)
    conclusion = "Operacion estable" if nps > 50 else "Se requiere intervencion inmediata en procesos de calidad."
    pdf.multi_cell(0, 8, f"Basado en los datos analizados: {conclusion}")
    
    return pdf.output(dest="S").encode("latin-1")

# ================================
# SIDEBAR
# ================================
st.sidebar.title("💊 SGC TECNOQUÍMICAS")
st.sidebar.markdown(f"**Auditor Senior:** `{st.session_state.usuario}`")
st.sidebar.markdown(f"**Rol:** `{st.session_state.rol}`")
st.sidebar.markdown("---")

CIUDADES = sorted([
    "Leticia","Medellín","Arauca","Barranquilla","Cartagena","Tunja","Manizales","Florencia","Yopal","Popayán","Valledupar","Quibdó","Montería","Bogotá","Inírida","San José del Guaviare","Neiva","Riohacha","Santa Marta","Villavicencio","Pasto","Cúcuta","Mocoa","Armenia","Pereira","San Andrés","Bucaramanga","Sincelejo","Ibagué","Cali","Mitú","Puerto Carreño","Soacha","Bello","Soledad","Buenaventura","Palmira","Tuluá","Ipiales","Barrancabermeja"
])

ZONAS = ["Antioquia", "Valle y Cauca", "Centro (Bogotá/Boyacá)", "Costa Norte", "Santanderes", "Eje Cafetero", "Sur (Huila/Nariño)", "Llanos/Amazonía"]

with st.sidebar.form("form"):
    st.subheader("📝 Captura de Hallazgos")
    nombre = st.text_input("Punto / Cliente")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad", CIUDADES)
    zona = st.selectbox("Zona Operativa", ZONAS)
    canal = st.selectbox("Canal", ["Ventas","Digital","Farma","Institucional"])
    sat = st.slider("Satisfacción (%)", 0, 100, 80)
    pqrs = st.number_input("Reclamos", 0, 100, 0)
    motivo = st.selectbox("Motivo No Conformidad", ["Ninguna","Calidad","Precios","Logística","Agotados","Atención"])
    obs = st.text_area("Observaciones Técnicas")

    if st.form_submit_button("💾 Guardar en SGC"):
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO auditoria VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
                     (str(date.today()), nombre, contacto, ciudad, zona, canal, sat, pqrs, motivo, obs))
        conn.commit(); conn.close()
        st.cache_data.clear(); st.success("✅ Registro almacenado"); st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Borrar Último"):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM auditoria WHERE id = (SELECT MAX(id) FROM auditoria)")
    conn.commit(); conn.close()
    st.cache_data.clear(); st.warning("Registro eliminado"); st.rerun()

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear(); st.rerun()

# ================================
# DASHBOARD
# ================================
st.title("💊 SGC TQ - Dashboard de Inteligencia de Calidad")
st.markdown("---")

df = load_data()

with st.container():
    f1, f2 = st.columns(2)
    zona_sel = f1.multiselect("📍 Zona Operativa", ZONAS, default=ZONAS)
    can_sel = f2.multiselect("📦 Canal de Distribución", ["Ventas","Digital","Farma","Institucional"], default=["Ventas","Digital","Farma","Institucional"])

df_f = df[(df["Region"].isin(zona_sel)) & (df["Canal"].isin(can_sel))] if not df.empty else pd.DataFrame()

nps, avg_sat = 0, 0

if not df_f.empty:
    prom = len(df_f[df_f["Satisfaccion"]>=90]); detr = len(df_f[df_f["Satisfaccion"]<70])
    nps = ((prom-detr)/len(df_f))*100
    avg_sat = df_f["Satisfaccion"].mean()
    total_pqrs = int(df_f["Reclamos"].sum())

    if nps < 50: st.error(f"🔴 **ALERTA CRÍTICA NPS:** {nps:.1f}%")
    if avg_sat < 70: st.warning(f"🟡 **ALERTA SATISFACCIÓN:** {avg_sat:.1f}%")

    st.markdown("### 📈 Indicadores Estratégicos")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Loyalty NPS", f"{nps:.1f}%")
    k2.metric("Indice Satisfacción", f"{avg_sat:.1f}%")
    k3.metric("Total Reclamos", total_pqrs)
    k4.metric("Tasa Falla", f"{(total_pqrs/len(df_f)):.2f}")

    col_chart1, col_chart2 = st.columns([2, 1])
    with col_chart1:
        fig = px.bar(df_f.groupby("Region")["Satisfaccion"].mean().reset_index().sort_values("Satisfaccion", ascending=False),
                     x="Region", y="Satisfaccion", color="Satisfaccion", color_continuous_scale="RdYlGn", text_auto=".1f", title="🎯 Ranking por Zona Operativa")
        st.plotly_chart(fig, use_container_width=True)
    with col_chart2:
        st.markdown("#### 🚦 Semáforo de Calidad")
        for z in zona_sel:
            sat_z = df_f[df_f["Region"]==z]["Satisfaccion"].mean()
            if sat_z >= 85: st.success(f"🟢 {z}: {sat_z:.1f}%")
            elif sat_z >= 70: st.warning(f"🟡 {z}: {sat_z:.1f}%")
            else: st.error(f"🔴 {z}: {sat_z:.1f}%")
else:
    st.info("💡 Por favor, registre hallazgos en el SGC para activar el análisis.")

# ================================
# TABS
# ================================
st.markdown("---")
tab1, tab2 = st.tabs(["🛠️ Gestión de Histórico","📑 Auditoría ISO 9001 PRO"])

with tab1:
    st.subheader("⚙️ Control de Datos Históricos")
    if not df.empty:
        col_del1, col_del2 = st.columns([1,3])
        id_borrar = col_del1.number_input("ID a borrar", min_value=0, step=1)
        if col_del2.button("⚠️ ELIMINAR REGISTRO POR ID"):
            conn = sqlite3.connect(DB); conn.execute(f"DELETE FROM auditoria WHERE id = {id_borrar}"); conn.commit(); conn.close()
            st.cache_data.clear(); st.success(f"ID {id_borrar} eliminado"); st.rerun()
        edit = st.data_editor(df, use_container_width=True)
        if st.button("🔄 Sincronizar"):
            conn = sqlite3.connect(DB)
            for _,r in edit.iterrows():
                conn.execute("""UPDATE auditoria SET Fecha=?,Nombre=?,Contacto=?,Ciudad=?,Region=?,Canal=?,Satisfaccion=?,Reclamos=?,Motivo=?,Observaciones=? WHERE id=?""",
                             (str(r["Fecha"]),r["Nombre"],r["Contacto"],r["Ciudad"],r["Region"],r["Canal"],r["Satisfaccion"],r["Reclamos"],r["Motivo"],r["Observaciones"],r["id"]))
            conn.commit(); conn.close(); st.success("SGC Actualizado"); st.rerun()

with tab2:
    st.subheader("📑 Análisis de No Conformidades ISO 9001")
    if PDF_OK:
        pdf_file = generar_pdf(df_f, nps, avg_sat, st.session_state.usuario)
        st.download_button("📥 Descargar Reporte de Auditoría PDF", pdf_file, f"Reporte_ISO_TQ_{date.today()}.pdf")
    if not df_f.empty:
        fallas = df_f[df_f["Motivo"]!="Ninguna"]
        if not fallas.empty:
            for f, c in fallas["Motivo"].value_counts().items():
                info = MATRIZ_ISO.get(f, {})
                with st.expander(f"📌 {f.upper()} | {c} Incidentes | Riesgo: {info.get('riesgo')}"):
                    c_iso1, c_iso2 = st.columns(2)
                    with c_iso1:
                        st.markdown(f"**🔍 Causa Raíz:**\n{info.get('causa')}")
                        st.markdown(f"**⚖️ Numeral ISO:**\n{info.get('numeral')}")
                    with c_iso2:
                        st.markdown(f"**👤 Responsable:**\n{info.get('responsable')}")
                        st.markdown(f"**⏱️ SLA:**\n{info.get('sla')}")
                    st.info(f"**🎯 Acción Correctiva:**\n{info.get('solucion')}")
        else:
            st.success("✅ CUMPLIMIENTO TOTAL: Operación bajo estándares ISO.")

st.caption(f"SGC TQ v17.5 | © {date.today().year} Sistema de Gestión de Calidad - Tecnoquímicas | Proyecto Jhon Marin")
