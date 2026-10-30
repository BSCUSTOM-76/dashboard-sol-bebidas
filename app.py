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
                "Clezio": "fin@2026",
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
            if len(partes) > 1 and partes[1].strip():
                entidade_atual = partes[1].strip()
            elif i + 1 < len(linhas_texto):
                entidade_atual = linhas_texto[i+1].strip()
        elif tipo == "pagamento" and " - " in linha and not padrao_data.search(linha):
            if len(linha) > 5 and not any(term in linha_upper for term in ["TOTAL", "SAIBWEB", "EMISSÃO"]):
                entidade_atual = linha.strip()
        elif tipo == "recebimento" and len(linha) > 3 and not padrao_data.search(linha) and not any(term in linha_upper for term in ["TOTAL", "SAIBWEB", "EMISSÃO", "PÁGINA"]):
            if any(char.isdigit() for char in linha[:3]) and "-" in linha:
                entidade_atual = linha.strip()

        if any(termo in linha_upper for termo in ["TOTAL GERAL", "TOTAL", "SAIBWEB", "EMISSÃO:", "PÁGINA:", "USUÁRIO:"]):
            continue
            
        datas = padrao_data.findall(linha)
        if datas:
            vencimento = datas[0]
            valores = re.findall(r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b', linha)
            if valores:
                valor_float = converter_valor(valores[-1])
                if valor_float > 0:
                    registos.append({
                        "Vencimento": vencimento,
                        "Entidade": entidade_atual,
                        "Valor": valor_float
                    })

    if not registos:
        for linha in linhas_texto:
            datas = padrao_data.findall(linha)
            if datas:
                vencimento = datas[0]
                valores = re.findall(r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b', linha)
                if valores:
                    valor_float = converter_valor(valores[-1])
                    if valor_float > 0:
                        registos.append({
                            "Vencimento": vencimento,
                            "Entidade": "DIVERSOS",
                            "Valor": valor_float
                        })

    if not registos:
        return pd.DataFrame(), "Nenhum valor/data extraído"
        
    df = pd.DataFrame(registos)
    df["Data_Obj"] = pd.to_datetime(df["Vencimento"], format="%d/%m/%Y", errors="coerce")
    df = df[df["Data_Obj"] >= "01-01-2026"].dropna(subset=["Data_Obj"])
    df["Ano"] = df["Data_Obj"].dt.year
    df["Mes"] = df["Data_Obj"].dt.month
    return df, "Ok"

meses_nomes = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
               7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

# ==========================================
# MÓDULO 1: CONTAS A PAGAR
# ==========================================
if menu_escolha == "Contas a Pagar":
    st.markdown('<div class="titulo-customizado">Gestão de Contas a Pagar</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    df_p, msg_p = processar_relatorio(caminho_pdf_pag, "pagamento")
    
    if not df_p.empty:
        anos = sorted(df_p["Ano"].unique().tolist())
        ano_sel = st.sidebar.selectbox("Ano (Pagar)", anos, key="ap1")
        df_f = df_p[df_p["Ano"] == ano_sel]
        
        # Filtro por Período Personalizado (Data Inicial e Final) na Sidebar
        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 Período (Pagar)")
        min_dp = df_f["Data_Obj"].min().date() if not df_f.empty else pd.to_datetime("01-01-2026").date()
        max_dp = df_f["Data_Obj"].max().date() if not df_f.empty else pd.to_datetime("31-12-2026").date()
        
       periodo_p = st.sidebar.date_input("Intervalo de Datas", value=(min_dp, max_dp), format="DD/MM/YYYY", key="date_range_pag")
        
        if isinstance(periodo_p, tuple):
            if len(periodo_p) == 2:
                d_ini_p, d_fim_p = periodo_p
                df_f = df_f[(df_f["Data_Obj"].dt.date >= d_ini_p) & (df_f["Data_Obj"].dt.date <= d_fim_p)]
            elif len(periodo_p) == 1:
                d_ini_p = periodo_p[0]
                df_f = df_f[df_f["Data_Obj"].dt.date == d_ini_p]

        val_total = f"R$ {df_f['Valor'].sum():,.2f}"
        qtd_reg = f"{len(df_f)}"
        maior_val = f"R$ {df_f['Valor'].max() if len(df_f)>0 else 0:,.2f}"
        media_val = f"R$ {df_f['Valor'].mean() if len(df_f)>0 else 0:,.2f}"

        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown(f'''<div class="card"><div class="metric-title">💰 Total Previsto</div><div class="metric-value">{val_total}</div></div>''', unsafe_allow_html=True)
            if st.button("🔄 Ver Todos", use_container_width=True, key="b_todos_p"):
                st.session_state["filtro_pag"] = "todos"
                st.rerun()
                
        with c2:
            st.markdown(f'''<div class="card"><div class="metric-title">📋 Registos</div><div class="metric-value">{qtd_reg}</div></div>''', unsafe_allow_html=True)
            if st.button("📋 Ver Lista Completa", use_container_width=True, key="b_reg_p"):
                st.session_state["filtro_pag"] = "todos"
                st.rerun()
                
        with c3:
            st.markdown(f'''<div class="card"><div class="metric-title">📈 Maior Pagamento</div><div class="metric-value">{maior_val}</div></div>''', unsafe_allow_html=True)
            if st.button("🔍 Ver Maior Valor", use_container_width=True, key="b_maior_p"):
                st.session_state["filtro_pag"] = "maior"
                st.rerun()
                
        with c4:
            st.markdown(f'''<div class="card"><div class="metric-title">📊 Média</div><div class="metric-value">{media_val}</div></div>''', unsafe_allow_html=True)
            if st.button("📊 Acima da Média", use_container_width=True, key="b_media_p"):
                st.session_state["filtro_pag"] = "acima_media"
                st.rerun()

        df_tabela_pag = df_f.copy()
        if st.session_state["filtro_pag"] == "maior" and len(df_f) > 0:
            max_v = df_f["Valor"].max()
            df_tabela_pag = df_f[df_f["Valor"] == max_v]
            st.info("ℹ️ A exibir apenas o registo com o **Maior Pagamento**.")
        elif st.session_state["filtro_pag"] == "acima_media" and len(df_f) > 0:
            med_v = df_f["Valor"].mean()
            df_tabela_pag = df_f[df_f["Valor"] > med_v]
            st.info("ℹ️ A exibir apenas os registos com valores **acima da média**.")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📊 Top 5 Fornecedores (Valores)")
            df_top = df_f.groupby("Entidade")["Valor"].sum().nlargest(5)
            st.bar_chart(df_top)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_g2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📋 Ranking Detalhado de Fornecedores")
            df_forn_detalhe = df_f.groupby("Entidade")["Valor"].sum().nlargest(10).reset_index()
            df_forn_detalhe["Valor"] = df_forn_detalhe["Valor"].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(df_forn_detalhe, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 Evolução Temporal de Pagamentos")
        d_d = df_f.groupby("Vencimento")["Valor"].sum().reset_index()
        d_d["DT"] = pd.to_datetime(d_d["Vencimento"], format="%d/%m/%Y")
        st.line_chart(d_d.sort_values("DT").set_index("Vencimento")["Valor"])
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📋 Lista Detalhada de Pagamentos")
        df_tb = df_tabela_pag[["Vencimento", "Entidade", "Valor"]].copy()
        df_tb.columns = ["Vencimento", "Fornecedor", "Valor"]
        df_tb["Valor"] = df_tb["Valor"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_tb, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Pagamentos - Ficheiro: '{os.path.basename(caminho_pdf_pag)}' | Estado: {msg_p}")

# ==========================================
# MÓDULO 2: CONTAS A RECEBER
# ==========================================
elif menu_escolha == "Contas a Receber":
    st.markdown('<div class="titulo-customizado">Gestão de Contas a Receber</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    df_r, msg_r = processar_relatorio(caminho_pdf_rec, "recebimento")
    
    if not df_r.empty:
        anos_r = sorted(df_r["Ano"].unique().tolist())
        ano_sel_r = st.sidebar.selectbox("Ano (Receber)", anos_r, key="ar2")
        df_fr = df_r[df_r["Ano"] == ano_sel_r]
        
        # Filtro por Período Personalizado (Data Inicial e Final) na Sidebar
        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 Período (Receber)")
        min_dr = df_fr["Data_Obj"].min().date() if not df_fr.empty else pd.to_datetime("01-01-2026").date()
        max_dr = df_fr["Data_Obj"].max().date() if not df_fr.empty else pd.to_datetime("31-12-2026").date()
        
        periodo_r = st.sidebar.date_input("Intervalo de Datas", value=(min_dr, max_dr), format="DD/MM/YYYY", key="date_range_rec")
        
        if isinstance(periodo_r, tuple):
            if len(periodo_r) == 2:
                d_ini_r, d_fim_r = periodo_r
                df_fr = df_fr[(df_fr["Data_Obj"].dt.date >= d_ini_r) & (df_fr["Data_Obj"].dt.date <= d_fim_r)]
            elif len(periodo_r) == 1:
                d_ini_r = periodo_r[0]
                df_fr = df_fr[df_fr["Data_Obj"].dt.date == d_ini_r]

        val_total_r = f"R$ {df_fr['Valor'].sum():,.2f}"
        qtd_reg_r = f"{len(df_fr)}"
        maior_val_r = f"R$ {df_fr['Valor'].max() if len(df_fr)>0 else 0:,.2f}"
        media_val_r = f"R$ {df_fr['Valor'].mean() if len(df_fr)>0 else 0:,.2f}"

        cr1, cr2, cr3, cr4 = st.columns(4)
        
        with cr1:
            st.markdown(f'''<div class="card"><div class="metric-title">💰 Total a Receber</div><div class="metric-value">{val_total_r}</div></div>''', unsafe_allow_html=True)
            if st.button("🔄 Ver Todos", use_container_width=True, key="b_todos_r"):
                st.session_state["filtro_rec"] = "todos"
                st.rerun()
                
        with cr2:
            st.markdown(f'''<div class="card"><div class="metric-title">📋 Registos</div><div class="metric-value">{qtd_reg_r}</div></div>''', unsafe_allow_html=True)
            if st.button("📋 Ver Lista Completa", use_container_width=True, key="b_reg_r"):
                st.session_state["filtro_rec"] = "todos"
                st.rerun()
                
        with cr3:
            st.markdown(f'''<div class="card"><div class="metric-title">📈 Maior Recebimento</div><div class="metric-value">{maior_val_r}</div></div>''', unsafe_allow_html=True)
            if st.button("🔍 Ver Maior Valor", use_container_width=True, key="b_maior_r"):
                st.session_state["filtro_rec"] = "maior"
                st.rerun()
                
        with cr4:
            st.markdown(f'''<div class="card"><div class="metric-title">📊 Média</div><div class="metric-value">{media_val_r}</div></div>''', unsafe_allow_html=True)
            if st.button("📊 Acima da Média", use_container_width=True, key="b_media_r"):
                st.session_state["filtro_rec"] = "acima_media"
                st.rerun()

        # --- SELETOR E TOTAL POR DIA (CONTAS A RECEBER) ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📅 Total e Filtro por Dia de Vencimento")
        
        df_por_dia = df_fr.groupby("Vencimento")["Valor"].agg(['sum', 'count']).reset_index()
        df_por_dia["DT_Aux"] = pd.to_datetime(df_por_dia["Vencimento"], format="%d/%m/%Y", errors="coerce")
        df_por_dia = df_por_dia.sort_values("DT_Aux")
        
        opcoes_dias = ["Todos os Dias"] + [f"{row['Vencimento']} — Total: R$ {row['sum']:,.2f}" for _, row in df_por_dia.iterrows()]
        dia_selecionado = st.selectbox("Selecione um dia específico para filtrar:", opcoes_dias, key="sel_dia_rec")
        st.markdown('</div>', unsafe_allow_html=True)

        df_tabela_rec = df_fr.copy()
        
        if dia_selecionado != "Todos os Dias":
            data_escolhida = dia_selecionado.split(" — ")[0]
            df_tabela_rec = df_fr[df_fr["Vencimento"] == data_escolhida]
            st.info(f"ℹ️ A exibir apenas os recebimentos do dia **{data_escolhida}**.")
        elif st.session_state["filtro_rec"] == "maior" and len(df_fr) > 0:
            max_vr = df_fr["Valor"].max()
            df_tabela_rec = df_fr[df_fr["Valor"] == max_vr]
            st.info("ℹ️ A exibir apenas o registo com o **Maior Recebimento**.")
        elif st.session_state["filtro_rec"] == "acima_media" and len(df_fr) > 0:
            med_vr = df_fr["Valor"].mean()
            df_tabela_rec = df_fr[df_fr["Valor"] > med_vr]
            st.info("ℹ️ A exibir apenas os registos com valores **acima da média**.")

        col_gr1, col_gr2 = st.columns(2)
        with col_gr1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📊 Top 5 Clientes (Valores)")
            df_top_cli = df_fr.groupby("Entidade")["Valor"].sum().nlargest(5)
            st.bar_chart(df_top_cli)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_gr2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📋 Ranking Detalhado de Clientes")
            df_cli_detalhe = df_fr.groupby("Entidade")["Valor"].sum().nlargest(10).reset_index()
            df_cli_detalhe["Valor"] = df_cli_detalhe["Valor"].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(df_cli_detalhe, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 Evolução Temporal de Recebimentos")
        d_dr = df_fr.groupby("Vencimento")["Valor"].sum().reset_index()
        d_dr["DT"] = pd.to_datetime(d_dr["Vencimento"], format="%d/%m/%Y")
        st.line_chart(d_dr.sort_values("DT").set_index("Vencimento")["Valor"])
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📋 Lista Detalhada de Recebimentos")
        df_tbr = df_tabela_rec[["Vencimento", "Entidade", "Valor"]].copy()
        df_tbr.columns = ["Vencimento", "Cliente", "Valor"]
        df_tbr["Valor"] = df_tbr["Valor"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_tbr, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Recebimentos - Ficheiro: '{os.path.basename(caminho_pdf_rec) if caminho_pdf_rec else 'Nenhum'}' | Estado: {msg_r}")

# --- ASSINATURA NO RODAPÉ ESQUERDO DA BARRA LATERAL ---
with st.sidebar:
    st.markdown("<br>" * 4, unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #30363d;'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: left; color: #f2cc0d; font-size: 13px;'>Desenvolvedor:<br><b>Bruno Sabanelli</b></div>", unsafe_allow_html=True)
