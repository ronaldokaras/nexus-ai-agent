"""
memory.py - Gerenciamento de memória persistente do Nexus Agent
"""

import logging
from typing import List, Optional

from core.database import NexusDatabase

# Configura logger
logger = logging.getLogger(__name__)


class NexusMemory:
    """
    Gerencia a memória de longo prazo do Nexus Agent usando SQLite.
    Mantém um limite de fatos para evitar crescimento infinito.
    """
    
    def __init__(self, limite_memoria: int = 50):
        """
        Inicializa a memória do Nexus.
        
        Args:
            limite_memoria: Número máximo de fatos a manter (padrão: 50)
        """
        self.db = NexusDatabase()
        self.limite_memoria = limite_memoria
        logger.info(f"Memória de longo prazo inicializada com limite de {limite_memoria} fatos")

    def add_fact(self, fact: str) -> bool:
        """
        Adiciona um fato à memória persistente.
        
        Args:
            fact: O fato a ser armazenado
            
        Returns:
            bool: True se adicionado com sucesso, False caso contrário
        """
        if not fact or len(fact.strip()) == 0:
            logger.warning("Tentativa de adicionar fato vazio ignorada")
            return False
        
        try:
            self.db.adicionar_memoria(fact, categoria="fato")
            self._prune_database()  # Executa limpeza automática
            logger.debug(f"Fato adicionado: {fact[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar fato: {e}")
            return False

    def _prune_database(self) -> None:
        """
        Mantém apenas os X fatos mais recentes, deletando os antigos.
        Usa query parametrizada para evitar SQL injection.
        """
        try:
            query = """
            DELETE FROM memorias 
            WHERE id NOT IN (
                SELECT id FROM memorias 
                ORDER BY data_criacao DESC 
                LIMIT ?
            )
            """
            
            try:
                self.db.executar_query(query, (self.limite_memoria,))
            except TypeError:
                logger.warning("Database não suporta parâmetros, usando método alternativo seguro")
                self._prune_database_alternativo()
                
        except Exception as e:
            logger.error(f"Erro na poda do banco: {e}")

    def _prune_database_alternativo(self) -> None:
        """
        Método alternativo de poda para databases que não suportam parâmetros.
        Obtém os IDs a manter e deleta o resto.
        """
        try:
            select_query = f"""
            SELECT id FROM memorias 
            ORDER BY data_criacao DESC 
            LIMIT {self.limite_memoria}
            """
            
            resultados = self.db.executar_query(select_query, fetch=True)
            
            if not resultados:
                return
            
            ids_manter = [str(row[0]) for row in resultados]
            
            if ids_manter:
                ids_str = ','.join(ids_manter)
                delete_query = f"""
                DELETE FROM memorias 
                WHERE id NOT IN ({ids_str})
                """
                self.db.executar_query(delete_query)
                
        except Exception as e:
            logger.error(f"Erro na poda alternativa: {e}")

    def get_context(self, limite: int = 20) -> str:
        """
        Recupera o contexto da memória para o prompt da IA.
        
        Args:
            limite: Número máximo de fatos a recuperar (padrão: 20)
            
        Returns:
            str: Texto formatado com os fatos mais recentes
        """
        try:
            try:
                fatos_db = self.db.listar_memorias(limite=limite)
            except TypeError:
                fatos_db = self.db.listar_memorias()
                if fatos_db and len(fatos_db) > limite:
                    fatos_db = fatos_db[:limite]
            
            if not fatos_db:
                return ""
            
            fatos_ordenados = list(reversed(fatos_db))
            facts_text = "\n".join([f"- {f}" for f in fatos_ordenados])
            
            return f"\n\n[MEMÓRIA DE LONGO PRAZO]:\n{facts_text}"
            
        except Exception as e:
            logger.error(f"Erro ao recuperar contexto: {e}")
            return ""

    def limpar_tudo(self) -> str:
        """
        Apaga toda a memória de longo prazo do banco de dados.
        
        Returns:
            str: Mensagem de confirmação
        """
        try:
            self.db.limpar_historico_eterno()
            logger.info("Memória de longo prazo foi limpa")
            return "Memória de longo prazo apagada com sucesso. O agente está pronto para novo contexto."
        except Exception as e:
            logger.error(f"Erro ao limpar memória: {e}")
            return "Não foi possível apagar a memória. Tente novamente."

    def clear_all(self) -> str:
        """
        Alias em inglês para limpar_tudo().
        """
        return self.limpar_tudo()

    def get_fact_count(self) -> int:
        """
        Retorna o número total de fatos na memória.
        
        Returns:
            int: Quantidade de fatos armazenados
        """
        try:
            query = "SELECT COUNT(*) FROM memorias WHERE categoria = 'fato'"
            resultado = self.db.executar_query(query, fetch=True)
            if resultado:
                return resultado[0][0]
            return 0
        except Exception as e:
            logger.error(f"Erro ao contar fatos: {e}")
            return 0

    def get_recent_facts(self, quantidade: int = 10) -> List[str]:
        """
        Retorna os fatos mais recentes como lista.
        
        Args:
            quantidade: Número de fatos a retornar
            
        Returns:
            List[str]: Lista dos fatos mais recentes
        """
        try:
            fatos_db = self.db.listar_memorias(limite=quantidade)
            return list(reversed(fatos_db)) if fatos_db else []
        except Exception as e:
            logger.error(f"Erro ao obter fatos recentes: {e}")
            return []