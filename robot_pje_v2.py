from RPA.Browser.Selenium import Selenium
from RPA.Windows import Windows
import time
from datetime import datetime
import pyperclip
import pyautogui

browser = Selenium()
windows = Windows()

def obter_data_busca():
    """Permite ao usuário escolher entre data atual ou data personalizada"""
    print("\n" + "="*60)
    print("  SISTEMA DE BUSCA DE COMUNICAÇÕES PROCESSUAIS - PJe")
    print("  Projeto: Advocacia e IA")
    print("="*60)
    
    print("\nEscolha a data para busca:")
    print("1 - Usar data atual (hoje)")
    print("2 - Informar data específica (passada)")
    
    opcao = input("\nDigite a opção (1 ou 2): ").strip()
    
    if opcao == "1":
        # Usa a data atual
        data_hoje = datetime.now()
        data_busca = data_hoje.strftime("%Y-%m-%d")
        data_display = data_hoje.strftime("%d/%m/%Y")
        print(f"\n✓ Data selecionada: {data_display} (HOJE)")
        return data_busca
    
    elif opcao == "2":
        # Solicita data específica
        while True:
            data_input = input("\nDigite a data desejada (formato: DD/MM/AAAA): ").strip()
            try:
                # Valida o formato
                data_obj = datetime.strptime(data_input, "%d/%m/%Y")
                data_busca = data_obj.strftime("%Y-%m-%d")
                print(f"\n✓ Data selecionada: {data_input}")
                return data_busca
            except ValueError:
                print("❌ Formato inválido! Use o formato DD/MM/AAAA (ex: 30/10/2025)")
    else:
        print("⚠️ Opção inválida! Usando data atual como padrão.")
        data_hoje = datetime.now()
        data_busca = data_hoje.strftime("%Y-%m-%d")
        data_display = data_hoje.strftime("%d/%m/%Y")
        print(f"✓ Data selecionada: {data_display} (HOJE)")
        return data_busca

def buscar_processo(numero, data_busca):
    print("\n=== INICIANDO BUSCA ===")
    
    # Constrói a URL com o número do processo e as datas
    print(f"1. Abrindo navegador para busca na data: {data_busca}...")
    url_busca = f"https://comunica.pje.jus.br/consulta?texto={numero}&dataDisponibilizacaoInicio={data_busca}&dataDisponibilizacaoFim={data_busca}"
    
    # Abre o navegador direto na URL correta
    browser.open_available_browser(url_busca)
    browser.maximize_browser_window()
    print(f"   ✓ URL: {url_busca}")
    
    # Aguarda a página carregar COMPLETAMENTE
    print("   Aguardando página carregar...")
    time.sleep(8)  # Aumentado para 8 segundos
    browser.capture_page_screenshot("01_resultado_direto.png")
    
    # Verifica se encontrou resultados
    print("2. Verificando resultados...")
    
    # Verifica se o botão "Copiar" já está visível (página de detalhes)
    try:
        if browser.is_element_visible("xpath://button[contains(text(), 'Copiar')]"):
            print("   ✓ Já na página de detalhes completa!")
        else:
            # Se não está, procura por links
            print("   Procurando link do processo para abrir detalhes...")
            
            # Usa Selenium para clicar no link (método mais simples)
            try:
                # Procura por qualquer link com número de processo
                link_processo = f"xpath://a[contains(@href, 'Processo') or contains(text(), 'Processo')]"
                browser.click_element(link_processo)
                print("   ✓ Link clicado via Selenium!")
                time.sleep(8)
                browser.capture_page_screenshot("02_processo_detalhes.png")
            except:
                print("   ℹ️ Nenhum link clicável encontrado")
    except Exception as e:
        print(f"   ℹ️ Verificação: {str(e)}")

