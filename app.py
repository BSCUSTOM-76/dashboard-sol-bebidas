import os
import re
import pandas as pd
import pdfplumber
import streamlit as st

st.set_page_config(
    page_title="Dashboard Financeiro Executivo - Sol Bebidas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS personalizada para o Dark Mode, Amarelo Corporativo e Utilizador no Topo Direito
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-top: 3px solid #f2cc0d;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .metric-title {
        color: #f2cc0d;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        color: #f0f6fc;
        font-size: 26px;
        font-weight: 700;
        margin-top: 5px;
    }
    .titulo-customizado {
        color: #f0f6fc;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .login-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-top: 3px solid #f2cc0d;
        padding: 30px;
        border-radius: 10px;
        max-width: 400px;
        margin: 80px auto;
    }
    .user-badge {
        position: fixed;
        top: 15px;
        right: 80px;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 3px solid #f2cc0d;
        padding: 5px 15px;
        border-radius: 20px;
        color: #f0f6fc;
        font-size: 13px;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE AUTENTICAÇÃO (LOGIN) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="login-card">
                <h2 style='color: #f0f6fc; text-align: center;'>🔐 Acesso Restrito</h2>
                <p style='color: #8b949e; text-align: center;'>Sol Bebidas - Financeiro</p>
        """, unsafe_allow_html=True)
        
        usuario_input = st.text_input("Utilizador")
        senha_input = st.text_input("Palavra-passe", type="password")
        
        if st.button("Entrar no Sistema", use_container_width=True):
            utilizadores_autorizados = {
                "Bruno": "Sol@2024",
                "Clezio": "fin@2026",
                "diretoria": "finan@sol",
                "Fabio": "sol@finan"
            }
            
            if usuario_input in utilizadores_autorizados and utilizadores_
