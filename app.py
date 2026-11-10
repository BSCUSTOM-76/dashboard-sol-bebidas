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

# --- BARRA LATERAL (LOGO, MENU E FILTROS) ---
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

fichs_pasta = os.listdir(pasta_dados)
caminho_pdf_pag = os.path.join(pasta_dados, "RELATÓRIO PREVISÃO DE PAGAMENTO.pdf")
caminho_excel_rec = os.path.join(pasta_dados, "Previsao_Recebimento_Analitico.xlsx")

for f in fichs_pasta:
    f_upper = f.upper()
    f_path = os.path.join(pasta_dados, f)
    if "PAGAMENTO" in f_upper:
        caminho_pdf_pag = f_path
    if "RECEBIMENTO" in f_upper and f_upper.endswith((".XLSX", ".XLS")):
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
    df["Data_Obj"] = pd.to_datetime(df["Vencimento"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Data_Obj"])
    df["Ano"] = df["Data_Obj"].dt.year
    df["Mes"] = df["Data_Obj"].dt.month
    return df, "Ok"

@st.cache_data
def processar_excel_receber(excel_path):
    if not excel_path or not os.path.exists(excel_path):
        return pd.DataFrame(), f"Ficheiro Excel não encontrado"
    try:
        df_raw = pd.read_excel(excel_path, header=0)
    except Exception as e:
        return pd.DataFrame(), str(e)
        
    if df_raw.empty:
        return pd.DataFrame(), "Ficheiro Excel vazio"
        
    registos = []
    for _, row in df_raw.iterrows():
        vals = list(row.values)
        if len(vals) < 2:
            continue
        val_data = vals[0]
        val_ent = vals[1] if len(vals) > 1 else "DIVERSOS"
        val_num = vals[-1] if len(vals) > 2 else 0.0
        
        if pd.isna(val_data):
            continue
            
        if isinstance(val_data, pd.Timestamp):
            data_obj = val_data
            vencimento_str = data_obj.strftime("%d/%m/%Y")
        else:
            dt_parse = pd.to_datetime(str(val_data), errors="coerce")
            if pd.isna(dt_parse):
                continue
            data_obj = dt_parse
            vencimento_str = data_obj.strftime("%d/%m/%Y")
            
        try:
            if isinstance(val_num, (int, float)):
                valor_float = float(val_num)
            else:
                v_limpo = str(val_num).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                valor_float = float(v_limpo)
        except:
            valor_float = 0.0
            
        entidade_str = str(val_ent).strip() if not pd.isna(val_ent) else "DIVERSOS"
        
        if valor_float > 0 and entidade_str.upper() not in ["CLIENTE", "VALOR", "VENCIMENTO", "NOME", "TOTAL"]:
            registos.append({"Vencimento": vencimento_str, "Entidade": entidade_str, "Valor": valor_float, "Data_Obj": data_obj})
            
    if not registos:
        return pd.DataFrame(), "Nenhum registo válido extraído do Excel"
        
    df = pd.DataFrame(registos)
    df = df.dropna(subset=["Data_Obj"])
    df["Ano"] = df["Data_Obj"].dt.year
    df["Mes"] = df["Data_Obj"].dt.month
    return df, "Ok"

# ==========================================
# MÓDULO 1: CONTAS A PAGAR
# ==========================================
if menu_escolha == "Contas a Pagar":
    st.markdown('<div class="titulo-customizado">Gestao de Contas a Pagar</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    df_p, msg_p = processar_relatorio(caminho_pdf_pag)
    
    if not df_p.empty:
        anos = sorted(df_p["Ano"].unique().tolist())
        ano_sel = st.sidebar.selectbox("Ano (Pagar)", anos, key="ap1")
        df_f = df_p[df_p["Ano"] == ano_sel]
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Periodo (Pagar)")
        min_dp = df_f["Data_Obj"].min().date() if not df_f.empty else pd.to_datetime("2026-01-01").date()
        max_dp = df_f["Data_Obj"].max().date() if not df_f.empty else pd.to_datetime("2026-12-31").date()
        
        periodo_p = st.sidebar.date_input("Intervalo de Datas", value=(min_dp, max_dp), format="DD/MM/YYYY", key="date_range_pag")
        
        if isinstance(periodo_p, tuple) and len(periodo_p) == 2:
            d_ini_p, d_fim_p = periodo_p
            df_f = df_f[(df_f["Data_Obj"].dt.date >= d_ini_p) & (df_f["Data_Obj"].dt.date <= d_fim_p)]

        val_total = f"R$ {df_f['Valor'].sum():,.2f}"
        qtd_reg = f"{len(df_f)}"
        maior_val = f"R$ {df_f['Valor'].max() if len(df_f)>0 else 0:,.2f}"
        media_val = f"R$ {df_f['Valor'].mean() if len(df_f)>0 else 0:,.2f}"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="card"><div class="metric-title">Total Previsto</div><div class="metric-value">{val_total}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card"><div class="metric-title">Registos</div><div class="metric-value">{qtd_reg}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card"><div class="metric-title">Maior Pagamento</div><div class="metric-value">{maior_val}</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="card"><div class="metric-title">Media</div><div class="metric-value">{media_val}</div></div>', unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Top 5 Fornecedores")
            df_top = df_f.groupby("Entidade")["Valor"].sum().nlargest(5)
            st.bar_chart(df_top)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_g2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Ranking Detalhado")
            df_forn_detalhe = df_f.groupby("Entidade")["Valor"].sum().nlargest(10).reset_index()
            df_forn_detalhe["Valor"] = df_forn_detalhe["Valor"].map("R$ {:,.2f}".format)
            st.dataframe(df_forn_detalhe, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Lista Detalhada de Pagamentos")
        df_tb = df_f[["Vencimento", "Entidade", "Valor"]].copy()
        df_tb.columns = ["Vencimento", "Fornecedor", "Valor"]
        df_tb["Valor"] = df_tb["Valor"].map("R$ {:,.2f}".format)
        st.dataframe(df_tb, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Pagamentos: {msg_p}")

# ==========================================
# MÓDULO 2: CONTAS A RECEBER
# ==========================================
elif menu_escolha == "Contas a Receber":
    st.markdown('<div class="titulo-customizado">Gestao de Contas a Receber</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    df_r, msg_r = processar_excel_receber(caminho_excel_rec)
    
    if not df_r.empty:
        anos_r = sorted(df_r["Ano"].unique().tolist())
        ano_sel_r = st.sidebar.selectbox("Ano (Receber)", anos_r, key="ar2")
        df_fr = df_r[df_r["Ano"] == ano_sel_r]
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("
