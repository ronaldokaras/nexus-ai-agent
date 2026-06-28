import pytest
from core.security import SecurityManager

class TestSecurityManager:
    def test_is_path_safe_inside_build(self, temp_dir):
        assert SecurityManager.is_path_safe(temp_dir, "teste.txt")[0] is True

    def test_is_path_safe_outside_build(self, temp_dir):
        assert SecurityManager.is_path_safe(temp_dir, "../outside.txt")[0] is False

    def test_sanitize_filename_valid(self):
        assert SecurityManager.sanitize_filename("script.py") == "script.py"

    def test_sanitize_filename_invalid_extension(self):
        result = SecurityManager.sanitize_filename("script.unsafe")
        assert result.endswith(".txt")

    def test_sanitize_filename_dangerous_chars(self):
        result = SecurityManager.sanitize_filename('file<name>.txt')
        assert "<" not in result

    def test_secure_write_file_success(self, temp_dir):
        success, msg = SecurityManager.secure_write_file(temp_dir, "teste.txt", "conteudo")
        assert success is True

    def test_secure_write_file_rate_limit(self, temp_dir):
        # Força o rate limit escrevendo 3 vezes
        for i in range(3):
            SecurityManager.secure_write_file(temp_dir, f"a{i}.txt", "x")
        success, msg = SecurityManager.secure_write_file(temp_dir, "b.txt", "x")
        assert success is False

    def test_secure_write_file_empty_content(self, temp_dir):
        success, msg = SecurityManager.secure_write_file(temp_dir, "vazio.txt", "")
        assert success is False