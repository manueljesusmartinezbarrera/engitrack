import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from sqlalchemy import text

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="EngiTrack", layout="centered", page_icon="⏱️")

# --- CSS "PIXEL PERFECT" (Calcando tu imagen) ---
st.markdown("""
<style>
    /* Limpieza de la interfaz nativa de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #FFFFFF; font-family: 'Segoe UI', Tahoma, sans-serif; }
    
    /* Contenedor central superior */
    .block-container { padding-top: 2rem !important; max-width: 600px; }

    /* ESTILOS PARA LAS PESTAÑAS (Emulando tu diseño) */
    div[data-testid="column"] { display: flex; justify-content: center; align-items: center; }
    
    /* Pestaña 1: Pomodoro (Activo - Texto Azul, Línea Inferior) */
    div[data-testid="column"]:nth-child(1) button {
        background-color: transparent; border: none; color: #1C64F2; font-size: 18px; 
        border-bottom: 1px solid #1C64F2; border-radius: 0; padding: 10px 0; width: 100%;
    }
    
    /* Pestaña 2: Descanso (Inactivo - Fondo Gris Claro, Texto Verde) */
    div[data-testid="column"]:nth-child(2) button {
        background-color: #F3F6F9; border: none; color: #00A650; font-size: 18px; 
        border-radius: 6px; padding: 10px 0; width: 100%; transition: 0.2s;
    }
    
    /* Pestaña 3: Descanso Largo (Inactivo - Transparente, Texto Verde) */
    div[data-testid="column"]:nth-child(3) button {
        background-color: transparent; border: none; color: #00A650; font-size: 18px; 
        padding: 10px 0; width: 100%; transition: 0.2s;
    }

    /* EL RELOJ CENTRAL */
    .reloj-container { display: flex; justify-content: center; align-items: center; flex-direction: column; margin: 50px 0; }
    .reloj-circulo {
        border: 4px solid #DCE6F9; border-radius: 50%; width: 340px; height: 340px;
        display: flex; justify-content: center; align-items: center; flex-direction: column;
        background-color: #FFFFFF; 
    }
    .reloj-texto { font-size: 95px; color: #1C64F2; font-weight: 400; margin: 0; line-height: 1; font-family: 'Arial', sans-serif; letter-spacing: -2px; }
    .reloj-nivel { font-size: 18px; color: #1C64F2; margin-top: 20px; margin-bottom: 0;}
    .reloj-sub { font-size: 20px; color: #1C64F2; font-weight: 800; margin-top: 0;}
    
    /* BOTÓN INICIAR (Azul vibrante, redondeado) */
    .stButton > button[kind="primary"] {
        background-color: #1C64F2; color: white; border-radius: 50px; height: 70px;
        font-size: 22px; font-weight: 600; border: none; transition: 0.3s; width: 100%; 
        box-shadow: 0 8px 20px rgba(28, 100, 242, 0.25); letter-spacing: 2px;
    }
    .stButton > button[kind="primary"]:hover { background-color: #1A56D1; transform: translateY(-2px); box-shadow: 0 12px 25px rgba(28, 100, 242, 0.35); }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A SUPABASE ---
try:
    conn = st.connection("engidb", type="sql")
    with conn.session as s:
        s.execute(text('''CREATE TABLE IF NOT EXISTS ejercicios (id SERIAL PRIMARY KEY, asignatura TEXT, tema TEXT, ejercicio TEXT, dificultad TEXT, cuello_botella TEXT, fecha_registro DATE, fecha_repaso DATE, veces_repasado INTEGER)'''))
        s.execute(text('''CREATE TABLE IF NOT EXISTS pomodoros (id SERIAL PRIMARY KEY, asignatura TEXT, fecha DATE, minutos_estudiados INTEGER, tipo TEXT)'''))
        s.commit()
except Exception as e:
    st.warning("Conectando base de datos o sin configurar localmente...")

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

# --- INTERFAZ ---
tab_pomo, tab_recall, tab_reg, tab_data = st.tabs(["⏱️ Foco", "🧠 Active Recall", "➕ Registro", "📊 Gestión"])

with tab_pomo:
    # Top Navigation (Idéntico a tu imagen)
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        if st.button(f"Pomodoro {st.session_state.count_pomo}", use_container_width=True):
            st.session_state.timer_running = False; st.session_state.timer_seconds = 20 * 60
            st.session_state.tiempo_inicial = 20 * 60; st.session_state.modo_actual = "Pomodoro"; st.rerun()
    with col_m2:
        if st.button(f"Descanso {st.session_state.count_desc}", use_container_width=True):
            st.session_state.timer_running = False; st.session_state.timer_seconds = 5 * 60
            st.session_state.tiempo_inicial = 5 * 60; st.session_state.modo_actual = "Descanso"; st.rerun()
    with col_m3:
        if st.button(f"Descanso largo {st.session_state.count_largo}", use_container_width=True):
            st.session_state.timer_running = False; st.session_state.timer_seconds = 15 * 60
            st.session_state.tiempo_inicial = 15 * 60; st.session_state.modo_actual = "Descanso Largo"; st.rerun()

    # Reloj central
    mins, secs = divmod(st.session_state.timer_seconds, 60)
    st.markdown(f"""
        <div class="reloj-container">
            <div class="reloj-circulo">
                <p class="reloj-texto">{mins:02d}:{secs:02d}</p>
                <p class="reloj-nivel">Nivel</p>
                <p class="reloj-sub">Popular</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Botón Principal
    _, btn_col, _ = st.columns([1, 4, 1])
    with btn_col:
        texto_btn = "PAUSAR" if st.session_state.timer_running else "INICIAR"
        if st.button(texto_btn, type="primary", use_container_width=True):
            st.session_state.timer_running = not st.session_state.timer_running
            st.rerun()

    # Motor del reloj
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
        if st.button(f"💾 Guardar {mins_reales} Minutos", use_container_width=True):
            try:
                with conn.session as s:
                    s.execute(text("INSERT INTO pomodoros (asignatura, fecha, minutos_estudiados, tipo) VALUES (:a, :f, :m, :t)"), 
                              {"a": asig_log, "f": datetime.now().strftime('%Y-%m-%d'), "m": mins_reales, "t": "Pomodoro"})
                    s.commit()
                st.success(f"¡{mins_reales} minutos guardados!")
            except:
                st.error("No se pudo guardar. Revisa la conexión a Supabase.")
            st.session_state.timer_running = False; st.session_state.timer_seconds = 20 * 60; st.rerun()

# --- DEMÁS PESTAÑAS (Funcionalidad Supabase intacta) ---
with tab_recall:
    st.header("Repaso de hoy")
    hoy = datetime.now().strftime('%Y-%m-%d')
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
        if st.form_submit_button("Guardar Problema"):
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
    with col_d1:
        st.subheader("Tiempos Guardados")
        try: st.dataframe(conn.query("SELECT id, asignatura, minutos_estudiados FROM pomodoros"), use_container_width=True)
        except: pass
    with col_d2:
        st.subheader("Ejercicios")
        try: st.dataframe(conn.query("SELECT id, asignatura, ejercicio FROM ejercicios"), use_container_width=True)
        except: pass
