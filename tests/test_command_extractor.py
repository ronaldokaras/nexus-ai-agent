import pytest
from core.command_extractor import CommandExtractor

class TestCommandExtractor:
    def setup_method(self):
        self.extractor = CommandExtractor(threshold=0.68)

    def test_extract_create_file(self):
        cmd = self.extractor.extract("crie um arquivo chamado teste.py")
        assert cmd.type == "criar_arquivo"

    def test_extract_modo_silencioso(self):
        cmd = self.extractor.extract("modo silencioso agora")
        assert cmd.type == "modo_silencioso"

    def test_extract_neutral(self):
        cmd = self.extractor.extract("como vai você?")
        assert cmd.type is None

    def test_extract_mostrar_metricas(self):
        cmd = self.extractor.extract(".metrics")
        assert cmd.type == "mostrar_metricas"