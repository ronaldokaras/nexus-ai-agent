"""
proactive_mode.py - Gerenciamento do Modo Proativo do Nexus Agent
Quando ativado, o agente pode sugerir ativamente ações ou iniciar interações de suporte.
"""

import time
import random
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class ProactiveConfig:
    """Configuração do modo proativo."""
    enabled: bool = False
    min_interval: int = 45      # segundos mínimos entre mensagens proativas
    max_interval: int = 120     # segundos máximos
    last_message_time: float = 0.0
    next_interval_target: float = 0.0


class ProactiveModeManager:
    """
    Gerenciador de iniciativa autônoma do Nexus Agent.
    
    Quando ativado, o agente pode sugerir proativamente ideias,
    relatórios ou dicas, em intervalos aleatórios configuráveis.
    A configuração persiste entre execuções.
    """

    def __init__(self, config_file: str = "build/proactive_config.json"):
        """
        Inicializa o gerenciador do modo proativo.
        
        Args:
            config_file: Caminho para o arquivo de configuração JSON
        """
        self.config_file = config_file
        self.config = ProactiveConfig()
        self._load_config()
        
        # Mensagens proativas (tom profissional, sugestivo)
        self._messages = [
            "Há algo em que eu possa ajudar agora?",
            "Tenho algumas sugestões de melhoria para o projeto. Quer ouvir?",
            "Realizei uma análise dos logs recentes. Deseja um resumo?",
            "Estou disponível para auxiliar em tarefas pendentes.",
            "Notei que você está ativo. Precisa de alguma coisa?",
            "Posso gerar um relatório de desempenho do sistema se desejar.",
            "Seu projeto está bem organizado. Posso otimizar algum módulo?",
            "Tenho ideias que podem aumentar sua produtividade. Quer que eu compartilhe?",
            "Revisei a memória de longo prazo. Algum item merece atenção?",
            "Estou pronto para colaborar em análises ou criação de arquivos."
        ]

    def _load_config(self) -> None:
        """Carrega configuração do arquivo JSON."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config.enabled = data.get('enabled', False)
                    self.config.min_interval = data.get('min_interval', 45)
                    self.config.max_interval = data.get('max_interval', 120)
                    self.config.last_message_time = data.get('last_message_time', 0.0)
                    self.config.next_interval_target = data.get('next_interval_target', 0.0)
            except Exception as e:
                print(f"⚠️ Erro ao carregar config do modo proativo: {e}")

    def _save_config(self) -> None:
        """Salva configuração no arquivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'enabled': self.config.enabled,
                    'min_interval': self.config.min_interval,
                    'max_interval': self.config.max_interval,
                    'last_message_time': self.config.last_message_time,
                    'next_interval_target': self.config.next_interval_target
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar config do modo proativo: {e}")

    def _calculate_next_interval(self) -> float:
        """Calcula um novo intervalo aleatório para a próxima mensagem."""
        return random.uniform(self.config.min_interval, self.config.max_interval)

    def toggle(self) -> str:
        """Alterna o estado do modo proativo."""
        self.config.enabled = not self.config.enabled
        
        if self.config.enabled:
            self.config.last_message_time = time.time()
            self.config.next_interval_target = self._calculate_next_interval()
            status = "✅ ATIVADO"
            mensagem = f"Modo Proativo {status}\n"
            mensagem += f"💬 Sugerirei ideias a cada {self.config.min_interval}-{self.config.max_interval} segundos."
        else:
            status = "❌ DESATIVADO"
            mensagem = f"Modo Proativo {status}\n"
            mensagem += "🔇 Não iniciarei mais interações até nova ativação."
        
        self._save_config()
        return mensagem

    def is_enabled(self) -> bool:
        """Retorna True se o modo proativo está ativado."""
        return self.config.enabled

    def should_speak(self) -> bool:
        """
        Decide se é hora de sugerir algo proativamente.
        Retorna True se o intervalo desde a última mensagem for maior que o alvo.
        """
        if not self.config.enabled:
            return False

        now = time.time()
        
        if self.config.next_interval_target == 0.0:
            self.config.next_interval_target = self._calculate_next_interval()
            self.config.last_message_time = now
            self._save_config()
            return False
        
        elapsed = now - self.config.last_message_time
        
        if elapsed >= self.config.next_interval_target:
            self.config.last_message_time = now
            self.config.next_interval_target = self._calculate_next_interval()
            self._save_config()
            return True
        
        return False

    def get_proactive_message(self, context: str = "") -> str:
        """
        Gera uma mensagem proativa, possivelmente baseada no contexto.
        
        Args:
            context: Contexto atual (ex: "acabou de criar um arquivo", "modo colaborativo ativo")
            
        Returns:
            Uma mensagem personalizada
        """
        if "arquivo" in context.lower() or "criou" in context.lower():
            context_messages = [
                "Arquivos processados com sucesso. Deseja revisar o conteúdo?",
                "Concluí a criação solicitada. Posso gerar um resumo do que foi feito.",
                "Seus arquivos estão organizados na pasta build."
            ]
            return random.choice(context_messages)
        
        if "código" in context.lower() or "programa" in context.lower():
            context_messages = [
                "Analisei o código recente. Tenho recomendações de otimização. Quer que eu apresente?",
                "Seu código está bem estruturado. Posso sugerir melhorias de legibilidade?",
                "Encontrei uma oportunidade de refatoração no projeto. Posso detalhar?"
            ]
            return random.choice(context_messages)
        
        # Mensagem padrão aleatória
        return random.choice(self._messages)

    def set_intervals(self, min_interval: int, max_interval: int) -> str:
        """
        Ajusta os intervalos de mensagens proativas.
        
        Args:
            min_interval: Intervalo mínimo em segundos
            max_interval: Intervalo máximo em segundos
            
        Returns:
            Mensagem de confirmação
        """
        if min_interval < 10:
            return "❌ Intervalo mínimo não pode ser menor que 10 segundos."
        if max_interval < min_interval:
            return "❌ Intervalo máximo deve ser maior que o mínimo."
        
        self.config.min_interval = min_interval
        self.config.max_interval = max_interval
        self._save_config()
        
        return f"✅ Intervalos ajustados: {min_interval}-{max_interval} segundos"

    def add_custom_message(self, message: str) -> None:
        """
        Adiciona uma mensagem personalizada à lista.
        
        Args:
            message: Nova mensagem para o agente usar
        """
        if message and message.strip():
            self._messages.append(message.strip())

    def get_stats(self) -> dict:
        """
        Retorna estatísticas do modo proativo.
        """
        return {
            "enabled": self.config.enabled,
            "min_interval": self.config.min_interval,
            "max_interval": self.config.max_interval,
            "next_interval_target": round(self.config.next_interval_target, 1),
            "last_message_time": self.config.last_message_time,
            "time_since_last": round(time.time() - self.config.last_message_time, 1) if self.config.last_message_time > 0 else 0,
            "total_messages": len(self._messages)
        }


# Instância global
proactive_mode = ProactiveModeManager()