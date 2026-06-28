import pytest
from core.code_guard import CodeExecutionGuard

class TestCodeExecutionGuard:
    def test_safe_code(self):
        safe, msg = CodeExecutionGuard.is_safe_code("print('hello')")
        assert safe is True

    def test_dangerous_code(self):
        safe, msg = CodeExecutionGuard.is_safe_code("os.system('rm -rf /')")
        assert safe is False

    def test_sanitize_code(self):
        sanitized = CodeExecutionGuard.sanitize_code_before_save("```python\nprint(1)\n```")
        assert "```" not in sanitized
        assert "print(1)" in sanitized

    def test_validate_syntax_valid(self):
        valid, _ = CodeExecutionGuard.validate_python_syntax("x = 1")
        assert valid is True

    def test_validate_syntax_invalid(self):
        valid, msg = CodeExecutionGuard.validate_python_syntax("x =")
        assert valid is False