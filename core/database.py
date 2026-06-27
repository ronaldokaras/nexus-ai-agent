"""
database.py - Gerenciamento do banco de dados SQLite do Nexus Agent
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Union

# Configura logger
logger = logging.getLogger(__name__)


class NexusDatabase:
    """
    Gerencia a persistência do Nexus Agent usando SQLite.
    Armazena memórias, fatos e preferências.
    """
    
    def __init__(self, db_path: str = "data/nexus.db"):
        """
        Inicializa o banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        
        # Garante que o diretório existe
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        self._criar_tabela()
        self._criar_indices()
        logger.info(f"Banco de dados inicializado: {self.db_path}")

    def _conectar(self) -> sqlite3.Connection:
        """Retorna uma conexão com o banco de dados."""
        return sqlite3.connect(self.db_path)

    def _criar_tabela(self) -> None:
        """Cria a estrutura de memórias se não existir."""
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memorias (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        categoria TEXT NOT NULL, 
                        conteudo TEXT NOT NULL,
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.debug("Tabela 'memorias' verificada/criada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar tabela: {e}")
            raise

    def _criar_indices(self) -> None:
        """Cria índices para otimizar consultas."""
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memorias_categoria 
                    ON memorias(categoria)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memorias_data 
                    ON memorias(data_criacao DESC)
                """)
                conn.commit()
                logger.debug("Índices criados/verificados com sucesso")
        except Exception as e:
            logger.warning(f"Não foi possível criar índices: {e}")

    # ==================== MÉTODO DE EXECUÇÃO GENÉRICA ====================
    
    def executar_query(
        self, 
        query: str, 
        params: tuple = (), 
        fetch: bool = False
    ) -> Union[bool, List[Tuple], List[str]]:
        """
        Executa comandos SQL de forma segura.
        
        Args:
            query: String SQL com placeholders (?)
            params: Tupla de parâmetros para a query
            fetch: Se True, retorna os resultados (para SELECT)
                   Se False, retorna bool indicando sucesso
            
        Returns:
            - Se fetch=True: Lista de resultados (cada resultado é uma tupla)
            - Se fetch=False: bool indicando sucesso/fracasso
        """
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch:
                    resultados = cursor.fetchall()
                    conn.commit()
                    return resultados
                else:
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            logger.debug(f"Query: {query[:200]}... | Params: {params}")
            if fetch:
                return []
            return False

    # ==================== MÉTODOS ESPECÍFICOS ====================
    
    def adicionar_memoria(self, conteudo: str, categoria: str = "fato") -> bool:
        """
        Insere um novo fato ou preferência no banco.
        
        Args:
            conteudo: O conteúdo da memória
            categoria: Categoria da memória (fato, preferencia, etc.)
            
        Returns:
            bool: True se adicionado com sucesso
        """
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO memorias (categoria, conteudo) VALUES (?, ?)",
                    (categoria, conteudo)
                )
                conn.commit()
                logger.debug(f"Memória adicionada: {conteudo[:50]}...")
                return True
        except Exception as e:
            logger.error(f"Erro ao adicionar memória: {e}")
            return False

    def listar_memorias(
        self, 
        limite: Optional[int] = 15, 
        categoria: Optional[str] = None
    ) -> List[str]:
        """
        Recupera os fatos mais recentes para o contexto do agente.
        
        Args:
            limite: Número máximo de resultados. Se None, sem limite.
            categoria: Filtrar por categoria específica (opcional)
            
        Returns:
            List[str]: Lista de conteúdos das memórias
        """
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                
                if categoria:
                    query = """
                        SELECT conteudo FROM memorias 
                        WHERE categoria = ?
                        ORDER BY id DESC
                    """
                    params = [categoria]
                else:
                    query = """
                        SELECT conteudo FROM memorias 
                        ORDER BY id DESC
                    """
                    params = []
                
                if limite is not None:
                    query += " LIMIT ?"
                    params.append(limite)
                
                cursor.execute(query, params)
                resultados = cursor.fetchall()
                return [row[0] for row in resultados if row]
                
        except Exception as e:
            logger.error(f"Erro ao listar memórias: {e}")
            return []

    def limpar_historico_eterno(self) -> bool:
        """
        Apaga todos os registros do banco (memória de longo prazo).
        
        Returns:
            bool: True se apagado com sucesso
        """
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memorias")
                conn.commit()
                logger.info("Histórico persistente limpo com sucesso")
                return True
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
            return False

    def contar_memorias(self, categoria: Optional[str] = None) -> int:
        """
        Conta o número de memórias no banco.
        
        Args:
            categoria: Filtrar por categoria (opcional)
            
        Returns:
            int: Número de memórias
        """
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                
                if categoria:
                    cursor.execute(
                        "SELECT COUNT(*) FROM memorias WHERE categoria = ?",
                        (categoria,)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM memorias")
                
                resultado = cursor.fetchone()
                return resultado[0] if resultado else 0
                
        except Exception as e:
            logger.error(f"Erro ao contar memórias: {e}")
            return 0

    def buscar_por_conteudo(self, termo: str, limite: int = 10) -> List[Tuple]:
        """
        Busca memórias por similaridade de conteúdo.
        
        Args:
            termo: Termo a buscar
            limite: Número máximo de resultados
            
        Returns:
            List[Tuple]: Lista de (id, conteudo, data_criacao)
        """
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, conteudo, data_criacao 
                    FROM memorias 
                    WHERE conteudo LIKE ? 
                    ORDER BY data_criacao DESC 
                    LIMIT ?
                """, (f"%{termo}%", limite))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Erro ao buscar por conteúdo: {e}")
            return []

    def deletar_memoria_por_id(self, memoria_id: int) -> bool:
        """
        Deleta uma memória específica pelo ID.
        
        Args:
            memoria_id: ID da memória a deletar
            
        Returns:
            bool: True se deletado com sucesso
        """
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memorias WHERE id = ?", (memoria_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Erro ao deletar memória {memoria_id}: {e}")
            return False

    def obter_estatisticas(self) -> dict:
        """
        Retorna estatísticas do banco de dados.
        
        Returns:
            dict: Estatísticas como total, categorias, etc.
        """
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM memorias")
                total = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT categoria, COUNT(*) 
                    FROM memorias 
                    GROUP BY categoria
                """)
                por_categoria = dict(cursor.fetchall())
                
                cursor.execute("""
                    SELECT MAX(data_criacao) FROM memorias
                """)
                ultima_memoria = cursor.fetchone()[0]
                
                return {
                    "total": total,
                    "por_categoria": por_categoria,
                    "ultima_memoria": ultima_memoria,
                    "db_path": self.db_path
                }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}