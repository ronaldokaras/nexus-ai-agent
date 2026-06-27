"""
utils.py - Funções utilitárias para o Nexus Agent
"""

import re
import os
import shutil
from datetime import datetime
from typing import Tuple, Union

# ==================== CONSTANTES ====================

def get_project_root() -> str:
    """Retorna o caminho absoluto da raiz do projeto."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ==================== LIMPEZA DE DADOS ====================

def limpar_dados(dados: str) -> str:
    """
    Remove espaços extras, caracteres invisíveis e 
    garante que o input não esteja vazio ou corrompido.
    
    NOTA: Remove caracteres de controle ASCII (0-31, 127-159)
    incluindo \n e \t. Para inputs de linha única é seguro.
    """
    if not isinstance(dados, str):
        return str(dados)

    # 1. Remove espaços em branco no início e no fim
    texto_limpo = dados.strip()

    # 2. Remove sequências de escape estranhas (comum em CLIs)
    # Remove ASCII 0-31 (controle) e 127-159 (extended)
    texto_limpo = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto_limpo)

    # 3. Normaliza múltiplos espaços para um único espaço
    texto_limpo = " ".join(texto_limpo.split())

    return texto_limpo


def sanitizar_para_texto(texto: str) -> str:
    """
    Sanitiza texto para armazenamento seguro (substitui aspas duplas por simples).
    Útil para salvar em bancos de dados ou arquivos que não suportam JSON.
    """
    if not isinstance(texto, str):
        texto = str(texto)
    return limpar_dados(texto).replace('"', "'")


# ==================== FUNÇÕES DE MELHORIA CONTÍNUA ====================

def gerar_proposta_update(nome_modulo: str, novo_codigo: str, descricao: str = "") -> Union[str, Tuple[bool, str]]:
    """
    Cria um arquivo na pasta 'updates' para revisão do operador.
    
    Retorno (modo compatível):
    - Em caso de sucesso: retorna o caminho do arquivo (string)
    - Em caso de erro: retorna mensagem de erro (string)
    
    Para novo código, use a versão com retorno de tupla: gerar_proposta_update_v2()
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
        
        return caminho_completo
        
    except Exception as e:
        return f"Erro ao gerar proposta: {e}"


def gerar_proposta_update_v2(nome_modulo: str, novo_codigo: str, descricao: str = "") -> Tuple[bool, str]:
    """
    Versão melhorada com retorno em tupla (sucesso, resultado).
    Recomendado para novos códigos.
    """
    resultado = gerar_proposta_update(nome_modulo, novo_codigo, descricao)
    
    if isinstance(resultado, str) and resultado.startswith("Erro"):
        return False, resultado
    elif isinstance(resultado, str):
        return True, resultado
    else:
        return False, "Erro desconhecido ao gerar proposta"


def validar_codigo_antes_aplicar(caminho_proposta: str) -> Tuple[bool, str]:
    """
    Valida se o código da proposta é sintaticamente válido.
    Retorna (True, "OK") se válido, (False, erro) caso contrário.
    """
    try:
        with open(caminho_proposta, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        # Tenta compilar o código Python (sem executar)
        compile(conteudo, caminho_proposta, 'exec')
        return True, "Código válido"
    except SyntaxError as e:
        return False, f"Erro de sintaxe na linha {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Erro na validação: {e}"


def aplicar_atualizacao_aprovada(caminho_proposta: str, modulo_alvo: str) -> Union[bool, Tuple[bool, str]]:
    """
    Move a proposta aprovada para o lugar do código original.
    
    Parâmetros:
    - caminho_proposta: Caminho do arquivo de proposta
    - modulo_alvo: Caminho relativo (ex: "core/database.py" ou "main.py")
    
    Retorno (modo compatível):
    - bool True/False para compatibilidade com código existente
    """
    try:
        base_dir = get_project_root()
        caminho_destino = os.path.join(base_dir, modulo_alvo)
        
        if not os.path.exists(caminho_destino):
            print(f"Erro ao aplicar atualização: Arquivo de destino não encontrado: {modulo_alvo}")
            return False
        
        valido, msg = validar_codigo_antes_aplicar(caminho_proposta)
        if not valido:
            print(f"Erro ao aplicar atualização: Validação falhou: {msg}")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_backup = f"{caminho_destino}.bak_{timestamp}"
        shutil.copy(caminho_destino, caminho_backup)
        shutil.copy(caminho_proposta, caminho_destino)
        
        print(f"✅ Atualização aplicada com sucesso. Backup: {caminho_backup}")
        return True
        
    except Exception as e:
        print(f"Erro ao aplicar atualização: {e}")
        return False


def aplicar_atualizacao_aprovada_v2(caminho_proposta: str, modulo_alvo: str) -> Tuple[bool, str]:
    """
    Versão melhorada com retorno em tupla (sucesso, mensagem).
    Recomendado para novos códigos.
    """
    try:
        base_dir = get_project_root()
        caminho_destino = os.path.join(base_dir, modulo_alvo)
        
        if not os.path.exists(caminho_destino):
            return False, f"Arquivo de destino não encontrado: {modulo_alvo}"
        
        valido, msg = validar_codigo_antes_aplicar(caminho_proposta)
        if not valido:
            return False, f"Validação falhou: {msg}"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_backup = f"{caminho_destino}.bak_{timestamp}"
        shutil.copy(caminho_destino, caminho_backup)
        shutil.copy(caminho_proposta, caminho_destino)
        
        return True, f"✅ Atualização aplicada com sucesso. Backup: {caminho_backup}"
        
    except Exception as e:
        return False, f"Erro ao aplicar: {e}"


# ==================== FUNÇÃO DEPRECIADA ====================

def formatar_para_json(dados):
    """
    [DEPRECIADA] Use sanitizar_para_texto() em vez desta.
    Esta função quebra JSON válido.
    """
    import warnings
    warnings.warn("formatar_para_json() é depreciada. Use sanitizar_para_texto()", DeprecationWarning)
    return sanitizar_para_texto(dados)