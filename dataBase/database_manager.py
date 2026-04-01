import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Union
import os


class DatabaseManager:
    """
    Gerencia o banco de dados SQLite para armazenar perguntas e métricas de tokens.
    """
    
    def __init__(self, db_path: str = "dataBase/agent_metrics.db"):
        """
        Inicializa o gerenciador do banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_database()
    
    def _ensure_db_directory(self):
        """Garante que o diretório do banco de dados existe."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _get_connection(self):
        """Retorna uma conexão com o banco de dados."""
        return sqlite3.connect(self.db_path)
    
    def _get_brazil_timestamp(self):
        """
        Retorna o timestamp atual no fuso horário do Brasil (UTC-3).
        
        Returns:
            String com timestamp no formato SQLite
        """
        # Obtém o tempo atual em UTC
        now_utc = datetime.now(timezone.utc)
        
        # Converte para o fuso horário do Brasil (UTC-3)
        brasil_offset = timedelta(hours=-3)
        brasil_tz = timezone(brasil_offset)
        now_brasil = now_utc.astimezone(brasil_tz)
        
        # Formata para o padrão SQLite
        return now_brasil.strftime('%Y-%m-%d %H:%M:%S')
    
    def _get_brazil_datetime(self):
        """
        Retorna o datetime atual no fuso horário do Brasil (UTC-3).
        
        Returns:
            datetime object com timezone do Brasil
        """
        now_utc = datetime.now(timezone.utc)
        brasil_offset = timedelta(hours=-3)
        brasil_tz = timezone(brasil_offset)
        return now_utc.astimezone(brasil_tz)
    
    def _initialize_database(self):
        """Cria as tabelas necessárias se não existirem."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabela principal de interações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                model_id TEXT,
                session_id TEXT,
                response_time_ms INTEGER
            )
        """)
        
        # Índices para melhorar performance de consultas
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON interactions(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session 
            ON interactions(session_id)
        """)
        
        conn.commit()
        conn.close()
    
    def save_interaction(
        self,
        question: str,
        answer: str,
        input_tokens: int,
        output_tokens: int,
        model_id: str = None,
        session_id: str = None,
        response_time_ms: int = None
    ) -> int:
        """
        Salva uma interação no banco de dados.
        
        Args:
            question: Pergunta feita pelo usuário
            answer: Resposta gerada pelo agente
            input_tokens: Número de tokens de entrada
            output_tokens: Número de tokens de saída
            model_id: Identificador do modelo usado
            session_id: Identificador da sessão
            response_time_ms: Tempo de resposta em milissegundos
            
        Returns:
            ID da interação inserida
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        total_tokens = input_tokens + output_tokens
        
        # SEMPRE usa timestamp do Brasil
        timestamp = self._get_brazil_timestamp()
        # print(f"[INFO] Salvando interação com timestamp Brasil: {timestamp}")
        
        cursor.execute("""
            INSERT INTO interactions 
            (timestamp, question, answer, input_tokens, output_tokens, total_tokens, 
            model_id, session_id, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, question, answer, input_tokens, output_tokens, total_tokens,
            model_id, session_id, response_time_ms))
        
        interaction_id = cursor.lastrowid
        
        # Debug: verifica o que foi inserido
        cursor.execute("SELECT timestamp FROM interactions WHERE id = ?", (interaction_id,))
        # inserted_timestamp = cursor.fetchone()[0]
        # print(f"[DEBUG] Timestamp inserido: {inserted_timestamp}")
        
        conn.commit()
        conn.close()
        
        return interaction_id
    
    def delete_interactions_by_ids(self, ids: List[int]) -> int:
        """
        Remove interações baseado em uma lista de IDs.
        
        Args:
            ids: Lista de IDs para remover
            
        Returns:
            Número de interações removidas
        """
        if not ids:
            return 0
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Cria placeholders para a query (?, ?, ?, ...)
        placeholders = ','.join('?' for _ in ids)
        
        cursor.execute(f"""
            DELETE FROM interactions 
            WHERE id IN ({placeholders})
        """, ids)
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    
    def get_total_tokens(self) -> Dict[str, int]:
        """
        Retorna o total de tokens consumidos.
        
        Returns:
            Dicionário com totais de input, output e total de tokens
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(input_tokens) as total_input,
                SUM(output_tokens) as total_output,
                SUM(total_tokens) as total
            FROM interactions
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            "total_input": result[0] or 0,
            "total_output": result[1] or 0,
            "total": result[2] or 0
        }
    
    def get_average_tokens(self) -> Dict[str, float]:
        """
        Retorna a média de tokens por interação.
        
        Returns:
            Dicionário com médias de input, output e total de tokens
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                AVG(input_tokens) as avg_input,
                AVG(output_tokens) as avg_output,
                AVG(total_tokens) as avg_total,
                COUNT(*) as total_interactions
            FROM interactions
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            "avg_input": round(result[0], 2) if result[0] else 0,
            "avg_output": round(result[1], 2) if result[1] else 0,
            "avg_total": round(result[2], 2) if result[2] else 0,
            "total_interactions": result[3] or 0
        }
    
    def get_recent_questions(self, limit: int = 50) -> List[Tuple]:
        """
        Retorna as perguntas mais recentes.
        
        Args:
            limit: Número máximo de perguntas a retornar
            
        Returns:
            Lista de tuplas (id, timestamp, question, input_tokens, output_tokens)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, question, input_tokens, output_tokens
            FROM interactions
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_all_questions(self) -> List[str]:
        """
        Retorna todas as perguntas armazenadas.
        Útil para análise de perguntas frequentes.
        
        Returns:
            Lista de strings com todas as perguntas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT question FROM interactions ORDER BY timestamp")
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_interaction_count(self) -> int:
        """
        Retorna o número total de interações.
        
        Returns:
            Número de interações
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM interactions")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_statistics_by_date(self, days: int = 7) -> List[Dict]:
        """
        Retorna estatísticas agrupadas por data.
        
        Args:
            days: Número de dias para análise
            
        Returns:
            Lista de dicionários com estatísticas diárias
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Calcula a data limite usando horário do Brasil
        brasil_now = self._get_brazil_datetime()
        cutoff_date = brasil_now - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as interactions,
                SUM(input_tokens) as total_input,
                SUM(output_tokens) as total_output,
                AVG(response_time_ms) as avg_response_time
            FROM interactions
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, (cutoff_str,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "date": row[0],
                "interactions": row[1],
                "total_input": row[2],
                "total_output": row[3],
                "avg_response_time": round(row[4], 2) if row[4] else 0
            })
        
        conn.close()
        return results
    
    def clear_old_data(self, days: int = 90):
        """
        Remove dados mais antigos que o número de dias especificado.
        
        Args:
            days: Número de dias para manter
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Calcula a data limite usando horário do Brasil
        brasil_now = self._get_brazil_datetime()
        cutoff_date = brasil_now - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            DELETE FROM interactions
            WHERE timestamp < ?
        """, (cutoff_str,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count