def copiar_conteudo():
    print("\n=== COPIANDO CONTEÚDO ===")
    try:
        # Aguarda a página carregar completamente
        time.sleep(3)
        
        print("1. Procurando botão 'Copiar sem formatação'...")
        
        # Rola a página para o topo para garantir que o botão esteja visível
        browser.execute_javascript("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Método 1: Tenta clicar no botão diretamente com Selenium
        try:
            print("   Tentando clicar no botão via Selenium...")
            # Botão está no lado direito da tela
            botao = "xpath://button[contains(text(), 'Copiar sem formatação')]"
            browser.wait_until_element_is_visible(botao, timeout=10)
            browser.click_element(botao)
            print("   ✓ Botão clicado via Selenium!")
            time.sleep(2)
            print("   ✓ Conteúdo copiado com sucesso!")
            return
        except Exception as e:
            print(f"   ⚠️ Erro Selenium: {str(e)}")
        
        # Método 2: Usa JavaScript para clicar
        try:
            print("   Tentando método JavaScript...")
            js_click = """
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var btnText = buttons[i].textContent.trim();
                if (btnText.includes('Copiar sem formatação') || btnText.includes('Copiar sem formata')) {
                    buttons[i].scrollIntoView();
                    buttons[i].click();
                    return true;
                }
            }
            return false;
            """
            resultado = browser.execute_javascript(js_click)
            
            if resultado:
                print("   ✓ Botão clicado via JavaScript!")
                time.sleep(2)
                print("   ✓ Conteúdo copiado com sucesso!")
                return
        except Exception as e:
            print(f"   ⚠️ Erro JavaScript: {str(e)}")
        
        # Método 3: Extrai o texto do painel direito diretamente usando Selenium
        print("   Tentando extrair texto do painel de conteúdo via Selenium...")
        try:
            import pyperclip
            
            # Estratégia: Pega todo o body e filtra o que não interessa
            texto_completo = browser.get_text("xpath://body")
            
            if texto_completo and len(texto_completo) > 100:
                print(f"   → Texto bruto capturado: {len(texto_completo)} caracteres")
                
                # Remove o conteúdo da sidebar (filtros) linha por linha
                linhas = texto_completo.split('\n')
                
                # Lista de padrões que indicam conteúdo da sidebar/filtros
                filtros_sidebar = [
                    'Todas as instituições',
                    'Todos os órgãos',
                    'Todos os meios',
                    'Data inicial',
                    'Data final',
                    'Nº de processo',
                    'Nome da parte',
                    'Buscar',
                    'Limpar filtros',
                    'Filtrar por',
                    'Ordenar por'
                ]
                
                # Filtra linhas removendo sidebar e linhas vazias
                linhas_filtradas = []
                for linha in linhas:
                    linha_strip = linha.strip()
                    # Pula linhas vazias
                    if not linha_strip:
                        continue
                    # Pula linhas que começam com padrões de sidebar
                    if any(linha_strip.startswith(filtro) for filtro in filtros_sidebar):
                        continue
                    # Mantém a linha
                    linhas_filtradas.append(linha)
                
                texto_limpo = '\n'.join(linhas_filtradas)
                
                if len(texto_limpo) > 100:
                    # Copia para clipboard usando pyperclip
                    pyperclip.copy(texto_limpo)
                    print(f"   ✓ Texto extraído e copiado! ({len(texto_limpo)} caracteres)")
                    print(f"   → Preview: {texto_limpo[:150]}...")
                    time.sleep(1)
                    return
                else:
                    print(f"   ⚠️ Texto filtrado muito curto: {len(texto_limpo)} caracteres")
                    print(f"   → Preview do que sobrou: {texto_limpo[:200]}")
            else:
                print(f"   ⚠️ Texto bruto muito curto: {len(texto_completo) if texto_completo else 0} caracteres")
        except Exception as e:
            print(f"   ⚠️ Erro ao extrair texto via Selenium: {str(e)}")
        
        raise Exception("Não foi possível copiar o conteúdo por nenhum método")
        
    except Exception as e:
        print(f"\n⚠️ Erro ao copiar: {str(e)}")
        browser.capture_page_screenshot("erro_copiar.png")
        raise

def abrir_bloco_de_notas():
    print("\n=== ABRINDO BLOCO DE NOTAS ===")
    print("1. Abrindo Notepad...")
    
    import subprocess
    import pyautogui
    
    try:
        # Abre o Notepad usando subprocess (mais confiável)
        subprocess.Popen("notepad.exe")
        time.sleep(2)  # Aguarda o Notepad abrir
        print("   ✓ Notepad aberto!")
    except Exception as e:
        print(f"   ⚠️ Erro ao abrir Notepad: {str(e)}")
        print("   Por favor, abra o Notepad manualmente e pressione CTRL+V")
        return
    
    print("2. Colando conteúdo...")
    time.sleep(1)
    
    try:
        # Usa pyautogui para colar (mais rápido e confiável que RPA.Windows)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        print("   ✓ Conteúdo colado no Bloco de Notas!")
    except Exception as e:
        print(f"   ⚠️ Não foi possível colar automaticamente: {str(e)}")
        print("   O conteúdo está na área de transferência - pressione CTRL+V manualmente no Notepad")
    print("\nO Bloco de Notas permanecerá aberto para você visualizar o conteúdo.")
    time.sleep(2)

def executar_robot():
    try:
        # Solicita a data de busca (atual ou personalizada)
        data_busca = obter_data_busca()
        
        # Solicita o número do processo
        print("\n" + "-"*60)
        numero = input("Digite o número do processo: ").strip()
        
        if not numero:
            raise Exception("Número do processo não pode estar vazio!")
        
        # Executa a busca
        buscar_processo(numero, data_busca)
        copiar_conteudo()
        abrir_bloco_de_notas()
        
        print("\n" + "="*60)
        print("  ✓✓✓ AUTOMAÇÃO CONCLUÍDA COM SUCESSO! ✓✓✓")
        print("  Projeto: Advocacia e IA")
        print("="*60 + "\n")
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"  ❌ ERRO: {str(e)}")
        print("="*60 + "\n")
        browser.capture_page_screenshot("erro_final.png")
    finally:
        input("\nPressione ENTER para fechar o navegador...")
        try:
            browser.close_browser()
        except:
            pass

if __name__ == "__main__":
    executar_robot()
