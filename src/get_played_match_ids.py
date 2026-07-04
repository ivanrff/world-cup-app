# %%
import sqlite3
from pathlib import Path

def get_played_match_ids(log_func=None):

    # 1. Pega o caminho absoluto de onde ESTE arquivo atual está
    current_file = Path(__file__).resolve()

    # 2. Sobe os níveis necessários para chegar na raiz do projeto
    # Se o arquivo está em 'meu_projeto/src/seu_script.py', o .parent.parent volta para 'meu_projeto/'
    project_root = current_file.parent.parent

    # 3. Constrói o caminho absoluto exato até o banco de dados
    db_path = project_root / "data" / "db" / "world_cup.db"

    # Se o banco de dados ainda não existir fisicamente, o SQLite cria um arquivo vazio.
    # Vamos checar se o arquivo realmente existe e tem dados antes de falhar silenciosamente.
    if not db_path.exists():
        if log_func:
            log_func(f"[WARNING] Database not found in: {db_path}")
        return []
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT opta_match_id
            FROM opta_snapshots
            WHERE match_status == 'Played'
        """)
        # O fetchall retorna uma lista de tuplas ex: [('id1',), ('id2',)]
        # Usamos uma list comprehension para extrair o texto limpo da tupla
        future_ids = [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # Prevenção caso a tabela ainda não exista no banco de dados novo
        if log_func:
            log_func("[WARNING] Table not found in the database.")
        future_ids = []
    finally:
        conn.close()

    return future_ids
# %%
