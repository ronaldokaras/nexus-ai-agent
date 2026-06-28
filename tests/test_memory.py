import pytest
from core.memory import NexusMemory

class TestNexusMemory:
    def test_add_fact(self, nexus_memory):
        assert nexus_memory.add_fact("Python é uma linguagem") is True

    def test_get_context(self, nexus_memory):
        nexus_memory.add_fact("Fato A")
        nexus_memory.add_fact("Fato B")
        context = nexus_memory.get_context(limite=5)
        assert "Fato A" in context
        assert "Fato B" in context

    def test_clear_all(self, nexus_memory):
        nexus_memory.add_fact("teste")
        result = nexus_memory.limpar_tudo()
        assert "apagada" in result.lower()
        assert nexus_memory.get_fact_count() == 0

    def test_get_fact_count(self, nexus_memory):
        nexus_memory.add_fact("fato 1")
        nexus_memory.add_fact("fato 2")
        assert nexus_memory.get_fact_count() == 2