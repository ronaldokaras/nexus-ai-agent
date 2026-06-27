"""
auto_evolution.py - Sistema de evolução contínua do Nexus Agent
Gerencia propostas de melhoria e aplicação de código aprovado
"""

import os
import shutil
from datetime import datetime
from typing import Tuple

from core.utils import get_project_root, validar_codigo_antes_aplicar


def gerar_proposta_update(
    nome_modulo: str, 
    novo_codigo: str, 
    descricao: str = ""
) -> Tuple[bool, str]:
    """
    Cria um arquivo na pasta 'updates' para revisão.
    
    Retorna:
    - (True, caminho_do_arquivo) em caso de sucesso
    - (False, mensagem_de_erro) em caso de falha
    """
    try:
        base_dir = get_project_root()
        pasta_updates = os.path.join(base_dir, "updates")
        
        if not os.path.exists(pasta_updates):
            os.makedirs(pasta_updates)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"proposta_{nome_modulo}_{timestamp}.py"
        caminho_completo = os.path.join(pasta_updates, nome_arquivo)
        
        with open(caminho_completo, "w", encoding="utf-8") as f:
            f.write(f'"""\nPROPOSTA DE MELHORIA DO NEXUS AGENT\n')
            f.write(f'DESCRIÇÃO: {descricao}\n')
            f.write(f'DATA: {datetime.now().strftime("%d/%m/%Y %H:%M")}\n"""\n\n')
            f.write(novo_codigo)
        
        return True, caminho_completo
        
    except Exception as e:
        return False, f"Erro ao gerar proposta: {e}"


def aplicar_atualizacao_aprovada(
    caminho_proposta: str, 
    modulo_alvo: str
) -> Tuple[bool, str]:
    """
    Move a proposta aprovada para o lugar do código original.
    
    Parâmetros:
    - caminho_proposta: Caminho do arquivo de proposta
    - modulo_alvo: Caminho relativo (ex: "core/database.py" ou "main.py")
    
    Retorna:
    - (True, mensagem) em caso de sucesso
    - (False, mensagem_de_erro) em caso de falha
    """
    try:
        base_dir = get_project_root()
        caminho_destino = os.path.join(base_dir, modulo_alvo)
        
        # Verifica se o arquivo de destino existe
        if not os.path.exists(caminho_destino):
            return False, f"Arquivo de destino não encontrado: {modulo_alvo}"
        
        # Valida o código antes de aplicar
        valido, msg = validar_codigo_antes_aplicar(caminho_proposta)
        if not valido:
            return False, f"Validação falhou: {msg}"
        
        # Cria backup com timestamp (evita sobrescrever backup anterior)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_backup = f"{caminho_destino}.bak_{timestamp}"
        shutil.copy(caminho_destino, caminho_backup)
        
        # Sobrescreve com o novo código
        shutil.copy(caminho_proposta, caminho_destino)
        
        return True, f"✅ Código aplicado com sucesso. Backup: {caminho_backup}"
        
    except Exception as e:
        return False, f"Erro ao aplicar: {e}"