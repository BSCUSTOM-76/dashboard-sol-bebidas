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
        st.markdown('''
            <div class="login-card">
                <h2 style='color: #f0f6fc; text-align: center;'>🔐 Acesso Restrito</h2>
                <p style='color: #8b949e; text-align: center;'>Sol Bebidas - Financeiro</p>
        ''', unsafe_allow_html=True)
        
        usuario_input = st.text_input("Utilizador")
        senha_input = st.text_input("Palavra-passe", type="password")
        
        if st.button("Entrar no Sistema", use_container_width=True):
            utilizadores_autorizados = {
                "Bruno": "Sol@2024",
                "financeiro": "solbeb2026",
                "diretoria": "finan@sol",
                "Fabio": "sol@finan"
            }
            
            if usuario_input in utilizadores_autorizados and utilizadores_autorizados[usuario_input] == senha_input:
                st.session_state["autenticado"] = True
                st.session_state["usuario_atual"] = usuario_input
                st.rerun()
            else:
                st.error("⚠️ Utilizador ou palavra-passe incorretos.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- EXIBIR UTILIZADOR NO CANTO SUPERIOR DIREITO ---
usuario_logado = st.session_state.get('usuario_atual', 'Convidado')
st.markdown(f'''
    <div class="user-badge">
        <span>👤 Utilizador:</span> <b>{usuario_logado}</b>
    </div>
''', unsafe_allow_html=True)

# --- GESTÃO DE ESTADOS PARA FILTROS DOS CARTÕES ---
if "filtro_pag" not in st.session_state:
    st.session_state["filtro_pag"] = "todos"
if "filtro_rec" not in st.session_state:
    st.session_state["filtro_rec"] = "todos"

# --- DAQUI PARA BAIXO: DASHBOARD PROTEGIDO ---
pasta_dados = os.getcwd()

with st.sidebar:
    caminho_logo = os.path.join(pasta_dados, "logo.png")
    if os.path.exists(caminho_logo):
        try:
            st.image(caminho_logo, width=130)
        except:
            st.write("SOL")
    else:
        st.write("SOL")
    
    st.markdown("### 🗂️ Menu Executivo")
    menu_escolha = st.radio(
        "Selecione o Relatório:",
        ["Contas a Pagar", "Contas a Receber"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.header("🔍 Filtros do Painel")

caminho_pdf_pag = os.path.join(pasta_dados, "RELATÓRIO PREVISÃO DE PAGAMENTO.pdf")
caminho_pdf_rec = os.path.join(pasta_dados, "previsao_recebimentos.pdf")

fichs = os.listdir(pasta_dados)
for f in fichs:
    f_upper = f.upper()
    f_path = os.path.join(pasta_dados, f)
    if "RELATÓRIO PREVISÃO DE PAGAMENTO" in f_upper:
        caminho_pdf_pag = f_path
    if "PREVISAO_RECEBIMENTOS" in f_upper or "PREVISÃO_RECEBIMENTOS" in f_upper:
        caminho_pdf_rec = f_path

def converter_valor(val_str):
    if not val_str:
        return 0.0
    v = str(val_str).strip().replace(" ", "")
    if "," in v:
        v = v.replace(".", "").replace(",", ".")
    try:
        return float(v)
    except:
        return 0.0

@st.cache_data
def processar_relatorio(pdf_path, tipo="pagamento"):
    if not pdf_path or not os.path.exists(pdf_path):
        return pd.DataFrame(), "Ficheiro não encontrado"
    
    linhas_texto = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for pagina in pdf.pages:
                t = pagina.extract_text()
                if t:
                    for l in t.split("\n"):
                        linhas_texto.append(l.strip())
    except Exception as e:
        return pd.DataFrame(), str(e)
                    
    if not linhas_texto:
        return pd.DataFrame(), "PDF vazio ou ilegível"
        
    registos = []
    entidade_atual = "DIVERSOS"
    padrao_data = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
    
    for i, linha in enumerate(linhas_texto):
        linha_upper = linha.upper()
        if any(k in linha_upper for k in ["FORNECEDOR", "FORN:", "CLIENTE", "CLIFOR:"]):
          partes = re.split(r'Fornecedor:|Forn:|Cliente:|Clifor:', linha, flags=re.IGNORECASE)
