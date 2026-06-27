"""
main.py - Ponto de entrada do Nexus Agent
Sistema Agentivo de Automação e Suporte
"""

import sys
import os
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Carrega variáveis de ambiente
load_dotenv()

# ==================== VERIFICAÇÃO DE DEPENDÊNCIAS ====================
def check_dependencies() -> bool:
    """
    Verifica se todas as dependências necessárias estão instaladas.
    Retorna True se tudo ok, caso contrário exibe erro e sai.
    """
    missing = []
    
    libs_to_check = {
        "nltk": "nltk",
        "numpy": "numpy",
        "pandas": "pandas",
        "rich": "rich",
        "sentence-transformers": "sentence_transformers",
        "scikit-learn": "sklearn",
        "transformers": "transformers",
        "python-dotenv": "dotenv"
    }

    for lib_pip, lib_import in libs_to_check.items():
        try:
            __import__(lib_import)
        except ImportError:
            missing.append(lib_pip)

    if missing:
        print("\n❌ Algumas dependências estão faltando:")
        for lib in missing:
            print(f"   • {lib}")
        print(f"\n🔧 Instale com: pip install {' '.join(missing)}")
        sys.exit(1)

    return True

# Executa verificação antes de qualquer import pesado
check_dependencies()

# ==================== IMPORTS PÓS-VERIFICAÇÃO ====================
import nltk
from core.nexus import Nexus          # Módulo principal do agente (antigo core.selena)
from core.utils import limpar_dados

# Download silencioso do tokenizador
nltk.download('punkt', quiet=True)

console = Console()

