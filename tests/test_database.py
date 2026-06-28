import pytest
from core.database import NexusDatabase

class TestNexusDatabase:
    def test_adicionar_memoria(self, nexus_db):
        assert nexus_db.adicionar_memoria("lembrete", "fato") is True

    def test_listar_memorias(self, nexus_db):
        nexus_db.adicionar_memoria("teste A")
        nexus_db.adicionar_memoria("teste B")
        memorias = nexus_db.listar_memorias(limite=10)
        assert len(memorias) == 2
        assert "teste A" in memorias

    def test_limpar_historico(self, nexus_db):
        nexus_db.adicionar_memoria("x")
        assert nexus_db.limpar_historico_eterno() is True
        assert nexus_db.contar_memorias() == 0

    def test_contar_memorias_por_categoria(self, nexus_db):
        nexus_db.adicionar_memoria("f1", "fato")
        nexus_db.adicionar_memoria("p1", "preferencia")
        assert nexus_db.contar_memorias("fato") == 1
        assert nexus_db.contar_memorias("preferencia") == 1