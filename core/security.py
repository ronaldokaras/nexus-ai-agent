"""
security.py - Módulo de Segurança e Governança de Código (Nexus Agent)
Implementa guardrails para escrita, leitura e deleção de arquivos,
sanitização de nomes, rate limiting e confinamento de diretório.
"""

import os
import re
import time
from pathlib import Path
from typing import Tuple, Dict
from collections import defaultdict

class SecurityManager:
    """Gerencia a segurança das operações de arquivo, com isolamento no diretório build/ e rate limiting."""

    ALLOWED_EXTENSIONS = {'.py', '.txt', '.md', '.json', '.log', '.yaml', '.yml', '.html', '.css', '.js'}
    
    rate_limit = defaultdict(list)  # {operation_type: [timestamps]}

    @staticmethod
    def is_path_safe(base_dir: str, target_path: str) -> Tuple[bool, str]:
        """Verifica se o caminho está restrito ao diretório base (build/)."""
        try:
            base_path = Path(base_dir).resolve()
            target = (base_path / target_path).resolve()

            if not str(target).startswith(str(base_path)):
                return False, "Tentativa de acesso fora do diretório permitido bloqueada."

            return True, ""
        except Exception as e:
            return False, f"Erro de validação de caminho: {e}"

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitiza nome de arquivo, garantindo extensão segura."""
        if not filename:
            return "arquivo_autonomo.txt"

        # Remove caracteres perigosos
        filename = re.sub(r'[<>:"|?*]', '_', filename.strip())
        filename = re.sub(r'[\\/]+', '/', filename).lstrip('/')

        ext = Path(filename).suffix.lower()
        if not ext or ext not in SecurityManager.ALLOWED_EXTENSIONS:
            filename = Path(filename).stem + '.txt'

        return filename

    @staticmethod
    def check_rate_limit(operation: str = "write", max_per_minute: int = 3) -> bool:
        """Impede abusos limitando operações por minuto."""
        now = time.time()
        SecurityManager.rate_limit[operation] = [t for t in SecurityManager.rate_limit[operation] if now - t < 60]

        if len(SecurityManager.rate_limit[operation]) >= max_per_minute:
            return False
        
        SecurityManager.rate_limit[operation].append(now)
        return True

    @staticmethod
    def secure_write_file(base_dir: str, filename: str, content: str) -> Tuple[bool, str]:
        """
        Escreve arquivo de forma segura.
        Retorna (True, caminho_completo) ou (False, erro).
        """
        if not SecurityManager.check_rate_limit("write"):
            return False, "Limite de taxa atingido (3 arquivos por minuto). Aguarde."

        if not content or len(content.strip()) < 1:
            return False, "Conteúdo vazio ou muito curto."

        safe_filename = SecurityManager.sanitize_filename(filename)
        is_safe, error = SecurityManager.is_path_safe(base_dir, safe_filename)

        if not is_safe:
            return False, f"Operação bloqueada: {error}"

        try:
            full_path = Path(base_dir) / safe_filename
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)

            return True, str(full_path)
        except Exception as e:
            return False, f"Erro ao escrever: {e}"

    @staticmethod
    def secure_delete_file(base_dir: str, filename: str) -> Tuple[bool, str]:
        """
        Deleta arquivo de forma segura.
        Retorna (True, caminho_completo) ou (False, erro).
        """
        if not SecurityManager.check_rate_limit("delete"):
            return False, "Limite de exclusão atingido (3 operações por minuto). Aguarde."

        safe_filename = SecurityManager.sanitize_filename(filename)
        is_safe, error = SecurityManager.is_path_safe(base_dir, safe_filename)

        if not is_safe:
            return False, f"Operação bloqueada: {error}"

        try:
            full_path = Path(base_dir) / safe_filename
            if full_path.exists():
                full_path.unlink()
                return True, str(full_path)
            else:
                return False, f"Arquivo não encontrado: {safe_filename}"
        except Exception as e:
            return False, f"Erro ao deletar: {e}"

    @staticmethod
    def secure_read_file(base_dir: str, filename: str) -> Tuple[bool, str]:
        """
        Lê arquivo com segurança.
        Retorna (True, conteúdo) ou (False, erro).
        """
        safe_filename = SecurityManager.sanitize_filename(filename)
        is_safe, error = SecurityManager.is_path_safe(base_dir, safe_filename)

        if not is_safe:
            return False, f"Operação bloqueada: {error}"

        try:
            full_path = Path(base_dir) / safe_filename
            if not full_path.exists():
                return False, f"Arquivo não encontrado: {safe_filename}"
            
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return True, content
        except Exception as e:
            return False, f"Erro ao ler: {e}"

    @staticmethod
    def secure_list_files(base_dir: str, extension: str = None) -> Tuple[bool, list]:
        """
        Lista arquivos do diretório base.
        Retorna (True, lista) ou (False, erro).
        """
        try:
            base_path = Path(base_dir).resolve()
            if not base_path.exists():
                return False, f"Diretório não encontrado: {base_dir}"
            
            arquivos = []
            for item in base_path.iterdir():
                if item.is_file():
                    if extension is None or item.suffix == extension:
                        arquivos.append(item.name)
            
            return True, sorted(arquivos)
        except Exception as e:
            return False, f"Erro ao listar arquivos: {e}"

    @staticmethod
    def get_rate_limit_status(operation: str = "write") -> Dict:
        """Retorna o status atual do rate limit para monitoramento."""
        now = time.time()
        recent = [t for t in SecurityManager.rate_limit[operation] if now - t < 60]
        return {
            "operation": operation,
            "recent_operations": len(recent),
            "remaining": max(0, 3 - len(recent)),
            "reset_in_seconds": 60 - (now - recent[0]) if recent else 0
        }