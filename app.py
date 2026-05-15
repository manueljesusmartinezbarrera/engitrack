import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from sqlalchemy import text

st.set_page_config(page_title="EngiTrack", layout="centered", page_icon="⏱️")

# --- CSS AGRESIVO PARA BOTONES ---
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background-color: #FFFFFF; font-family: 'Segoe UI', Tahoma, sans-serif; }
    .block-container { padding-top: 1rem !important; max-width: 650px; }

    /* Forzar botones superiores sin borde (Estilo Pestaña) */
    button[kind="secondary"] {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        color: #00A650 !important; /* Verde por defecto */
        font-size: 18px !important;
        font-weight: 500 !important;
    }
    button[kind="secondary"]:hover {
        background-color: #F4F6F8 !important; color: #1C64F2 !important;
    }

    /* Botón INICIAR (Gigante y Azul) */
    button[kind="primary"] {
        background-color: #1C64F2 !important; color: white !important; 
        border-radius: 50px !important; height: 75px !important;
        font-size: 24px !important; font-weight: bold !important; 
        border: none !important; width: 100% !important; 
        box-shadow: 0 10px 25px rgba(28, 100, 242, 0.3) !important; letter-spacing: 2px !important;
    }
    button[kind="primary"]:hover { background-color: #1A56D1 !important; transform: translateY(-2px); }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A SUPABASE ---
try:
    conn = st.connection("engidb", type="sql")
    with conn.session as s:
        s.execute(text('''CREATE TABLE IF NOT EXISTS ejercicios (id SERIAL PRIMARY KEY, asignatura TEXT, tema TEXT, ejercicio TEXT, dificultad TEXT, cuello_botella TEXT, fecha_registro DATE, fecha_repaso DATE, veces_repasado INTEGER)'''))
        s.execute(text('''CREATE TABLE IF NOT EXISTS pomodoros (id SERIAL PRIMARY KEY, asignatura TEXT, fecha DATE, minutos_estudiados INTEGER, tipo TEXT)'''))
        s.commit()
    db_ok = True
except Exception as e:
    db_ok = False

# --- ESTADO DE LA SESIÓN ---
if 'timer_seconds' not in st.session_state: st.session_state.timer_seconds = 20 * 60
if 'tiempo_inicial' not in st.session_state: st.session_state.tiempo_inicial = 20 * 60
if 'timer_running' not in st.session_state: st.session_state.timer_running = False
if 'modo_actual' not in st.session_state: st.session_state.modo_actual = "Pomodoro"
if 'count_pomo' not in st.session_state: st.session_state.count_pomo = 0
if 'count_desc' not in st.session_state: st.session_state.count_desc = 0
if 'count_largo' not in st.session_state: st.session_state.count_largo = 0

def calcular_proximo_repaso(fecha_base, dificultad, veces_repasado):
    dias = {"Fácil": 7, "Normal": 3, "Difícil": 1, "No pude hacerlo": 0}[dificultad] * (1.5 ** veces_repasado)
    if dias == 0: dias = 1
    return (datetime.strptime(fecha_base, '%Y-%m-%d') + timedelta(days=int(dias))).strftime('%Y-%m-%d')

if not db_ok:
    st.warning("⚠️ Sin conexión a la base de datos. Revisa el menú 'Settings -> Secrets' en Streamlit.")

# --- INTERFAZ ---
tab_pomo, tab_recall, tab_reg, tab_data = st.tabs(["⏱️ Foco", "🧠 Active Recall", "➕ Registro", "📊 Gestión"])

with tab_pomo:
    # Navegación Superior
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        if st.button(f"Pomodoro  {st.session_state.count_pomo}", use_container_width=True):
            st.session_state.timer_running = False; st.session_state.timer_seconds = 20 * 60
            st.session_state.tiempo_inicial = 20 * 60; st.session_state.modo_actual = "Pomodoro"; st.rerun()
    with col_m2:
        if st.button(f"Descanso  {st.session_state.count_desc}", use_container_width=True):
            st.session_state.timer_running = False; st.session_state.timer_seconds = 5 * 60
            st.session_state.tiempo_inicial = 5 * 60; st.session_state.modo_actual = "Descanso"; st.rerun()
    with col_m3:
        if st.button(f"Descanso largo  {st.session_state.count_largo}", use_container_width=True):
            st.session_state.timer_running = False; st.session_state.timer_seconds = 15 * 60
            st.session_state.tiempo_inicial = 15 * 60; st.session_state.modo_actual = "Descanso Largo"; st.rerun()

    # RELOJ CON HTML INLINE (Para forzar el tamaño gigante)
    mins, secs = divmod(st.session_state.timer_seconds, 60)
    reloj_html = f"""
    <div style="display: flex; justify-content: center; margin: 50px 0;">
        <div style="border: 4px solid #DCE6F9; border-radius: 50%; width: 380px; height: 380px; display: flex; justify-content: center; align-items: center; flex-direction: column; background-color: transparent;">
            <p style="font-size: 130px; color: #1C64F2; font-weight: 300; margin: 0; line-height: 1; letter-spacing: -3px; font-family: 'Segoe UI', Arial, sans-serif;">{mins:02d}:{secs:02d}</p>
            <p style="font-size: 20px; color: #1C64F2; margin-top: 15px; margin-bottom: 0;">Nivel</p>
            <p style="font-size: 24px; color: #1C64F2; font-weight: bold; margin-top: 0;">Popular</p>
        </div>
    </div>
    """
    st.markdown(reloj_html, unsafe_allow_html=True)

    # Botón Principal
    _, btn_col, _ = st.columns([1, 4, 1])
    with btn_col:
        texto_btn = "PAUSAR" if st.session_state.timer_running else "INICIAR"
        if st.button(texto_btn, type="primary", use_container_width=True):
            st.session_state.timer_running = not st.session_state.timer_running
            st.rerun()

    # Lógica del motor
    if st.session_state.timer_running and st.session_state.timer_seconds > 0:
        time.sleep(1)
        st.session_state.timer_seconds -= 1
        st.rerun()
    elif st.session_state.timer_seconds <= 0 and st.session_state.timer_running:
        st.session_state.timer_running = False
        st.balloons()
        if st.session_state.modo_actual == "Pomodoro": st.session_state.count_pomo += 1
        elif st.session_state.modo_actual == "Descanso": st.session_state.count_desc += 1
        elif st.session_state.modo_actual == "Descanso Largo": st.session_state.count_largo += 1
        st.rerun()

    # Guardado a Supabase
    if st.session_state.modo_actual == "Pomodoro" and (st.session_state.tiempo_inicial - st.session_state.timer_seconds) > 60:
        st.divider()
        seg_trans = st.session_state.tiempo_inicial - st.session_state.timer_seconds
        mins_reales = max(1, seg_trans // 60)
        
        asig_log = st.text_input("Asignatura a guardar:", "Circuitos")
        if st.button(f"💾 Guardar {mins_reales} Minutos", use_container_width=True) and db_ok:
            try:
                with conn.session as s:
                    s.execute(text("INSERT INTO pomodoros (asignatura, fecha, minutos_estudiados, tipo) VALUES (:a, :f, :m, :t)"), 
                              {"a": asig_log, "f": datetime.now().strftime('%Y-%m-%d'), "m": mins_reales, "t": "Pomodoro"})
                    s.commit()
                st.success(f"¡{mins_reales} minutos guardados!")
            except:
                st.error("Error al guardar.")
            st.session_state.timer_running = False; st.session_state.timer_seconds = 20 * 60; st.rerun()

# --- DEMÁS PESTAÑAS ---
with tab_recall:
    st.header("Repaso de hoy")
    hoy = datetime.now().strftime('%Y-%m-%d')
    if db_ok:
        try:
            df_repaso = conn.query(f"SELECT * FROM ejercicios WHERE fecha_repaso <= '{hoy}'")
            if df_repaso.empty: st.success("¡Todo al día!")
            else:
                for _, row in df_repaso.iterrows():
                    with st.expander(f"📌 {row['asignatura']} - {row['ejercicio']}"):
                        st.markdown(f"**Cuello de botella:** {row['cuello_botella']}")
                        cols = st.columns(4)
                        for i, dif in enumerate(["Fácil", "Normal", "Difícil", "No pude"]):
                            if cols[i].button(dif, key=f"btn_{row['id']}_{dif}"):
                                nf = calcular_proximo_repaso(hoy, dif if dif != "No pude" else "No pude hacerlo", row['veces_repasado']+1)
                                with conn.session as s:
                                    s.execute(text("UPDATE ejercicios SET fecha_repaso=:nf, veces_repasado=:vr WHERE id=:id"), {"nf": nf, "vr": row['veces_repasado']+1, "id": row['id']})
                                    s.commit(); st.rerun()
        except: pass

with tab_reg:
    st.header("Nuevo Problema")
    with st.form("reg"):
        ca, cb = st.columns(2)
        asig = ca.text_input("Asignatura"); tema = ca.text_input("Tema")
        ejer = cb.text_input("ID Ejercicio"); dif = cb.selectbox("Dificultad", ["Fácil", "Normal", "Difícil", "No pude hacerlo"])
        botella = st.text_area("Cuello de botella (Usa $ para fórmulas, ej: $F=ma$)")
        if st.form_submit_button("Guardar Problema") and db_ok:
            fr = datetime.now().strftime('%Y-%m-%d'); pr = calcular_proximo_repaso(fr, dif, 0)
            try:
                with conn.session as s:
                    s.execute(text("INSERT INTO ejercicios (asignatura, tema, ejercicio, dificultad, cuello_botella, fecha_registro, fecha_repaso, veces_repasado) VALUES (:a, :t, :e, :d, :c, :fr, :pr, :vr)"),
                              {"a": asig, "t": tema, "e": ejer, "d": dif, "c": botella, "fr": fr, "pr": pr, "vr": 0})
                    s.commit()
                st.success(f"Registrado. Próximo repaso: {pr}")
            except: st.error("Error al guardar en la nube.")

with tab_data:
    col_d1, col_d2 = st.columns(2)
    if db_ok:
        with col_d1:
            st.subheader("Tiempos Guardados")
            try: st.dataframe(conn.query("SELECT id, asignatura, minutos_estudiados FROM pomodoros"), use_container_width=True)
            except: pass
        with col_d2:
            st.subheader("Ejercicios")
            try: st.dataframe(conn.query("SELECT id, asignatura, ejercicio FROM ejercicios"), use_container_width=True)
            except: pass
