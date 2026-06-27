"""
core/string_utils.py
Utilidades de manipulação de strings para o Nexus Agent.
Funções leves, rápidas e úteis no dia a dia.
"""

import re
from typing import List, Optional


def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto removendo espaços extras, mas preserva quebras de linha.
    Diferente de limpar_dados() do utils.py que remove \\n e \\t.
    
    Args:
        texto: Texto a ser normalizado
        
    Returns:
        Texto normalizado
    """
    if not texto:
        return ""
    # Remove espaços/tabs repetidos, mas preserva \n
    texto = re.sub(r'[ \t]+', ' ', texto.strip())
    return texto


def truncar_texto(texto: str, max_caracteres: int = 600, suffix: str = "…") -> str:
    """
    Trunca texto longo de forma inteligente (quebra em palavras).
    
    Args:
        texto: Texto a ser truncado
        max_caracteres: Número máximo de caracteres
        suffix: String adicionada ao final quando truncado
        
    Returns:
        Texto truncado
    """
    if not texto or len(texto) <= max_caracteres:
        return texto
    
    # Tenta quebrar no último espaço antes do limite
    truncated = texto[:max_caracteres].rsplit(' ', 1)[0]
    return truncated + suffix


def eh_pergunta(texto: str) -> bool:
    """
    Verifica se o texto parece uma pergunta.
    
    Args:
        texto: Texto a ser analisado
        
    Returns:
        True se termina com '?'
    """
    return texto.strip().endswith('?')


def destacar_comandos(texto: str) -> str:
    """
    Destaca comandos técnicos para melhor visualização no console.
    Formato Rich: `comando` vira [bold cyan]comando[/bold cyan]
    
    Args:
        texto: Texto com comandos entre crases
        
    Returns:
        Texto formatado para Rich
    """
    return re.sub(r'`([^`]+)`', r'[bold cyan]\1[/bold cyan]', texto)


def contar_palavras(texto: str) -> int:
    """
    Conta palavras no texto.
    
    Args:
        texto: Texto a ser analisado
        
    Returns:
        Número de palavras
    """
    return len(texto.split()) if texto else 0


def remover_emojis(texto: str) -> str:
    """
    Remove emojis mantendo apenas o texto.
    
    Args:
        texto: Texto com possíveis emojis
        
    Returns:
        Texto sem emojis
    """
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"  # dingbats
        u"\U000024C2-\U0001F251"  # enclosed characters
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', texto)


def extrair_urls(texto: str) -> List[str]:
    """
    Extrai URLs do texto.
    
    Args:
        texto: Texto com possíveis URLs
        
    Returns:
        Lista de URLs encontradas
    """
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
    return re.findall(url_pattern, texto)


def extrair_emails(texto: str) -> List[str]:
    """
    Extrai emails do texto.
    
    Args:
        texto: Texto com possíveis emails
        
    Returns:
        Lista de emails encontrados
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, texto)


def capitalizar_primeira(texto: str) -> str:
    """
    Capitaliza a primeira letra de cada frase.
    
    Args:
        texto: Texto a ser capitalizado
        
    Returns:
        Texto com primeira letra maiúscula em cada frase
    """
    if not texto:
        return texto
    
    # Divide em frases (por .!? seguido de espaço)
    frases = re.split(r'([.!?]\s+)', texto)
    resultado = []
    
    for i, frase in enumerate(frases):
        if i % 2 == 0:  # é uma frase (não o separador)
            if frase and len(frase) > 0:
                frase = frase[0].upper() + frase[1:] if frase[0].isalpha() else frase
        resultado.append(frase)
    
    return ''.join(resultado)


# ==================== ATALHOS ÚTEIS ====================
# (Sem dicionário confuso - apenas exportação direta)

__all__ = [
    'normalizar_texto',
    'truncar_texto', 
    'eh_pergunta',
    'destacar_comandos',
    'contar_palavras',
    'remover_emojis',
    'extrair_urls',
    'extrair_emails',
    'capitalizar_primeira'
]