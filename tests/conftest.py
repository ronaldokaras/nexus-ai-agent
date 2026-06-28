import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Cria um diretório temporário para testes de arquivos."""
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp

@pytest.fixture
def nexus_db():
    """Fornece uma instância do banco de dados com arquivo temporário."""
    from core.database import NexusDatabase
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db = NexusDatabase(db_path=tmp.name)
        yield db
        db.limpar_historico_eterno()
        os.unlink(tmp.name)

@pytest.fixture
def nexus_memory(nexus_db):
    """Fornece uma instância do gerenciador de memória."""
    from core.memory import NexusMemory
    memory = NexusMemory(limite_memoria=10)
    memory.db = nexus_db  # usa o banco temporário
    return memory