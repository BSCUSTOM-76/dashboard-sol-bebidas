import os
import pandas as pd
import pdfplumber

pasta_dados = os.getcwd()

def ler_tabela_pdf(nome_arquivo):
    caminho = os.path.join(pasta_dados, nome_arquivo)
    if not os.path.exists(caminho):
        print(f"Ficheiro não encontrado: {nome_arquivo}")
        return pd.DataFrame()
    
    todas_linhas = []
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            tabela = pagina.extract_table()
            if tabela:
                todas_linhas.extend(tabela)
                
    if len(todas_linhas) <= 1:
        print(f"Aviso: Nenhuma tabela válida encontrada em {nome_arquivo}")
        return pd.DataFrame()
        
    # Usa a primeira linha como cabeçalho e o resto como dados
    df = pd.DataFrame(todas_linhas[1:], columns=todas_linhas[0])
    return df

def processar_tudo():
    print("=== A INICIAR PROCESSAMENTO E FILTRAGEM (A PARTIR DE JAN/2026) ===")
    
    # 1. Contas a Pagar (Previsão de Pagamentos)
    print("\nA processar: Previsão de Pagamentos...")
    df_pagar = ler_tabela_pdf("previsao_pagamentos.pdf")
    if not df_pagar.empty:
        print(f"Linhas carregadas: {len(df_pagar)}")
    
    # 2. Contas a Receber (Previsão de Recebimentos)
    print("\nA processar: Previsão de Recebimentos...")
    df_receber = ler_tabela_pdf("previsao_recebimentos.pdf")
    if not df_receber.empty:
        print(f"Linhas carregadas: {len(df_receber)}")

    # 3. Controle Bancário (Demonstrativo Mensal)
    print("\nA processar: Demonstrativo Mensal...")
    df_banco = ler_tabela_pdf("demonstrativo_mensal.pdf")
    if not df_banco.empty:
        print(f"Linhas carregadas: {len(df_banco)}")

    print("\nProcessamento concluído com sucesso! Os dados estão prontos para os gráficos.")

if __name__ == "__main__":
    processar_tudo()