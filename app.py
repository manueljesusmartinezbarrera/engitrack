import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from sqlalchemy import text

# --- CONFIGURACIÓN DE ESTILO ---
st.set_page_config(page_title="EngiTrack Cloud", layout="wide", page_icon="⏱️")

st.markdown("""
<style>
    .reloj-container { display: flex; justify-content: center; align-items: center; flex-direction: column; margin: 30px 0; }
    .reloj-circulo {
        border: 3px solid #E5E7EB; border-radius: 50%; width: 350px; height: 350px;
        display: flex; justify-content: center; align-items: center; flex-direction: column;
        background-color: transparent; 
    }
    .reloj-texto { font-size: 90px; color: #1C64F2; font-weight: 400; margin: 0; line-height: 1.1; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .reloj-nivel { font-size: 16px; color: #6B7280; margin-top: 5px; margin-bottom: 0;}
    .reloj-sub { font-size: 16px; color: #1C64F2; font-weight: bold; margin-top: 0;}
    .stButton > button.iniciar-btn {
        background-color: #1C64F2; color: white; border-radius: 30px; height: 60px;
        font-size: 20px; font-weight: bold; border: none; transition: 0.2s; width: 100%;
    }
    .stButton > button.iniciar-btn:hover { background-color: #1A56D1; color: white; }
    .modo-btn > button {
        border: none; background: transparent; color: #6B7280; font-size: 16px; border-bottom: 2px solid transparent; border-radius: 0; padding: 10px 0;
    }
    .modo-btn > button:hover { border-bottom: 2px solid #1C64F2; color: #1C64F2; background: transparent; }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS EN LA NUBE (SUPABASE) ---
conn = st.connection("engidb", type="sql")

with conn.session as s:
    s.execute(text('''
        CREATE TABLE IF NOT EXISTS ejercicios (
            id SERIAL PRIMARY KEY, 
            asignatura TEXT, tema TEXT, ejercicio TEXT, dificultad TEXT, 
            cuello_botella TEXT, fecha_registro DATE, fecha_repaso DATE, veces_repasado INTEGER
        )
    '''))
    s.execute(text('''
        CREATE TABLE IF NOT EXISTS pomodoros (
            id SERIAL PRIMARY KEY, 
            asignatura TEXT, fecha DATE, minutos_estudiados INTEGER, tipo TEXT
        )
    '''))
    s.commit()

# --- ESTADO DE LA SESIÓN ---
if 'timer_seconds' not in st.session_state: 
    st.session_state.timer_seconds = 20 * 60
    st.session_state.tiempo_inicial = 20 * 60
if 'timer_running' not in st.session_state: st.session_state.timer_running = False
if 'modo_actual' not in st.session_state: st.session_state.modo_actual = "Pomodoro"

def calcular_proximo_repaso(fecha_base, dificultad, veces_repasado):
    dias = {"Fácil": 7, "Normal": 3, "Difícil": 1, "No pude hacerlo": 0}[dificultad] * (1.5 ** veces_repasado)
    if dias == 0: dias = 1
    return (datetime.strptime(fecha_base, '%Y-%m-%d') + timedelta(days=int(dias))).strftime('%Y-%m-%d')

# --- INTERFAZ ---
tab_pomo, tab_recall, tab_reg, tab_data = st.tabs(["⏱️ Foco", "🧠 Active Recall", "➕ Registro", "📊 Gestión"])

# --- PESTAÑA POMODORO ---
with tab_pomo:
    _, col_centro, _ = st.columns([1, 2, 1])
    with col_centro:
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown('<div class="modo-btn">', unsafe_allow_html=True)
            if st.button("Pomodoro 20", use_container_width=True):
                st.session_state.timer_running = False
                st.session_state.timer_seconds = 20 * 60
                st.session_state.tiempo_inicial = 20 * 60
                st.session_state.modo_actual = "Pomodoro"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown('<div class="modo-btn">', unsafe_allow_html=True)
            if st.button("Descanso 5", use_container_width=True):
                st.session_state.timer_running = False
                st.session_state.timer_seconds = 5 * 60
                st.session_state.tiempo_inicial = 5 * 60
                st.session_state.modo_actual = "Descanso"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown('<div class="modo-btn">', unsafe_allow_html=True)
            if st.button("Descanso largo 15", use_container_width=True):
                st.session_state.timer_running = False
                st.session_state.timer_seconds = 15 * 60
                st.session_state.tiempo_inicial = 15 * 60
                st.session_state.modo_actual = "Descanso Largo"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        mins, secs = divmod(st.session_state.timer_seconds, 60)
        st.markdown(f"""
            <div class="reloj-container">
                <div class="reloj-circulo">
                    <p class="reloj-texto">{mins:02d}:{secs:02d}</p>
                    <p class="reloj-nivel">Nivel</p>
                    <p class="reloj-sub">Ingeniería</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="stButton">', unsafe_allow_html=True)
        if st.button("PAUSAR" if st.session_state.timer_running else "INICIAR", key="btn_iniciar", use_container_width=True):
            st.session_state.timer_running = not st.session_state.timer_running
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.timer_running and st.session_state.timer_seconds > 0:
            time.sleep(1)
            st.session_state.timer_seconds -= 1
            st.rerun()
        elif st.session_state.timer_seconds <= 0 and st.session_state.timer_running:
            st.session_state.timer_running = False
            st.balloons()
            st.rerun()

        if st.session_state.modo_actual == "Pomodoro":
            st.divider()
            segundos_transcurridos = st.session_state.tiempo_inicial - st.session_state.timer_seconds
            minutos_reales = max(1, segundos_transcurridos // 60)
            
            asig_log = st.text_input("Asignatura a guardar:", "General")
            
            if st.button(f"💾 Guardar {minutos_reales} Minutos", use_container_width=True):
                with conn.session as s:
                    s.execute(text("INSERT INTO pomodoros (asignatura, fecha, minutos_estudiados, tipo) VALUES (:asig, :f, :m, :t)"), 
                              {"asig": asig_log, "f": datetime.now().strftime('%Y-%m-%d'), "m": minutos_reales, "t": "Pomodoro"})
                    s.commit()
                st.success(f"¡{minutos_reales} minutos guardados!")
                st.session_state.timer_running = False
                st.session_state.timer_seconds = 20 * 60
                st.rerun()

# --- PESTAÑA ACTIVE RECALL ---
with tab_recall:
    st.header("Repaso de hoy")
    hoy = datetime.now().strftime('%Y-%m-%d')
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
                            s.execute(text("UPDATE ejercicios SET fecha_repaso=:nf, veces_repasado=:vr WHERE id=:id"),
                                      {"nf": nf, "vr": row['veces_repasado']+1, "id": row['id']})
                            s.commit()
                        st.rerun()

# --- PESTAÑA REGISTRO ---
with tab_reg:
    st.header("Nuevo Problema")
    with st.form("reg"):
        ca, cb = st.columns(2)
        asig = ca.text_input("Asignatura")
        tema = ca.text_input("Tema")
        ejer = cb.text_input("ID Ejercicio")
        dif = cb.selectbox("Dificultad", ["Fácil", "Normal", "Difícil", "No pude hacerlo"])
        botella = st.text_area("Cuello de botella (Usa $ para fórmulas, ej: $F=ma$)")
        if st.form_submit_button("Guardar Problema"):
            fr = datetime.now().strftime('%Y-%m-%d')
            pr = calcular_proximo_repaso(fr, dif, 0)
            with conn.session as s:
                s.execute(text("INSERT INTO ejercicios (asignatura, tema, ejercicio, dificultad, cuello_botella, fecha_registro, fecha_repaso, veces_repasado) VALUES (:a, :t, :e, :d, :c, :fr, :pr, :vr)"),
                          {"a": asig, "t": tema, "e": ejer, "d": dif, "c": botella, "fr": fr, "pr": pr, "vr": 0})
                s.commit()
            st.success(f"Registrado. Próximo repaso: {pr}")

# --- PESTAÑA GESTIÓN ---
with tab_data:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.subheader("Tiempos Guardados")
        st.dataframe(conn.query("SELECT id, asignatura, minutos_estudiados FROM pomodoros"), use_container_width=True)
        id_borrar_pomo = st.number_input("ID de tiempo a borrar", min_value=0, step=1)
        if st.button("Borrar Tiempo") and id_borrar_pomo > 0:
            with conn.session as s:
                s.execute(text("DELETE FROM pomodoros WHERE id=:id"), {"id": id_borrar_pomo})
                s.commit()
            st.rerun()
    with col_d2:
        st.subheader("Ejercicios")
        st.dataframe(conn.query("SELECT id, asignatura, ejercicio FROM ejercicios"), use_container_width=True)
        id_borrar_ej = st.number_input("ID de ejercicio a borrar", min_value=0, step=1)
        if st.button("Borrar Ejercicio") and id_borrar_ej > 0:
            with conn.session as s:
                s.execute(text("DELETE FROM ejercicios WHERE id=:id"), {"id": id_borrar_ej})
                s.commit()
            st.rerun()
