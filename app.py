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

# ================================
# SEGURIDAD
# ================================
def hash_pass(p):
    return hashlib.sha256(p.strip().encode()).hexdigest()

def check_password():
    if not st.session_state.get("password_correct", False):
        st.title("🔐 SGC TQ - Acceso al Sistema de Auditoría")
        with st.container():
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
                    st.error("❌ Acceso denegado.")
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
# SIDEBAR
# ================================
st.sidebar.title("💊 SGC TECNOQUÍMICAS")
CIUDADES = sorted(["Leticia","Medellín","Barranquilla","Cartagena","Tunja","Manizales","Popayán","Valledupar","Montería","Bogotá","Neiva","Santa Marta","Villavicencio","Pasto","Cúcuta","Armenia","Pereira","Bucaramanga","Sincelejo","Ibagué","Cali","Soacha","Buenaventura","Palmira","Tuluá","Barrancabermeja"])
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
        conn.execute("INSERT INTO auditoria (Fecha, Nombre, Contacto, Ciudad, Region, Canal, Satisfaccion, Reclamos, Motivo, Observaciones) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (str(date.today()), nombre, contacto, ciudad, zona, canal, sat, pqrs, motivo, obs))
        conn.commit(); conn.close()
        st.cache_data.clear(); st.success("✅ Registro almacenado"); st.rerun()

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear(); st.rerun()

# ================================
# DASHBOARD
# ================================
st.title("💊 SGC TQ - Dashboard de Inteligencia")
df = load_data()

if not df.empty:
    f1, f2 = st.columns(2)
    zona_sel = f1.multiselect("📍 Zona", ZONAS, default=ZONAS)
    can_sel = f2.multiselect("📦 Canal", ["Ventas","Digital","Farma","Institucional"], default=["Ventas","Digital","Farma","Institucional"])
    df_f = df[(df["Region"].isin(zona_sel)) & (df["Canal"].isin(can_sel))]

    if not df_f.empty:
        prom = len(df_f[df_f["Satisfaccion"]>=90]); detr = len(df_f[df_f["Satisfaccion"]<70])
        nps = ((prom-detr)/len(df_f))*100
        avg_sat = df_f["Satisfaccion"].mean()
        
        st.markdown("### 📈 Indicadores Clave")
        k1, k2, k3 = st.columns(3)
        k1.metric("Loyalty NPS", f"{nps:.1f}%")
        k2.metric("Indice Satisfacción", f"{avg_sat:.1f}%")
        k3.metric("Total Reclamos", int(df_f["Reclamos"].sum()))
        
        fig = px.bar(df_f.groupby("Region")["Satisfaccion"].mean().reset_index(), x="Region", y="Satisfaccion", color="Satisfaccion", color_continuous_scale="RdYlGn")
        st.plotly_chart(fig, use_container_width=True)

# ================================
# TABS (ELIMINACIÓN CORREGIDA SIN TECLAS)
# ================================
st.markdown("---")
tab1, tab2 = st.tabs(["🛠️ Gestión de Histórico","📑 Auditoría ISO 9001 PRO"])

with tab1:
    st.subheader("⚙️ Control de Datos Históricos")
    if not df.empty:
        # 1. Editor de datos para cambios de texto
        edit = st.data_editor(df, use_container_width=True, key="editor_historico")
        
        if st.button("🔄 Guardar Cambios de Texto"):
            conn = sqlite3.connect(DB)
            for _, r in edit.iterrows():
                conn.execute("""UPDATE auditoria SET Fecha=?,Nombre=?,Contacto=?,Ciudad=?,Region=?,Canal=?,Satisfaccion=?,Reclamos=?,Motivo=?,Observaciones=? WHERE id=?""",
                             (str(r["Fecha"]), r["Nombre"], r["Contacto"], r["Ciudad"], r["Region"], r["Canal"], r["Satisfaccion"], r["Reclamos"], r["Motivo"], r["Observaciones"], r["id"]))
            conn.commit(); conn.close()
            st.success("✅ Cambios de texto guardados"); st.rerun()

        st.markdown("---")
        # 2. SECCIÓN DE ELIMINACIÓN DIRECTA (Solo Botón)
        st.subheader("🗑️ Eliminar Registros")
        ids_disponibles = df["id"].tolist()
        seleccionados = st.multiselect("Seleccione los IDs que desea eliminar definitivamente:", ids_disponibles)
        
        if st.button("⚠️ ELIMINAR SELECCIONADOS"):
            if seleccionados:
                conn = sqlite3.connect(DB)
                for id_del in seleccionados:
                    conn.execute("DELETE FROM auditoria WHERE id = ?", (id_del,))
                conn.commit(); conn.close()
                st.cache_data.clear()
                st.success(f"✅ Se eliminaron {len(seleccionados)} registros correctamente.")
                st.rerun()
            else:
                st.warning("Seleccione al menos un ID para eliminar.")

with tab2:
    st.subheader("📑 Auditoría ISO 9001")
    if not df.empty:
        fallas = df[df["Motivo"]!="Ninguna"]
        if not fallas.empty:
            for m in fallas["Motivo"].unique():
                info = MATRIZ_ISO.get(m, {})
                with st.expander(f"📌 {m} - Riesgo: {info.get('riesgo')}"):
                    st.write(f"**Numeral:** {info.get('numeral')}")
                    st.write(f"**Acción Correctiva:** {info.get('solucion')}")
        else:
            st.success("✅ Cumplimiento total.")

st.caption(f"SGC TQ v19.0 | © {date.today().year} Sistema de Gestión de Calidad - Tecnoquímicas | Proyecto Jhon Marin")
