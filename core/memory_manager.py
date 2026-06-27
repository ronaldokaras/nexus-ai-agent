"""
core/memory_manager.py
Gerenciador de memória RAM do Nexus Agent.
Monitora uso real de memória e limpa histórico automaticamente.
"""

import gc
import os
from typing import List, Optional
from rich.console import Console

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    console = Console()
    console.print("[yellow]⚠️ psutil não instalado. Monitoramento de memória desabilitado.[/yellow]")

console = Console()


class NexusMemoryManager:
    """
    Gerenciador inteligente de memória para o Nexus Agent.
    
    Monitora uso de RAM e força limpeza de memória quando necessário.
    Útil para sessões longas ou uso intenso.
    """

    def __init__(self, memory_limit_mb: int = 850):
        """
        Args:
            memory_limit_mb: Limiar de memória em MB para acionar limpeza
        """
        self.memory_limit_mb = memory_limit_mb
        self.has_psutil = HAS_PSUTIL
        
        if self.has_psutil:
            self.process = psutil.Process(os.getpid())
            self.session_start_memory = self.process.memory_info().rss / (1024 * 1024)
        else:
            self.process = None
            self.session_start_memory = 0.0

    def get_current_usage_mb(self) -> float:
        """Retorna o uso atual de memória em MB."""
        if not self.has_psutil:
            return 0.0
        return self.process.memory_info().rss / (1024 * 1024)

    def get_usage_summary(self) -> str:
        """Retorna um resumo do uso de memória."""
        if not self.has_psutil:
            return "N/A (psutil não instalado)"
        current = self.get_current_usage_mb()
        return f"{current:.1f} MB"

    def get_session_peak_mb(self) -> Optional[float]:
        """Retorna o pico de memória da sessão (se disponível)."""
        if not self.has_psutil:
            return None
        return self.process.memory_info().rss / (1024 * 1024)

    def clean_history(self, messages: List, max_messages: int = 60) -> None:
        """
        Limpa histórico antigo mantendo o System Prompt.
        
        Args:
            messages: Lista de mensagens (será modificada in-place)
            max_messages: Número máximo de mensagens a manter
        """
        if len(messages) > max_messages:
            system_prompt = messages[0]
            messages[:] = [system_prompt] + messages[-max_messages + 1:]
            console.print("[dim]🧹 Histórico limpo automaticamente (memória otimizada)[/dim]")
            gc.collect()

    def force_cleanup(self) -> None:
        """Força limpeza de lixo (garbage collection)."""
        gc.collect()
        console.print(f"[dim]🧹 Limpeza forçada executada. Uso atual: {self.get_usage_summary()}[/dim]")

    def check_and_alert(self) -> bool:
        """
        Verifica se o uso de memória está alto e limpa se necessário.
        
        Returns:
            True se limpou, False se estava ok
        """
        if not self.has_psutil:
            return False
        
        usage = self.get_current_usage_mb()
        if usage > self.memory_limit_mb:
            console.print(f"[bold yellow]⚠️ Uso alto de memória detectado! {usage:.1f}MB > {self.memory_limit_mb}MB[/bold yellow]")
            console.print("[bold yellow]   Limpando memória...[/bold yellow]")
            self.force_cleanup()
            return True
        return False

    def get_status(self) -> str:
        """Retorna status do gerenciador de memória."""
        if not self.has_psutil:
            return "⚠️ Monitoramento desabilitado (instale psutil)"
        
        current = self.get_current_usage_mb()
        if current > self.memory_limit_mb:
            return f"⚠️ Memória alta: {current:.1f}MB / {self.memory_limit_mb}MB"
        elif current > self.memory_limit_mb * 0.7:
            return f"🟡 Memória moderada: {current:.1f}MB / {self.memory_limit_mb}MB"
        else:
            return f"✅ Memória ok: {current:.1f}MB"


# Instância global
memory_manager = NexusMemoryManager()