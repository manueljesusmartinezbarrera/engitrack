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
            st.markdown('<div class
