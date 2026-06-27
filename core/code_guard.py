"""
code_guard.py - Guarda de segurança de código do Nexus Agent
Proteção equilibrada: Permite codificação, bloqueia destruição.
"""

import re
from pathlib import Path
from typing import Tuple

class CodeExecutionGuard:
    """Proteção equilibrada: Permite codificação, bloqueia destruição."""

    # Comandos que REALMENTE oferecem risco sistêmico imediato
    CRITICAL_DANGER = [
        r"shutil\.rmtree\s*\(\s*['\"]\s*[/\\]\s*['\"]\s*\)",  # rmtree na raiz /
        r"os\.system\s*\(\s*['\"]\s*rm\s+-\s*rf\s+",           # comando rm -rf via sistema
        r"os\.system\s*\(\s*['\"]\s*del\s+/",                   # del /f /q (Windows)
        r"subprocess\.call\s*\(\s*['\"]\s*rm\s+-\s*rf",         # subprocess com rm -rf
        r"format\s+[a-zA-Z]:",                                  # tentativa de formatar drive (Windows)
        r"diskpart",                                            # comando perigoso do Windows
        r":\(\)\s*\{\s*:\|:&\s*\};:",                           # fork bomb
    ]

    # Padrões que geram ALERTA (não bloqueiam, mas logam)
    SUSPICIOUS_PATTERNS = [
        (r"eval\s*\([^)]*input\s*\(", "eval com input - possível injeção"),
        (r"exec\s*\([^)]*input\s*\(", "exec com input - possível injeção"),
        (r"__import__\s*\(\s*['\"]os['\"]\s*\)", "import dinâmico do os"),
        (r"open\s*\(\s*['\"][^'\"]*\.\./[^'\"]*['\"]", "tentativa de path traversal"),
    ]

    # Whitelist de padrões que parecem perigosos mas são seguros
    SAFE_PATTERNS = [
        r"eval\s*\(\s*['\"].*?['\"]\s*\)",  # eval com string literal (ex: eval('2+2'))
        r"exec\s*\(\s*['\"].*?['\"]\s*\)",  # exec com string literal
    ]

    @staticmethod
    def is_safe_code(code: str) -> Tuple[bool, str]:
        """
        Analisa o código gerado e decide se é seguro.
        
        Retorna:
        - (True, mensagem) para código seguro
        - (False, mensagem_de_erro) para código bloqueado
        """
        if not code or len(code.strip()) < 3:
            return True, "Código irrelevante ou vazio."

        code_lower = code.lower()
        
        # 1. Verifica se é um padrão seguro conhecido (whitelist)
        for pattern in CodeExecutionGuard.SAFE_PATTERNS:
            if re.search(pattern, code_lower, re.IGNORECASE):
                # É um padrão seguro, continua a verificação
                pass
        
        # 2. Bloqueio de Comandos Destrutivos Reais
        for pattern in CodeExecutionGuard.CRITICAL_DANGER:
            if re.search(pattern, code_lower, re.IGNORECASE):
                return False, f"⚠️ BLOQUEIO CRÍTICO: Comando destrutivo detectado"

        # 3. Verificação de caminhos do sistema (apenas bloqueia se tentar acessar)
        system_paths = [
            r"c:[\/\\]windows",           # Windows
            r"c:[\/\\]program files",     # Windows
            r"[\/\\]etc[\/\\]shadow",     # Linux shadow
            r"[\/\\]usr[\/\\]bin",        # Linux bin
            r"[\/\\]boot[\/\\]",          # Linux boot
            r"[\/\\]sys[\/\\]",           # Linux sys
            r"[\/\\]proc[\/\\]",          # Linux proc
        ]
        
        for sys_path in system_paths:
            if re.search(sys_path, code_lower, re.IGNORECASE):
                return False, "⚠️ BLOQUEIO: Tentativa de acesso a pastas do Sistema Operacional."

        # 4. Alertas (não bloqueia, mas registra - opcional)
        for pattern, warning in CodeExecutionGuard.SUSPICIOUS_PATTERNS:
            if re.search(pattern, code_lower, re.IGNORECASE):
                # Em desenvolvimento, você pode querer logar isso
                # logger.warning(f"Código suspeito: {warning}")
                pass  # Não bloqueia, apenas avisa

        return True, "✅ Código verificado e seguro para desenvolvimento."

    @staticmethod
    def sanitize_code_before_save(code: str) -> str:
        """
        Limpa marcações markdown e espaços extras antes de salvar.
        Não altera o código funcional.
        """
        if not code:
            return ""
        
        # Remove possíveis marcações de Markdown que a IA às vezes esquece
        sanitized = code
        sanitized = sanitized.replace("```python", "")
        sanitized = sanitized.replace("```", "")
        
        # Remove linhas que são apenas comentários de segurança (se existirem)
        lines = sanitized.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove linhas que são apenas marcadores de segurança
            if not line.strip().startswith('# [SECURITY'):
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Garante que o arquivo termine com newline (boa prática)
        if result and not result.endswith('\n'):
            result += '\n'
        
        return result

    @staticmethod
    def validate_python_syntax(code: str) -> Tuple[bool, str]:
        """
        Valida a sintaxe do código Python sem executá-lo.
        Útil para verificar se o código gerado é válido.
        
        Retorna:
        - (True, "Sintaxe válida") para código com sintaxe correta
        - (False, mensagem_de_erro) para código com erro de sintaxe
        """
        if not code or len(code.strip()) < 3:
            return True, "Código vazio ou muito curto"
        
        try:
            compile(code, '<string>', 'exec')
            return True, "Sintaxe Python válida"
        except SyntaxError as e:
            return False, f"Erro de sintaxe na linha {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Erro ao compilar: {str(e)}"

    @staticmethod
    def get_security_report(code: str) -> dict:
        """
        Gera um relatório completo de segurança do código.
        Útil para debug e análise.
        
        Retorna um dicionário com:
        - is_safe: bool
        - message: str
        - has_dangerous_patterns: list
        - has_suspicious_patterns: list
        - syntax_valid: bool
        - syntax_error: str or None
        """
        report = {
            "is_safe": True,
            "message": "",
            "has_dangerous_patterns": [],
            "has_suspicious_patterns": [],
            "syntax_valid": True,
            "syntax_error": None
        }
        
        if not code or len(code.strip()) < 3:
            report["message"] = "Código vazio ou muito curto"
            return report
        
        code_lower = code.lower()
        
        # Verifica padrões perigosos
        for pattern in CodeExecutionGuard.CRITICAL_DANGER:
            if re.search(pattern, code_lower, re.IGNORECASE):
                report["has_dangerous_patterns"].append(pattern)
                report["is_safe"] = False
        
        # Verifica padrões suspeitos
        for pattern, warning in CodeExecutionGuard.SUSPICIOUS_PATTERNS:
            if re.search(pattern, code_lower, re.IGNORECASE):
                report["has_suspicious_patterns"].append(warning)
        
        # Verifica sintaxe
        syntax_valid, syntax_msg = CodeExecutionGuard.validate_python_syntax(code)
        report["syntax_valid"] = syntax_valid
        if not syntax_valid:
            report["syntax_error"] = syntax_msg
            # Erro de sintaxe não bloqueia, apenas informa
        
        if report["is_safe"]:
            if report["has_suspicious_patterns"]:
                report["message"] = f"⚠️ Código seguro, mas contém padrões suspeitos: {', '.join(report['has_suspicious_patterns'])}"
            else:
                report["message"] = "✅ Código verificado e seguro"
        else:
            report["message"] = "❌ Código bloqueado: contém comandos destrutivos"
        
        return report