# ==================== FUNÇÕES AUXILIARES ====================
def print_nexus(text: str) -> None:
    """Exibe respostas do Nexus Agent com estilo corporativo."""
    console.print(Panel(
        text,
        title="[bold blue]Nexus[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    ))

def limpar_terminal() -> None:
    """Limpa o terminal de forma cross-platform."""
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_ajuda() -> None:
    """Exibe a lista de comandos disponíveis."""
    comandos = """
    [bold cyan]COMANDOS DISPONÍVEIS:[/bold cyan]
    
    [yellow]Sistema:[/yellow]
    • sair, exit, quit, /sair      - Encerra o Nexus Agent
    • limpar, clear, /limpar       - Limpa o terminal
    • reiniciar, reset, /reiniciar - Reinicia a conversa (limpa memória)
    • atualizar, reload, /atualizar- Reinicia o programa por completo
    
    [yellow]Visualização:[/yellow]
    • .notes, mostra notas, ver notas - Exibe notas de comportamento
    • .metrics, mostra métricas, ver métricas - Exibe métricas de uso
    • .status, status - Mostra estado atual dos módulos
    
    [yellow]Modos:[/yellow]
    • .silencioso, modo silencioso    - Alterna modo silencioso (respostas sob demanda)
    • .proativo, modo proativo        - Alterna modo proativo (sugestões automáticas)
    
    [yellow]Voz:[/yellow]
    • .voz, ativar voz, voz on      - Ativa a síntese de voz
    • .silenciar, desativar voz, voz off - Desativa a síntese de voz
    
    [yellow]Geral:[/yellow]
    • .help, ajuda, /help - Mostra esta ajuda
    """
    console.print(Panel(comandos, title="[bold cyan]📖 Ajuda do Nexus[/bold cyan]", border_style="cyan"))

# ==================== COMANDOS DISPONÍVEIS ====================
COMANDOS_SISTEMA = {
    "sair": ("sair", "exit", "quit", "/sair"),
    "limpar": ("limpar", "clear", "/limpar"),
    "reiniciar": ("reiniciar", "reset", "/reiniciar", "/reset"),
    "atualizar": ("atualizar", "reload", "/atualizar", "/reload"),
    "ajuda": (".help", "ajuda", "/help"),
}

COMANDOS_VISUALIZACAO = {
    ".notes": ("mostra notas", "ver notas"),
    ".metrics": ("mostra métricas", "ver métricas"),
    ".status": ("status",),
}

COMANDOS_MODOS = {
    ".silencioso": ("modo silencioso", "silencioso"),
    ".proativo": ("modo proativo", "proativo"),
}

COMANDOS_VOZ = {
    ".voz": ("ativar voz", "voz on", "liga voz"),
    ".silenciar": ("desativar voz", "voz off", "desliga voz"),
}

def processar_comando_sistema(user_input: str, nexus: Nexus) -> str | None:
    """
    Processa comandos de sistema.
    Retorna string de resposta ou None se não for comando de sistema.
    """
    cmd_lower = user_input.lower()
    
    if cmd_lower in COMANDOS_SISTEMA["sair"]:
        return "SAIR"
    
    if cmd_lower in COMANDOS_SISTEMA["limpar"]:
        limpar_terminal()
        console.print("[bold yellow]🧹 Terminal limpo.[/bold yellow]")
        return "CONTINUE"
    
    if cmd_lower in COMANDOS_SISTEMA["reiniciar"]:
        return "REINICIAR_CONVERSA"
    
    if cmd_lower in COMANDOS_SISTEMA["atualizar"]:
        return "REINICIAR_PROGRAMA"
    
    if cmd_lower in COMANDOS_SISTEMA["ajuda"]:
        mostrar_ajuda()
        return "CONTINUE"
    
    return None

def processar_comando_visualizacao(user_input: str, nexus: Nexus) -> str | None:
    """
    Processa comandos de visualização.
    Retorna string de resposta ou None se não for comando de visualização.
    """
    cmd_lower = user_input.lower()
    
    if cmd_lower in COMANDOS_VISUALIZACAO[".notes"]:
        nexus.show_notes()
        return "CONTINUE"
    
    if cmd_lower in COMANDOS_VISUALIZACAO[".metrics"]:
        nexus.show_metrics()
        return "CONTINUE"
    
    if cmd_lower in COMANDOS_VISUALIZACAO[".status"]:
        status = f"Modo Silencioso: {'ON' if nexus.silent_mode.is_enabled() else 'OFF'}\n"
        
        pro_status = "OFF"
        if hasattr(nexus, 'proactive_mode') and nexus.proactive_mode.is_enabled():
            pro_status = "ON"
        
        status += f"Modo Proativo: {pro_status}\n"
        # Estabilidade de sentimento (análise de humor/contexto)
        status += f"Estabilidade de Sentimento: {nexus.emotional_stability.state.stability * 100:.0f}%"
        
        print_nexus(status)
        return "CONTINUE"
    
    return None

def processar_comando_modo(user_input: str, nexus: Nexus) -> str | None:
    """
    Processa comandos de modos (silencioso, proativo, voz).
    Retorna string de resposta ou None se não for comando de modo.
    """
    cmd_lower = user_input.lower()
    
    if cmd_lower in COMANDOS_MODOS[".silencioso"]:
        reply = nexus.silent_mode.toggle()
        print_nexus(reply)
        return "CONTINUE"
    
    if cmd_lower in COMANDOS_MODOS[".proativo"]:
        if hasattr(nexus, 'proactive_mode'):
            reply = nexus.proactive_mode.toggle()
            print_nexus(reply)
        else:
            console.print("[bold red]⚠️ Módulo proativo não disponível.[/bold red]")
        return "CONTINUE"
    
    if cmd_lower in COMANDOS_VOZ[".voz"]:
        nexus.voice_enabled = True
        print_nexus("🔊 Voz ativada.")
        return "CONTINUE"
    
    if cmd_lower in COMANDOS_VOZ[".silenciar"]:
        nexus.voice_enabled = False
        print_nexus("🔇 Voz desativada. Respostas apenas em texto.")
        return "CONTINUE"
    
    return None

# ==================== FUNÇÃO DE REINICIALIZAÇÃO ====================
def reiniciar_programa() -> None:
    """Reinicia o programa completamente."""
    console.print(Panel(
        "[bold yellow]🔄 Reiniciando o Nexus Agent...[/bold yellow]",
        border_style="yellow"
    ))
    time.sleep(1)
    python = sys.executable
    os.execl(python, python, *sys.argv)

# ==================== LOOP PRINCIPAL ====================
def main() -> None:
    """Função principal do programa."""
    try:
        nexus = Nexus()

        limpar_terminal()
        console.print(Panel.fit(
            "[bold blue]Nexus Agent iniciado.[/bold blue]\n"
            "Sistema de automação e suporte inteligente pronto.\n"
            "Como posso ajudar?\n\n"
            "[dim]Digite .help ou ajuda para ver os comandos disponíveis[/dim]",
            border_style="blue",
            padding=(1, 4)
        ))

        while True:
            try:
                # ============== MODO PROATIVO ==============
                if hasattr(nexus, 'proactive_mode') and nexus.proactive_mode.should_speak():
                    proactive_msg = nexus.proactive_mode.get_proactive_message()
                    if proactive_msg:
                        print_nexus(proactive_msg)

                # ============== ENTRADA DO USUÁRIO ==============
                entrada = console.input("\n[bold cyan]Entrada > [/bold cyan]").strip()
                user_input = limpar_dados(entrada)

                if not user_input:
                    continue

                # ============== PROCESSAMENTO DE COMANDOS ==============
                cmd_result = processar_comando_sistema(user_input, nexus)
                if cmd_result == "SAIR":
                    print_nexus("Encerrando Nexus Agent. Até logo!")
                    break
                elif cmd_result == "REINICIAR_CONVERSA":
                    nexus = Nexus()  # Nova instância com memória limpa
                    limpar_terminal()
                    console.print(Panel(
                        "[bold green]🔄 Conversa reiniciada com sucesso.[/bold green]",
                        border_style="green"
                    ))
                    continue
                elif cmd_result == "REINICIAR_PROGRAMA":
                    reiniciar_programa()
                    return
                elif cmd_result == "CONTINUE":
                    continue

                cmd_result = processar_comando_visualizacao(user_input, nexus)
                if cmd_result == "CONTINUE":
                    continue

                cmd_result = processar_comando_modo(user_input, nexus)
                if cmd_result == "CONTINUE":
                    continue

                # ============== CONVERSA NORMAL ==============
                with console.status("[bold blue]Nexus processando...[/bold blue]", spinner="dots"):
                    reply = nexus.chat(user_input)

                print_nexus(reply)

            except KeyboardInterrupt:
                print_nexus("Operação interrompida. Até logo.")
                break

            except Exception as e:
                console.print(f"[bold red]❌ Erro na interação: {e}[/bold red]")
                continuar = console.input("[dim]Deseja continuar? (s/n): [/dim]").lower()
                if continuar not in ['s', 'sim', 'y', 'yes']:
                    break

    except Exception as e:
        console.print(f"[bold red]❌ Erro crítico ao inicializar o Nexus Agent: {e}[/bold red]")
        sys.exit(1)

# ====================== PONTO DE ENTRADA ======================
if __name__ == "__main__":
    main()