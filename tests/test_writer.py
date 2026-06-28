import pytest
from core.writer import NexusWriter

class TestWriter:
    def test_criar_arquivo_autonomo(self, temp_dir):
        writer = NexusWriter()
        writer.build_dir = temp_dir  # redireciona para diretório temp
        result = writer.criar_arquivo_autonomo("teste.txt", "conteúdo")
        assert result["status"] == "success"
        assert os.path.exists(os.path.join(temp_dir, "teste.txt"))

    def test_listar_arquivos(self, temp_dir):
        writer = NexusWriter()
        writer.build_dir = temp_dir
        writer.criar_arquivo_autonomo("a.txt", "a")
        writer.criar_arquivo_autonomo("b.md", "b")
        lista = writer.listar_arquivos()
        assert len(lista["files"]) == 2

    def test_ler_arquivo(self, temp_dir):
        writer = NexusWriter()
        writer.build_dir = temp_dir
        writer.criar_arquivo_autonomo("readme.md", "# Nexus")
        result = writer.ler_arquivo("readme.md")
        assert result["status"] == "success"
        assert "# Nexus" in result["content"]