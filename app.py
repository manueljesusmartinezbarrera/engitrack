import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE ESTILO ---
st.set_page_config(page_title="EngiTrack v3.1", layout="wide", page_icon="⏱️")

# CSS para forzar el diseño centrado y limpio
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
    
    /* Estilo para el botón INICIAR principal */
    .stButton > button.iniciar-btn {
        background-color: #1C64F2; color: white; border-radius: 30px; height: 60px;
        font-size: 20px; font-weight: bold; border: none; transition: 0.2s; width: 100%;
    }
    .stButton > button.iniciar-btn:hover { background-color: #1A56D1; color: white; }
    
    /* Estilo para los botones de modo superiores (para que parezcan pestañas) */
    .modo-btn > button {
        border: none; background: transparent; color: #6B7280; font-size: 16px; border-bottom: 2px solid transparent; border-radius: 0; padding: 10px 0;
    }
    .modo-btn > button:hover { border-bottom: 2px solid #1C64F2; color: #1C64F2; background: transparent; }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS LOCAL ---
conn = sqlite3.connect('engitrack_v3.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS ejercicios (id INTEGER PRIMARY KEY, asignatura TEXT, tema TEXT, ejercicio TEXT, dificultad TEXT, cuello_botella TEXT, fecha_registro DATE, fecha_repaso DATE, veces_repasado INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS pomodoros (id INTEGER PRIMARY KEY, asignatura TEXT, fecha DATE, minutos_estudiados INTEGER, tipo TEXT)')
conn.commit()

# --- ESTADO DE LA SESIÓN ---
if 'timer_seconds' not in st.session_state: 
    st.session_state.timer_seconds = 20 * 60
    st.session_state.tiempo_inicial = 20 * 60 # NUEVO: Para saber de dónde partimos
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
    # Usamos columnas para CENTRAR el diseño y que no se estire
    _, col_centro, _ = st.columns([1, 2, 1])
    
    with col_centro:
        # Selector de modo (Pestañas superiores)
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

        # Diseño del cronómetro circular
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

        # Botón INICIAR / PAUSAR centrado
        st.markdown('<div class="stButton">', unsafe_allow_html=True)
        texto_boton = "PAUSAR" if st.session_state.timer_running else "INICIAR"
        if st.button(texto_boton, key="btn_iniciar", help="iniciar-btn", use_container_width=True):
            st.session_state.timer_running = not st.session_state.timer_running
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Lógica de cuenta atrás
        if st.session_state.timer_running and st.session_state.timer_seconds > 0:
            time.sleep(1)
            st.session_state.timer_seconds -= 1
            st.rerun()
        elif st.session_state.timer_seconds <= 0 and st.session_state.timer_running:
            st.session_state.timer_running = False
            st.balloons()
            st.rerun()

        # Guardado DINÁMICO de tiempo (Solo en modo Pomodoro)
        if st.session_state.modo_actual == "Pomodoro":
            st.divider()
            # Calcular tiempo transcurrido matemáticamente
            segundos_transcurridos = st.session_state.tiempo_inicial - st.session_state.timer_seconds
            minutos_reales = max(1, segundos_transcurridos // 60) # Mínimo 1 minuto para que guarde algo
            
            asig_log = st.text_input("Asignatura a guardar:", "General")
            
            # El botón ahora muestra exactamente cuánto vas a guardar
            if st.button(f"💾 Guardar {minutos_reales} Minutos reales", use_container_width=True):
                c.execute("INSERT INTO pomodoros (asignatura, fecha, minutos_estudiados, tipo) VALUES (?, ?, ?, ?)", 
                          (asig_log, datetime.now().strftime('%Y-%m-%d'), minutos_reales, "Pomodoro"))
                conn.commit()
                st.success(f"¡{minutos_reales} minutos guardados en {asig_log}!")
                # Resetear cronómetro tras guardar
                st.session_state.timer_running = False
                st.session_state.timer_seconds = 20 * 60
                st.rerun()

# --- PESTAÑA ACTIVE RECALL ---
with tab_recall:
    st.header("Repaso de hoy")
    hoy = datetime.now().strftime('%Y-%m-%d')
    df_repaso = pd.read_sql_query(f"SELECT * FROM ejercicios WHERE fecha_repaso <= '{hoy}'", conn)
    if df_repaso.empty: st.success("¡Todo al día!")
    else:
        for _, row in df_repaso.iterrows():
            with st.expander(f"📌 {row['asignatura']} - {row['ejercicio']}"):
                st.markdown(f"**Cuello de botella:** {row['cuello_botella']}")
                cols = st.columns(4)
                for i, dif in enumerate(["Fácil", "Normal", "Difícil", "No pude"]):
                    if cols[i].button(dif, key=f"btn_{row['id']}_{dif}"):
                        nf = calcular_proximo_repaso(hoy, dif if dif != "No pude" else "No pude hacerlo", row['veces_repasado']+1)
                        c.execute("UPDATE ejercicios SET fecha_repaso=?, veces_repasado=? WHERE id=?", (nf, row['veces_repasado']+1, row['id']))
                        conn.commit(); st.rerun()

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
            c.execute("INSERT INTO ejercicios (asignatura, tema, ejercicio, dificultad, cuello_botella, fecha_registro, fecha_repaso, veces_repasado) VALUES (?,?,?,?,?,?,?,?)", 
                      (asig, tema, ejer, dif, botella, fr, pr, 0))
            conn.commit(); st.success(f"Registrado. Próximo repaso: {pr}")

# --- PESTAÑA GESTIÓN ---
with tab_data:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.subheader("Tiempos Guardados")
        st.dataframe(pd.read_sql_query("SELECT id, asignatura, minutos_estudiados FROM pomodoros", conn), use_container_width=True)
        id_borrar_pomo = st.number_input("ID de tiempo a borrar", min_value=0, step=1)
        if st.button("Borrar Tiempo") and id_borrar_pomo > 0:
            c.execute("DELETE FROM pomodoros WHERE id=?", (id_borrar_pomo,)); conn.commit(); st.rerun()
    with col_d2:
        st.subheader("Ejercicios")
        st.dataframe(pd.read_sql_query("SELECT id, asignatura, ejercicio FROM ejercicios", conn), use_container_width=True)
        id_borrar_ej = st.number_input("ID de ejercicio a borrar", min_value=0, step=1)
        if st.button("Borrar Ejercicio") and id_borrar_ej > 0:
            c.execute("DELETE FROM ejercicios WHERE id=?", (id_borrar_ej,)); conn.commit(); st.rerun()
