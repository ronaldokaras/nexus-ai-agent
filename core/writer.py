"""
writer.py - Módulo de Escrita Autônoma de Arquivos do Nexus Agent
Gerencia criação, leitura, deleção e listagem de arquivos com segurança.
Inclui limpeza de código, backup automático e guardrails de segurança.
"""

import os
import shutil
import re
from datetime import datetime
from rich.console import Console
from pathlib import Path
from typing import Dict, Union

from core.security import SecurityManager
from core.code_guard import CodeExecutionGuard 

console = Console()

class NexusWriter:
    """
    Gerencia a criação e manipulação segura de arquivos no diretório build/.
    Aplica validação de segurança, backup automático e limpeza de código.
    """
    def __init__(self):
        # Raiz do projeto detectada automaticamente
        self.base_dir = str(Path(__file__).resolve().parent.parent)
        self.build_dir = os.path.join(self.base_dir, "build")
        os.makedirs(self.build_dir, exist_ok=True)

    def criar_arquivo_autonomo(self, nome_arquivo: str, conteudo: str) -> Dict[str, Union[str, None]]:
        """
        Cria arquivo com segurança e limpeza de código.
        
        Retorna dicionário com:
        - status: 'success' ou 'error'
        - message: Mensagem descritiva
        - path: Caminho completo do arquivo (se sucesso)
        """
        try:
            nome_arquivo_limpo = nome_arquivo.replace("..", "").lstrip("\\/")
            conteudo_limpo = re.sub(r"```[a-zA-Z]*", "", conteudo).replace("```", "").strip()

            # Verificação de segurança de código
            is_safe, message = CodeExecutionGuard.is_safe_code(conteudo_limpo)
            if not is_safe:
                return {
                    "status": "error",
                    "message": f"❌ {message}",
                    "path": None
                }

            success, result = SecurityManager.secure_write_file(
                base_dir=self.build_dir, 
                filename=nome_arquivo_limpo,
                content=conteudo_limpo
            )

            if not success:
                return {
                    "status": "error",
                    "message": f"❌ {result}",
                    "path": None
                }

            full_path = Path(result)

            # Backup automático se arquivo já existir
            backup_created = False
            if full_path.exists() and full_path.stat().st_size > 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = full_path.with_name(f"{full_path.stem}.backup_{timestamp}{full_path.suffix}")
                try:
                    shutil.copy2(full_path, backup_path)
                    console.print(f"[dim]💾 Backup criado: {backup_path.name}[/dim]")
                    backup_created = True
                except Exception as backup_error:
                    console.print(f"[bold yellow]⚠️ Falha ao criar backup: {backup_error}[/bold yellow]")

            return {
                "status": "success",
                "message": f"✅ Arquivo criado: `[bold cyan]{full_path.name}[/bold cyan]`",
                "path": str(full_path),
                "backup_created": backup_created
            }

        except Exception as e:
            console.print(f"[bold red]Erro crítico no módulo de escrita:[/bold red] {e}")
            return {
                "status": "error",
                "message": f"❌ Erro: {str(e)}",
                "path": None
            }

    def deletar_arquivo(self, nome_arquivo: str) -> str:
        """
        Deleta arquivo de forma segura.
        Retorna mensagem de status.
        """
        try:
            success, result = SecurityManager.secure_delete_file(
                base_dir=self.build_dir,
                filename=nome_arquivo
            )
            
            if success:
                caminho = Path(result)
                return f"🗑️ Arquivo removido: {caminho.name}"
            else:
                return f"❌ {result}"
                
        except Exception as e:
            console.print(f"[bold red]Erro ao deletar arquivo:[/bold red] {e}")
            return f"❌ Erro ao deletar: {str(e)}"

    def listar_arquivos(self, extensao: str = None) -> Dict[str, Union[str, list]]:
        """
        Lista arquivos no diretório build/.
        Filtra por extensão se informado.
        """
        try:
            build_path = Path(self.build_dir)
            if not build_path.exists():
                return {
                    "status": "error",
                    "message": "Diretório build não encontrado.",
                    "files": []
                }
            
            if extensao:
                arquivos = [f.name for f in build_path.iterdir() if f.is_file() and f.suffix == extensao]
            else:
                arquivos = [f.name for f in build_path.iterdir() if f.is_file()]
            
            if not arquivos:
                return {
                    "status": "success",
                    "message": "Nenhum arquivo encontrado.",
                    "files": []
                }
            
            return {
                "status": "success",
                "message": f"Encontrados {len(arquivos)} arquivo(s).",
                "files": sorted(arquivos)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao listar: {str(e)}",
                "files": []
            }

    def ler_arquivo(self, nome_arquivo: str) -> Dict[str, Union[str, None]]:
        """
        Lê o conteúdo de um arquivo no diretório build/.
        Retorna dicionário com status e conteúdo.
        """
        try:
            nome_arquivo_limpo = nome_arquivo.replace("..", "").lstrip("\\/")
            full_path = Path(self.build_dir) / nome_arquivo_limpo
            
            if not full_path.exists():
                return {
                    "status": "error",
                    "message": f"Arquivo não encontrado: {nome_arquivo}",
                    "content": None
                }
            
            with open(full_path, "r", encoding="utf-8") as f:
                conteudo = f.read()
            
            return {
                "status": "success",
                "message": f"✅ Arquivo lido: {full_path.name}",
                "content": conteudo,
                "path": str(full_path)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao ler arquivo: {str(e)}",
                "content": None
            }


# Instância global para uso pelos módulos do agente
file_writer = NexusWriter()