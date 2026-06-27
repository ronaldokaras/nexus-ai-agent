"""
silent_mode.py - Gerenciamento do Modo Silencioso do Nexus Agent
Quando ativado, respostas técnicas são salvas em arquivos em vez de exibidas no chat.
"""

import time
import os
import json
import re
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from core.writer import file_writer


@dataclass
class SilentModeConfig:
    """Configuração do modo silencioso."""
    enabled: bool = False
    save_folder: str = "build/silent"
    quiet_responses: bool = True


class SilentModeManager:
    """
    Gerenciador do Modo Silencioso com persistência.
    
    Quando ativado:
    - Conteúdo técnico é salvo em arquivos .md
    - Respostas do agente são reduzidas ao essencial
    - Configuração persiste entre execuções
    """

    def __init__(self):
        self.config_file = "build/silent_config.json"
        self.config = SilentModeConfig()
        self._load_config()
        
        # Garante que a pasta de salvamento existe
        os.makedirs(self.config.save_folder, exist_ok=True)

    def _load_config(self) -> None:
        """Carrega configuração do arquivo JSON."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config.enabled = data.get('enabled', False)
                    if 'save_folder' in data:
                        self.config.save_folder = data.get('save_folder', 'build/silent')
            except Exception as e:
                print(f"⚠️ Erro ao carregar config do modo silencioso: {e}")

    def _save_config(self) -> None:
        """Salva configuração no arquivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'enabled': self.config.enabled,
                    'save_folder': self.config.save_folder
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar config do modo silencioso: {e}")

    def toggle(self) -> str:
        """Alterna o estado do modo silencioso."""
        self.config.enabled = not self.config.enabled
        self._save_config()
        
        if self.config.enabled:
            status = "✅ ATIVADO"
            mensagem = f"Modo Silencioso {status}\n"
            mensagem += f"📁 Conteúdo técnico será salvo em: `{self.config.save_folder}/`\n"
            mensagem += "💬 Respostas serão concisas e objetivas."
        else:
            status = "❌ DESATIVADO"
            mensagem = f"Modo Silencioso {status}\n"
            mensagem += "💬 Retomando respostas normais."
        
        return mensagem

    def is_enabled(self) -> bool:
        """Retorna True se o modo silencioso está ativado."""
        return self.config.enabled

    def _sanitize_topic(self, topic: str) -> str:
        """Sanitiza o tópico para uso em nome de arquivo."""
        sanitized = re.sub(r'[^\w\s-]', '', topic.lower())
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized[:30] if sanitized else "conteudo"

    def process_technical_content(self, technical_content: str, topic: str = "melhorias") -> str:
        """
        Salva conteúdo técnico em arquivo e retorna resposta curta.
        """
        if not self.config.enabled:
            return technical_content

        if not technical_content or len(technical_content.strip()) < 10:
            return "⚠️ Conteúdo muito curto para salvar."

        timestamp = int(time.time())
        safe_topic = self._sanitize_topic(topic)
        filename = f"{safe_topic}_{timestamp}.md"
        
        relative_path = f"{self.config.save_folder}/{filename}"
        
        # Usa o file_writer (instância corporativa)
        resultado = file_writer.criar_arquivo_autonomo(relative_path, technical_content)
        
        if resultado.get("status") == "success":
            caminho_real = resultado.get("path", relative_path)
            return f"📁 Conteúdo técnico salvo em: `{caminho_real}`"
        else:
            return f"❌ Erro ao salvar conteúdo: {resultado.get('message', 'Erro desconhecido')}"

    def get_save_folder(self) -> str:
        """Retorna a pasta onde os arquivos são salvos."""
        return self.config.save_folder

    def list_saved_files(self) -> list:
        """Lista os arquivos salvos no modo silencioso."""
        try:
            folder_path = Path(self.config.save_folder)
            if not folder_path.exists():
                return []
            return [f.name for f in folder_path.iterdir() if f.is_file()]
        except Exception:
            return []


# Instância global
silent_mode = SilentModeManager()