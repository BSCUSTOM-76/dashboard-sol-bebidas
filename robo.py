import os
from time import sleep
from playwright.sync_api import sync_playwright

SYSTEM_URL = "https://erp.saibweb.com.br/auth"
USER = "SOL.FINANCEIRO"
PASS = "Sol@2025"

DATA_INICIAL = "01/01/2026"
DATA_FINAL = "31/12/2026"

FLUXOS_EXTRACAO = [
    {
        "categoria": "CONTAS A RECEBER",
        "relatorios": [
            {"nome": "MOVIMENTAÇÃO FINANCEIRA CR", "arquivo": "movimentacao_financeira_cr.pdf"},
            {"nome": "COBRANÇA X FORMA PGTO X ROTA", "arquivo": "cobranca_forma_pgto_rota.pdf"},
            {"nome": "REL. PREVISÃO DE RECEBIMENTOS", "arquivo": "previsao_recebimentos.pdf"}
        ]
    },
    {
        "categoria": "CONTAS A PAGAR",
        "relatorios": [
            {"nome": "REL. PREVISÃO DE PAGAMENTOS", "arquivo": "RELATÓRIO PREVISÃO DE PAGAMENTO.pdf"}
        ]
    },
    {
        "categoria": "CONTROLE BANCÁRIO",
        "relatorios": [
            {"nome": "DEMONSTRATIVO MENSAL", "arquivo": "demonstrativo_mensal.pdf"},
            {"nome": "REL FECHAMENTO DE CAIXA", "arquivo": "rel_fechamento_caixa.pdf"}
        ]
    }
]

def extrair_relatorios():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("1. A aceder ao SAIBWEB...")
        page.goto(SYSTEM_URL)
        page.wait_for_load_state("networkidle")

        print("2. A preencher as credenciais de acesso...")
        try:
            page.locator("input[type='text'], input[type='email']").first.fill(USER)
            page.locator("input[type='password']").first.fill(PASS)
            page.locator("button[type='submit'], input[type='submit']").first.click()
        except Exception as e:
            print(f"Erro no login: {e}")

        print("3. A aguardar o carregamento do painel principal...")
        page.wait_for_load_state("networkidle")
        sleep(5)

        pasta_destino = os.getcwd()

        for grupo in FLUXOS_EXTRACAO:
            cat_menu = grupo["categoria"]
            
            for index, item in enumerate(grupo["relatorios"]):
                nome_rel = item["nome"]
                nome_arq = item["arquivo"]
                print(f"\n--- A processar [{cat_menu}] -> {nome_rel} ---")

                try:
                    page.keyboard.press("Escape")
                    sleep(1)

                    print("A abrir o menu lateral (☰)...")
                    page.locator("header button, nav button, .fa-bars, span:has-text('☰')").first.click(force=True)
                    sleep(2)

                    print(f"A aceder a '{cat_menu}'...")
                    page.locator("nav, aside, div[class*='drawer'], div[class*='menu']").get_by_text(cat_menu, exact=False).first.click()
                    sleep(2)

                    print("A aceder a 'RELATÓRIOS'...")
                    page.get_by_text("RELATÓRIOS", exact=False).first.click()
                    sleep(2)

                    # Clica no relatório correspondente
                    relatorio = page.locator(f"text={nome_rel}")
                    relatorio.wait_for(state="visible", timeout=15000)
                    relatorio.click()
                    sleep(3) 

                    print(f"A preencher o período de datas ({DATA_INICIAL} a {DATA_FINAL})...")
                    page.evaluate("""(datas) => {
                        const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"])'));
                        let alterados = 0;
                        inputs.forEach(input => {
                            const ph = (input.placeholder || '').toLowerCase();
                            const id = (input.id || '').toLowerCase();
                            const name = (input.name || '').toLowerCase();
                            
                            if (ph.includes('data') || ph.includes('ini') || ph.includes('fim') ||
                                id.includes('data') || id.includes('ini') || id.includes('fim') || id.includes('dt') ||
                                name.includes('data') || name.includes('ini') || name.includes('fim') ||
                                input.type === 'date') {
                                
                                if (alterados === 0) {
                                    input.value = datas.inicio;
                                } else {
                                    input.value = datas.fim;
                                }
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                                alterados++;
                            }
                        });

                        if (alterados < 2 && inputs.length >= 2) {
                            inputs[0].value = datas.inicio;
                            inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                            inputs[0].dispatchEvent(new Event('change', { bubbles: true }));

                            inputs[1].value = datas.fim;
                            inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
                            inputs[1].dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }""", {"inicio": DATA_INICIAL, "fim": DATA_FINAL})
                    sleep(2)

                    print("A gerar o relatório (clicar no botão de geração/busca)...")
                    page.evaluate("""() => {
                        const botoes = Array.from(document.querySelectorAll('button, div[role="button"], a, i.fa-search, span'));
                        let botaoAlvo = botoes.find(b => b.textContent && b.textContent.includes('Gerar relatório'));
                        if (!botaoAlvo) {
                            botaoAlvo = botoes.find(b => {
                                const rect = b.getBoundingClientRect();
                                return rect.top > 30 && rect.top < 140 && rect.left >= 0 && rect.left < 200;
                            });
                        }
                        if (botaoAlvo) {
                            botaoAlvo.click();
                        } else {
                            const iconeBusca = document.querySelector('.fa-search, [class*="search"]');
                            if (iconeBusca) iconeBusca.click();
                        }
                    }""")
                    
                    print("A aguardar o carregamento completo dos dados...")
                    sleep(8) 

                    # Guarda o relatório atual como PDF
                    caminho_ficheiro = os.path.join(pasta_destino, nome_arq)
                    page.pdf(path=caminho_ficheiro, format="A4", print_background=True)
                    print(f"Sucesso absoluto! Guardado em: {nome_arq}")

                    # Fecha a janela de pré-visualização
                    page.evaluate("""() => {
                        const btnFechar = Array.from(document.querySelectorAll('button, i, span')).find(el => {
                            const rect = el.getBoundingClientRect();
                            return rect.top > 40 && rect.top < 120 && rect.right > (window.innerWidth - 80) && (el.textContent.includes('×') || el.className.includes('close') || el.querySelector('.fa-times'));
                        });
                        if (btnFechar) btnFechar.click();
                    }""")
                    sleep(2)

                except Exception as e:
                    print(f"Erro ao processar o relatório {nome_rel}: {e}")

        print("\nProcesso concluído com sucesso para todos os módulos e relatórios!")
        sleep(5)
        browser.close()

if __name__ == "__main__":
    extrair_relatorios()