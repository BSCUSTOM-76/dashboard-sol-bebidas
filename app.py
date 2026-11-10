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

# Estilização CSS personalizada para o Dark Mode e Amarelo Corporativo
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

# --- SISTEMA DE AUTENTICACAO (LOGIN) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="login-card">
                <h2 style='color: #f0f6fc; text-align: center;'>Acesso Restrito</h2>
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
            
            if usuario_input in utilizadores_autorizados and utilizadores_autorizados[usuario_input] == senha_input:
                st.session_state["autenticado"] = True
                st.session_state["usuario_atual"] = usuario_input
                st.rerun()
            else:
                st.error("Utilizador ou palavra-passe incorretos.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- EXIBIR UTILIZADOR NO CANTO SUPERIOR DIREITO ---
usuario_logado = st.session_state.get('usuario_atual', 'Convidado')
st.markdown(f"""
    <div class="user-badge">
        <span>Utilizador:</span> <b>{usuario_logado}</b>
    </div>
""", unsafe_allow_html=True)

if "filtro_pag" not in st.session_state:
    st.session_state["filtro_pag"] = "todos"
if "filtro_rec" not in st.session_state:
    st.session_state["filtro_rec"] = "todos"

pasta_dados = os.getcwd()

# --- BARRA LATERAL ORGANIZADA ---
with st.sidebar:
    caminho_logo = os.path.join(pasta_dados, "logo.png")
    if os.path.exists(caminho_logo):
        try:
            st.image(caminho_logo, width=140)
        except:
            st.markdown("<h2 style='color: #f2cc0d;'>SOL BEBIDAS</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='color: #f2cc0d;'>SOL BEBIDAS</h2>", unsafe_allow_html=True)
    
    st.markdown("### Menu Executivo")
    menu_escolha = st.radio(
        "Selecione o Relatorio:",
        ["Contas a Pagar", "Contas a Receber"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.header("Filtros do Painel")

# Identificação de ficheiros
fichs_pasta = os.listdir(pasta_dados)
caminho_pdf_pag = os.path.join(pasta_dados, "RELATÓRIO PREVISÃO DE PAGAMENTO.pdf")
caminho_excel_rec = os.path.join(pasta_dados, "Previsao_Recebimento_Analitico.xlsx")

for f in fichs_pasta:
    f_upper = f.upper()
    f_path = os.path.join(pasta_dados, f)
    if "PAGAMENTO" in f_upper:
        caminho_pdf_pag = f_path
    if ("RECEBIMENTO" in f_upper or "ANALITICO" in f_upper) and f_upper.endswith((".XLSX", ".XLS")):
        caminho_excel_rec = f_path

def converter_valor(val_str):
    if not val_str:
        return 0.0
    if isinstance(val_str, (int, float)):
        return float(val_str)
    v = str(val_str).strip().replace("R$", "").replace(" ", "")
    if "," in v and "." in v:
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:
        v = v.replace(",", ".")
    try:
        return float(v)
    except:
        return 0.0

def formatar_br(valor):
    try:
        val_float = float(valor)
        s = f"{val_float:,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"
    except:
        return "R$ 0,00"

@st.cache_data
def processar_relatorio(pdf_path):
    if not pdf_path or not os.path.exists(pdf_path):
        return pd.DataFrame(), "Ficheiro PDF não encontrado"
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
        
    registos = []
    entidade_atual = "DIVERSOS"
    padrao_data = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')
    
    for i, linha in enumerate(linhas_texto):
        linha_upper = linha.upper()
        if any(k in linha_upper for k in ["FORNECEDOR", "FORN:", "CLIENTE", "CLIFOR:"]):
            partes = re.split(r'Fornecedor:|Forn:|Cliente:|Clifor:', linha, flags=re.IGNORECASE)
            if len(partes) > 1 and partes[1].strip():
                entidade_atual = partes[1].strip()
        datas = padrao_data.findall(linha)
        if datas:
            vencimento = datas[0]
            valores = re.findall(r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b', linha)
            if valores:
                valor_float = converter_valor(valores[-1])
                if valor_float > 0:
                    registos.append({"Vencimento": vencimento, "Entidade": entidade_atual, "Valor": valor_float})
                    
    if not registos:
        return pd.DataFrame(), "Nenhum valor extraído do PDF"
        
    df = pd.DataFrame(registos)
    df["Data_Obj"] = pd.to_datetime(df["Vencimento"], format="%d/%m
