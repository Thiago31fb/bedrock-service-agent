"""
Módulo de gerenciamento de banco de dados.
"""

# O arquivo se chama database_manager.py, então importamos dele
try:
    from .database_manager import DatabaseManager
    __all__ = ['DatabaseManager']
except ImportError:
    # Se não existir database_manager.py, tenta database.py
    try:
        from .database_manager import DatabaseManager
        __all__ = ['DatabaseManager']
    except ImportError as e:
        print(f"Erro ao importar DatabaseManager: {e}")
        print("Certifique-se de que existe dataBase/database_manager.py ou dataBase/database.py")
        raise