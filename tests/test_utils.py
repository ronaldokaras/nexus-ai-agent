import pytest
from core.utils import limpar_dados, sanitizar_para_texto

class TestUtils:
    def test_limpar_dados_espacos(self):
        assert limpar_dados("   texto   ") == "texto"

    def test_limpar_dados_caracteres_controle(self):
        assert limpar_dados("oi\nvoce\tai") == "oi voce ai"

    def test_sanitizar_aspas(self):
        assert sanitizar_para_texto('ele disse "olá"') == "ele disse 'olá'"