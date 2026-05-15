import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE ESTILO ---
st.set_page_config(page_title="EngiTrack v3.0", layout="wide", page_icon="⚙️")

# CSS personalizado para el cronómetro circular y botones
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; font-weight: bold; }
    .timer-text { font-size: 80px; font-weight: bold; text-align: center; color: #1E88E5; font-family: 'Courier New', monospace; }
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS ---
conn = sqlite3.connect('engitrack_v3.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS ejercicios (id INTEGER PRIMARY KEY, asignatura TEXT, tema TEXT, ejercicio TEXT, dificultad TEXT, cuello_botella TEXT, fecha_registro DATE, fecha_repaso DATE, veces_repasado INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS pomodoros (id INTEGER PRIMARY KEY, asignatura TEXT, fecha DATE, minutos_estudiados INTEGER, tipo TEXT)')
conn.commit()

# --- ESTADO DE LA SESIÓN ---
if 'timer_seconds' not in st.session_state: st.session_state.timer_seconds = 20 * 60
if 'timer_running' not in st.session_state: st.session_state.timer_running = False
if 'last_run' not in st.session_state: st.session_state.last_run = time.time()

# --- LÓGICA DE REPASO ---
def calcular_proximo_repaso(fecha_base, dificultad, veces_repasado):
    dias = {"Fácil": 7, "Normal": 3, "Difícil": 1, "No pude hacerlo": 0}[dificultad] * (1.5 ** veces_repasado)
    if dias == 0: dias = 1
    return (datetime.strptime(fecha_base, '%Y-%m-%d') + timedelta(days=int(dias))).strftime('%Y-%m-%d')

# --- INTERFAZ ---
tab_recall, tab_reg, tab_pomo, tab_data = st.tabs(["🧠 Active Recall", "➕ Registro", "⏱️ Pomodoro 20/5", "📊 Historial y Gestión"])

# --- PESTAÑA POMODORO (Novedad v3) ---
with tab_pomo:
    st.header("⏱️ Cronómetro de Estudio")
    
    # Selector de Modo (Como en tu imagen)
    modo = st.radio("Selecciona modo:", ["Pomodoro (20m)", "Descanso (5m)", "Descanso Largo (15m)"], horizontal=True)
    
    # Ajustar tiempo según modo si el timer no está corriendo
    if not st.session_state.timer_running:
        if modo == "Pomodoro (20m)": st.session_state.timer_seconds = 20 * 60
        elif modo == "Descanso (5m)": st.session_state.timer_seconds = 5 * 60
        else: st.session_state.timer_seconds = 15 * 60

    # Mostrar Cronómetro
    mins, secs = divmod(st.session_state.timer_seconds, 60)
    st.markdown(f"<p class='timer-text'>{mins:02d}:{secs:02d}</p>", unsafe_allow_html=True)

    col_p1, col_p2, col_p3 = st.columns([1,1,1])
    
    with col_p1:
        if st.button("▶️ INICIAR" if not st.session_state.timer_running else "⏸️ PAUSAR"):
            st.session_state.timer_running = not st.session_state.timer_running
            st.rerun()
            
    with col_p2:
        if st.button("🔄 REINICIAR"):
            st.session_state.timer_running = False
            st.rerun()

    # Lógica de cuenta atrás (solo si está activo)
    if st.session_state.timer_running and st.session_state.timer_seconds > 0:
        time.sleep(1)
        st.session_state.timer_seconds -= 1
        st.rerun()
    elif st.session_state.timer_seconds == 0 and st.session_state.timer_running:
        st.session_state.timer_running = False
        st.balloons()
        if modo == "Pomodoro (20m)":
            st.success("¡Ciclo completado! No olvides guardar tu progreso abajo.")
        else:
            st.info("Descanso terminado. ¡A por otro ciclo!")

    # Guardar tiempo (Solo para modo Pomodoro)
    if modo == "Pomodoro (20m)":
        st.divider()
        asigs = pd.read_sql_query("SELECT DISTINCT asignatura FROM ejercicios", conn)
        lista_asig = asigs['asignatura'].tolist() if not asigs.empty else ["General"]
        asig_log = st.selectbox("Asignatura a la que asignar este tiempo:", lista_asig)
        
        if st.button("💾 GUARDAR SESIÓN (20 MIN)"):
            c.execute("INSERT INTO pomodoros (asignatura, fecha, minutos_estudiados, tipo) VALUES (?, ?, ?, ?)", 
                      (asig_log, datetime.now().strftime('%Y-%m-%d'), 20, "Pomodoro"))
            conn.commit()
            st.success(f"Guardados 20 minutos para {asig_log}")

# --- PESTAÑA GESTIÓN (Borrado de tiempos) ---
with tab_data:
    st.header("Gestión de Datos y Tiempos")
    
    col_stat1, col_stat2 = st.columns(2)
    
    with col_stat1:
        st.subheader("Historial de Pomodoros")
        df_pomo = pd.read_sql_query("SELECT id, asignatura, fecha, minutos_estudiados FROM pomodoros ORDER BY id DESC", conn)
        st.dataframe(df_pomo, use_container_width=True)
        
        # BORRAR TIEMPO SI TE EQUIVOCAS
        st.warning("🗑️ Borrar tiempo erróneo")
        id_borrar_pomo = st.number_input("ID del pomodoro a eliminar", min_value=1, step=1)
        if st.button("Eliminar Registro de Tiempo"):
            c.execute("DELETE FROM pomodoros WHERE id=?", (id_borrar_pomo,))
            conn.commit()
            st.success(f"Registro {id_borrar_pomo} eliminado.")
            st.rerun()

    with col_stat2:
        st.subheader("Ejercicios Registrados")
        df_ej = pd.read_sql_query("SELECT id, asignatura, ejercicio, dificultad FROM ejercicios", conn)
        st.dataframe(df_ej, use_container_width=True)
        
        # BORRAR EJERCICIO
        st.warning("🗑️ Borrar ejercicio")
        id_borrar_ej = st.number_input("ID del ejercicio a eliminar", min_value=1, step=1)
        if st.button("Eliminar Ejercicio"):
            c.execute("DELETE FROM ejercicios WHERE id=?", (id_borrar_ej,))
            conn.commit()
            st.success(f"Ejercicio {id_borrar_ej} eliminado.")
            st.rerun()

# --- PESTAÑAS ORIGINALES (Mantenidas y mejoradas) ---
with tab_recall:
    st.header("Active Recall")
    hoy = datetime.now().strftime('%Y-%m-%d')
    df_repaso = pd.read_sql_query(f"SELECT * FROM ejercicios WHERE fecha_repaso <= '{hoy}'", conn)
    if df_repaso.empty: st.success("¡Todo repasado!")
    else:
        for _, row in df_repaso.iterrows():
            with st.expander(f"📌 {row['asignatura']} - {row['ejercicio']}"):
                st.markdown(f"**Atención:** {row['cuello_botella']}")
                cols = st.columns(4)
                for i, dif in enumerate(["Fácil", "Normal", "Difícil", "No pude"]):
                    if cols[i].button(dif, key=f"btn_{row['id']}_{dif}"):
                        nf = calcular_proximo_repaso(hoy, dif if dif != "No pude" else "No pude hacerlo", row['veces_repasado']+1)
                        c.execute("UPDATE ejercicios SET fecha_repaso=?, veces_repasado=? WHERE id=?", (nf, row['veces_repasado']+1, row['id']))
                        conn.commit(); st.rerun()

with tab_reg:
    st.header("Nuevo Registro")
    with st.form("reg"):
        ca, cb = st.columns(2)
        asig = ca.text_input("Asignatura")
        tema = ca.text_input("Tema")
        ejer = cb.text_input("ID Ejercicio")
        dif = cb.selectbox("Dificultad", ["Fácil", "Normal", "Difícil", "No pude hacerlo"])
        botella = st.text_area("Cuello de botella (LaTeX permitido: $...$)")
        if st.form_submit_button("Guardar"):
            fr = datetime.now().strftime('%Y-%m-%d')
            pr = calcular_proximo_repaso(fr, dif, 0)
            c.execute("INSERT INTO ejercicios (asignatura, tema, ejercicio, dificultad, cuello_botella, fecha_registro, fecha_repaso, veces_repasado) VALUES (?,?,?,?,?,?,?,?)", 
                      (asig, tema, ejer, dif, botella, fr, pr, 0))
            conn.commit(); st.success(f"Toca repasar el {pr}")

### Mejoras clave en esta versión:
1.  **Triple Modo:** Tienes los botones de Pomodoro (20), Descanso (5) y Descanso Largo (15) que cambian el reloj automáticamente.
2.  **Cronómetro Dinámico:** El reloj ahora descuenta los segundos en tiempo real en la pantalla.
3.  **Gestión de Errores:** En la pestaña **"Historial y Gestión"**, puedes ver los IDs de cada vez que guardaste tiempo y borrarlos individualmente si te equivocaste de asignatura.
4.  **Guardado Manual:** Para que el tiempo sea real, el botón de "Guardar Sesión" aparece solo cuando quieres registrar esos 20 minutos en tu estadística.

¿Te gustaría que ahora pasemos a conectarla a **Supabase** para que esto mismo funcione sincronizado en tu móvil?