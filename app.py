¡Entendido! He agregado un diccionario maestro (`MAPEO_CIUDAD_ZONA`) que vincula exactamente cada ciudad con su zona correspondiente (por ejemplo, Medellín -> Antioquia). 

Para cumplir tu regla de **"no tocar nada más"** y evitar que Streamlit se bloquee por estar dentro de un formulario (`st.form`), simplemente oculté el selector manual de zona y ahora el sistema **calcula y asigna la zona correcta automáticamente en la base de datos** al darle guardar, basándose en la ciudad que elegiste. 

Aquí tienes el código con este único ajuste implementado:

```python
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
st.set_page_config(page_title="TQ BI Enterprise v17.5 Platinum", layout="wide", page_icon="💊")

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
        st.title("🔐 Acceso Empresarial TQ")
        with st.container():
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.button("Ingresar Sistema Platinum"):
                usuarios_db = {
                    "equipotq": {"pass": hash_pass("tqcalidad2024"), "role": "Equipo Auditor"}
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
# PDF EJECUTIVO MEJORADO (CON CORRECCIÓN UNICODE)
# ================================
def limpiar_texto(t):
    """Limpia caracteres no compatibles con latin-1 para evitar UnicodeEncodeError"""
    if not isinstance(t, str): return str(t)
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N", "🔴": "(ALTO)", "🟡": "(MEDIO)", "🟢": "(BAJO)"
    }
    for char, rep in replacements.items():
        t = t.replace(char, rep)
    return t

def generar_pdf(df, nps, avg, usuario):
    if not PDF_OK: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(190, 15, limpiar_texto("TECNOQUIMICAS S.A - REPORTE EJECUTIVO DE CALIDAD"), ln=True, align="C")
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, limpiar_texto(f"Auditor Responsable: {usuario} | Fecha de Emision: {date.today()}"), ln=True, align="C")
    pdf.ln(10)
    
    # KPIs
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "1. RESUMEN ESTRATEGICO (KPIs)", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(95, 10, f"Net Promoter Score (NPS): {nps:.1f}%")
    pdf.cell(95, 10, limpiar_texto(f"Indice de Satisfaccion: {avg:.1f}%"), ln=True)
    pdf.ln(5)

    # Auditoria
    fallas = df[df["Motivo"] != "Ninguna"] if "Motivo" in df.columns else pd.DataFrame()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "2. ANALISIS DE NO CONFORMIDADES ISO 9001", ln=True)
    
    if not fallas.empty:
        pdf.set_font("Arial", "", 9)
        for _, r in fallas.iterrows():
            info = MATRIZ_ISO.get(r['Motivo'], {})
            txt = (f"ID: {r['id']} | CIUDAD: {limpiar_texto(r['Ciudad'])} | RIESGO: {limpiar_texto(info.get('riesgo',''))}\n"
                   f"NUMERAL: {limpiar_texto(info.get('numeral',''))}\n"
                   f"ACCION: {limpiar_texto(info.get('solucion',''))}\n"
                   f"RESPONSABLE: {limpiar_texto(info.get('responsable',''))} | SLA: {info.get('sla','')}\n")
            pdf.multi_cell(0, 5, txt)
            pdf.ln(3)
            
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "3. CONCLUSION EJECUTIVA", ln=True)
    pdf.set_font("Arial", "I", 10)
    conclusion = "Operacion estable" if nps > 50 else "Se requiere intervencion inmediata en procesos de calidad."
    pdf.multi_cell(0, 8, limpiar_texto(f"Basado en los datos analizados: {conclusion}"))
    
    # Retornamos el PDF codificado correctamente
    return pdf.output(dest="S").encode("latin-1", errors="replace")

# ================================
# SIDEBAR (GESTIÓN Y REGISTRO)
# ================================
st.sidebar.title("🏢 TQ BI PRO v17.5")
st.sidebar.markdown(f"**Usuario:** `{st.session_state.usuario}`")
st.sidebar.markdown(f"**Rol:** `{st.session_state.rol}`")
st.sidebar.markdown("---")

# Diccionario maestro para asignación automática Ciudad -> Zona
MAPEO_CIUDAD_ZONA = {
    "Leticia": "Llanos/Amazonía", "Medellín": "Antioquia", "Arauca": "Llanos/Amazonía",
    "Barranquilla": "Costa Norte", "Cartagena": "Costa Norte", "Tunja": "Centro (Bogotá/Boyacá)",
    "Manizales": "Eje Cafetero", "Florencia": "Llanos/Amazonía", "Yopal": "Llanos/Amazonía",
    "Popayán": "Valle y Cauca", "Valledupar": "Costa Norte", "Quibdó": "Antioquia",
    "Montería": "Costa Norte", "Bogotá": "Centro (Bogotá/Boyacá)", "Inírida": "Llanos/Amazonía",
    "San José del Guaviare": "Llanos/Amazonía", "Neiva": "Sur (Huila/Nariño)", "Riohacha": "Costa Norte",
    "Santa Marta": "Costa Norte", "Villavicencio": "Llanos/Amazonía", "Pasto": "Sur (Huila/Nariño)",
    "Cúcuta": "Santanderes", "Mocoa": "Sur (Huila/Nariño)", "Armenia": "Eje Cafetero",
    "Pereira": "Eje Cafetero", "San Andrés": "Costa Norte", "Bucaramanga": "Santanderes",
    "Sincelejo": "Costa Norte", "Ibagué": "Centro (Bogotá/Boyacá)", "Cali": "Valle y Cauca",
    "Mitú": "Llanos/Amazonía", "Puerto Carreño": "Llanos/Amazonía", "Soacha": "Centro (Bogotá/Boyacá)",
    "Bello": "Antioquia", "Soledad": "Costa Norte", "Buenaventura": "Valle y Cauca",
    "Palmira": "Valle y Cauca", "Tuluá": "Valle y Cauca", "Ipiales": "Sur (Huila/Nariño)",
    "Barrancabermeja": "Santanderes"
}

CIUDADES = sorted(list(MAPEO_CIUDAD_ZONA.keys()))
ZONAS = ["Antioquia", "Valle y Cauca", "Centro (Bogotá/Boyacá)", "Costa Norte", "Santanderes", "Eje Cafetero", "Sur (Huila/Nariño)", "Llanos/Amazonía"]

with st.sidebar.form("form"):
    st.subheader("📝 Captura de Datos")
    nombre = st.text_input("Punto / Cliente")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad", CIUDADES)
    # ⚠️ El input manual de Zona se eliminó, ahora se asigna automáticamente al guardar
    canal = st.selectbox("Canal", ["Ventas","Digital","Farma","Institucional"])
    sat = st.slider("Satisfacción (%)", 0, 100, 80)
    pqrs = st.number_input("Reclamos", 0, 100, 0)
    motivo = st.selectbox("Motivo No Conformidad", ["Ninguna","Calidad","Precios","Logística","Agotados","Atención"])
    obs = st.text_area("Observaciones Técnicas")

    if st.form_submit_button("💾 Guardar en Base de Datos"):
        zona_automatica = MAPEO_CIUDAD_ZONA[ciudad] # Asignación matemática directa
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO auditoria VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
                     (str(date.today()), nombre, contacto, ciudad, zona_automatica, canal, sat, pqrs, motivo, obs))
        conn.commit(); conn.close()
        st.cache_data.clear(); st.success(f"✅ Registro almacenado en {zona_automatica}"); st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🗑️ Zona de Peligro")

if st.sidebar.button("🗑️ Borrar Último"):
    st.sidebar.warning("¿Está seguro? Esta acción es irreversible.")
    if st.sidebar.button("Confirmar Borrado Último"):
        conn = sqlite3.connect(DB)
        conn.execute("DELETE FROM auditoria WHERE id = (SELECT MAX(id) FROM auditoria)")
        conn.commit(); conn.close()
        st.cache_data.clear(); st.success("Registro eliminado"); st.rerun()

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear(); st.rerun()

# ================================
# DASHBOARD EJECUTIVO
# ================================
st.title("🏢 TQ Business Intelligence Enterprise")
st.markdown("---")

df = load_data()

with st.container():
    f1, f2 = st.columns(2)
    zona_sel = f1.multiselect("📍 Zona Operativa", ZONAS, default=ZONAS)
    can_sel = f2.multiselect("📦 Canal de Distribución", ["Ventas","Digital","Farma","Institucional"], default=["Ventas","Digital","Farma","Institucional"])

df_f = df[(df["Region"].isin(zona_sel)) & (df["Canal"].isin(can_sel))] if not df.empty else pd.DataFrame()

nps, avg_sat = 0, 0

if not df_f.empty:
    prom = len(df_f[df_f["Satisfaccion"]>=90])
    detr = len(df_f[df_f["Satisfaccion"]<70])
    nps = ((prom-detr)/len(df_f))*100
    avg_sat = df_f["Satisfaccion"].mean()
    total_pqrs = int(df_f["Reclamos"].sum())

    if nps < 50: st.error(f"🔴 **ALERTA CRÍTICA NPS:** El índice actual ({nps:.1f}%) está por debajo del umbral corporativo.")
    if avg_sat < 70: st.warning(f"🟡 **ALERTA SATISFACCIÓN:** La media de satisfacción ({avg_sat:.1f}%) requiere atención inmediata.")
    if total_pqrs > 10: st.error(f"🚨 **RIESGO OPERATIVO:** Alto volumen de reclamos detectado ({total_pqrs} PQRS).")

    st.markdown("### 📈 Indicadores Clave de Gestión")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Loyalty NPS", f"{nps:.1f}%", delta=f"{nps-50:.1f}% vs Goal")
    k2.metric("Customer Sat", f"{avg_sat:.1f}%")
    k3.metric("Total Reclamos", total_pqrs)
    k4.metric("Tasa de Falla", f"{(total_pqrs/len(df_f)):.2f}")

    st.markdown("---")
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        fig = px.bar(
            df_f.groupby("Region")["Satisfaccion"].mean().reset_index().sort_values("Satisfaccion", ascending=False),
            x="Region", y="Satisfaccion", color="Satisfaccion",
            color_continuous_scale="RdYlGn", text_auto=".1f",
            title="🎯 Ranking de Desempeño por Zona"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.markdown("#### 🚦 Semáforo de Calidad")
        for z in zona_sel:
            sat_z = df_f[df_f["Region"]==z]["Satisfaccion"].mean()
            if sat_z >= 85: st.success(f"🟢 {z}: {sat_z:.1f}%")
            elif sat_z >= 70: st.warning(f"🟡 {z}: {sat_z:.1f}%")
            else: st.error(f"🔴 {z}: {sat_z:.1f}%")

else:
    st.info("💡 Bienvenido. No hay datos en el filtro actual. Por favor, registre hallazgos en el panel lateral.")

# ================================
# TABS PROFESIONALES
# ================================
st.markdown("---")
tab1, tab2 = st.tabs(["🛠️ Gestión de Datos e Histórico","📑 Auditoría ISO 9001 PRO"])

with tab1:
    st.subheader("⚙️ Panel de Control de Datos")
    if not df.empty:
        with st.expander("🗑️ Herramientas de Eliminación"):
            col_del1, col_del2 = st.columns([1,3])
            
            # FIX: Usar selectbox con los IDs reales para evitar borrar IDs inexistentes
            ids_disponibles = df["id"].tolist() if not df.empty else []
            id_borrar = col_del1.selectbox("ID del Registro", options=ids_disponibles)
            
            if col_del2.button("⚠️ ELIMINAR REGISTRO POR ID"):
                if ids_disponibles: # Validar que sí haya registros para borrar
                    conn = sqlite3.connect(DB)
                    conn.execute(f"DELETE FROM auditoria WHERE id = {id_borrar}")
                    conn.commit(); conn.close()
                    st.cache_data.clear()
                    st.success(f"Registro {id_borrar} eliminado permanentemente.")
                    st.rerun()

        st.markdown("#### Tabla Maestra de Auditoría")
        edit = st.data_editor(df, use_container_width=True)
        if st.button("🔄 Sincronizar Cambios"):
            conn = sqlite3.connect(DB)
            for _,r in edit.iterrows():
                conn.execute("""UPDATE auditoria SET Fecha=?,Nombre=?,Contacto=?,Ciudad=?,Region=?,Canal=?,Satisfaccion=?,Reclamos=?,Motivo=?,Observaciones=? WHERE id=?""",
                            (str(r["Fecha"]),r["Nombre"],r["Contacto"],r["Ciudad"],r["Region"],r["Canal"],r["Satisfaccion"],r["Reclamos"],r["Motivo"],r["Observaciones"],r["id"]))
            conn.commit(); conn.close()
            st.success("✅ Base de Datos Sincronizada"); st.rerun()
    else:
        st.write("Esperando datos para mostrar historial...")

with tab2:
   st.subheader("📑 Auditoría ISO 9001:2015 - Inteligencia de Riesgo")
   
   if PDF_OK:
       try:
           pdf_file = generar_pdf(df_f, nps, avg_sat, st.session_state.usuario)
           st.download_button("📥 Descargar Reporte Ejecutivo PDF", pdf_file, f"TQ_Executive_Report_{date.today()}.pdf")
       except Exception as e:
           st.error(f"Error al generar PDF: {e}")

   if not df_f.empty:
       st.markdown("---")
       fallas = df_f[df_f["Motivo"]!="Ninguna"]
       if not fallas.empty:
           top_falla = fallas["Motivo"].value_counts().idxmax()
           st.error(f"📌 **HALLAZGO CRÍTICO:** La falla más recurrente es **{top_falla}**.")

           for f, c in fallas["Motivo"].value_counts().items():
               info = MATRIZ_ISO.get(f, {})
               with st.expander(f"📌 {f.upper()} | {c} Incidentes | Riesgo: {info.get('riesgo')}"):
                   c_iso1, c_iso2 = st.columns(2)
                   with c_iso1:
                       st.markdown(f"**🔍 Causa Raíz Sugerida:**\n{info.get('causa')}")
                       st.markdown(f"**⚖️ Numeral ISO:**\n{info.get('numeral')}")
                   with c_iso2:
                        st.markdown(f"**👤 Responsable:**\n{info.get('responsable')}")
                        st.markdown(f"**⏱️ SLA de Solución:**\n{info.get('sla')}")
                   st.info(f"**🎯 Acción Correctiva Proyectada:**\n{info.get('solucion')}")
       else:
           st.success("✅ **CUMPLIMIENTO TOTAL:** La operación cumple con el 100% de los estándares ISO en el filtro seleccionado.")

st.caption(f"TQ BI Enterprise v17.5 Platinum | © {date.today().year} Tecnoquímicas S.A. | Auditoría Senior")
```
