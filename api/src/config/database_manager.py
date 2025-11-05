from abc import ABC, abstractmethod
from typing import Any, List

from ..errors import BaseException

class PackageNotInstalledException(BaseException):
    def __init__(self, *packages):
        message=f"Erro ao importar os seguintes pacotes: \n{', '.join(packages)}\nPor favor, instale-os para continuar."
        super().__init__(message)

class DatabaseManager(ABC):
    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def select(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def insert(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def update(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def delete(self, **kwargs) -> Any:
        pass


class SQLiteManager(DatabaseManager):
    def __init__(self, db_name: str) -> None:
        super().__init__()
        try:
            import sqlite3
        except ImportError:
            raise PackageNotInstalledException('sqlite3')
            
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cur = self.conn.cursor()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.conn.rollback()
        self.conn.commit()

    def select(self, **kwargs) -> Any:
        """
        Executa uma consulta SELECT no banco de dados, usando
        argumentos de palavra-chave para construir a cláusula WHERE.

        Argumentos de controle (são removidos de kwargs):
        - table (str): OBRIGATÓRIO. A tabela de onde selecionar.
        - options (List[str]): Opcional. Colunas a selecionar. Default: ['*'].
        
        Argumentos de filtro (tudo o que sobrar em kwargs):
        - Ex: id=1, nome='Alice' -> "WHERE id = ? AND nome = ?"
        """
    
        table: str = kwargs.pop('table', None)
        options: List[str] = kwargs.pop('options', ['*'])

        if not table:
            raise ValueError("O argumento 'table' é obrigatório para a função select.")

        cols = ", ".join(options)
        query = f"SELECT {cols} FROM {table}"
        
        where_clauses = []  # Lista para "id = ?", "email = ?", ...
        params = []         # Lista para [1, '...']

        for key, value in kwargs.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)

        # 5. Adicionar a cláusula WHERE à query (se houver filtros)
        if where_clauses:
            where_string = " AND ".join(where_clauses)
            query += f" WHERE {where_string}"

        # 6. Executar a query com segurança e retornar os dados
        # O self.cur.execute lida com a tupla de parâmetros com segurança
        self.cur.execute(query, tuple(params))
        
        return self.cur.fetchall()
        

    
    def insert(self, **kwargs) -> int:
        """
        Insere uma nova linha no banco de dados.

        Argumentos de controle (são removidos de kwargs):
        - table (str): OBRIGATÓRIO. A tabela onde inserir.
        
        Argumentos de dados (tudo o que sobrar em kwargs):
        - Ex: nome='Alice', status='ativo'
        """
        
        # 1. Extrair o argumento de "controle" (tabela)
        table: str = kwargs.pop('table', None)

        # 2. Validar
        if not table:
            raise ValueError("O argumento 'table' é obrigatório para a função insert.")
        
        if not kwargs:
            raise ValueError("Nenhum dado fornecido para inserção. (Ex: nome='Alice')")

        # 3. Construir a query
        # O que sobrou em kwargs são os dados (ex: {'nome': 'Alice', 'status': 'ativo'})
        
        # Pega os nomes das colunas: ('nome', 'status')
        columns = kwargs.keys()
        # Pega os valores: ('Alice', 'ativo')
        values = kwargs.values()

        # Cria a string de colunas: "nome, status"
        cols_sql = ", ".join(columns)
        
        # Cria os placeholders: "?, ?"
        placeholders_sql = ", ".join(["?"] * len(values))

        # Monta a query final
        query = f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders_sql})"

        # 4. Executar com segurança
        try:
            # Passamos os valores como uma tupla para o execute
            self.cur.execute(query, tuple(values))
            
            # 5. Retornar o ID da linha recém-criada
            return self.cur.lastrowid
            
        except Exception as e:
            # Em caso de erro, é bom reverter imediatamente
            self.conn.rollback()
            raise e # E então, levantar o erro para o usuário saber

    
    def update(self, **kwargs) -> int:
        """
        Atualiza uma ou mais linhas no banco de dados.

        Argumentos de controle (são removidos de kwargs):
        - table (str): OBRIGATÓRIO. A tabela onde atualizar.
        - data (dict): OBRIGATÓRIO. Um dicionário com as colunas e 
                       os novos valores (ex: {'nome': 'Novo'})
        
        Argumentos de filtro (tudo o que sobrar em kwargs):
        - Usado para construir a cláusula WHERE.
        - Ex: id=1, status='ativo' -> "WHERE id = ? AND status = ?"
        """
        
        # 1. Extrair os argumentos de "controle"
        table: str = kwargs.pop('table', None)
        data_to_set: dict = kwargs.pop('data', None)

        # 2. Validar
        if not table:
            raise ValueError("O argumento 'table' é obrigatório para a função update.")
        
        if not data_to_set or not isinstance(data_to_set, dict):
            raise ValueError("O argumento 'data' (um dict) é obrigatório "
                             "para informar o que deve ser alterado.")
        
        # O que sobrou em 'kwargs' são os filtros do WHERE
        # É PERIGOSO fazer UPDATE sem WHERE (altera a tabela inteira)
        if not kwargs:
            raise ValueError("UPDATE sem cláusula WHERE não é permitido por segurança. "
                             "Forneça ao menos um filtro (ex: id=1).")

        # 3. Construir a cláusula SET (com base no dict 'data')
        # Ex: "nome = ?, email = ?"
        set_clauses = [f"{key} = ?" for key in data_to_set.keys()]
        set_sql = ", ".join(set_clauses)

        # 4. Construir a cláusula WHERE (com base no que sobrou em 'kwargs')
        # Ex: "id = ? AND status = ?"
        where_clauses = [f"{key} = ?" for key in kwargs.keys()]
        where_sql = " AND ".join(where_clauses)

        # 5. Juntar os parâmetros (A ORDEM IMPORTA)
        # Primeiro vêm os valores do SET, depois os do WHERE
        params = tuple(list(data_to_set.values()) + list(kwargs.values()))

        # 6. Montar e executar a query
        query = f"UPDATE {table} SET {set_sql} WHERE {where_sql}"

        try:
            self.cur.execute(query, params)
            
            # Retorna o número de linhas que foram afetadas
            return self.cur.rowcount
        
        except Exception as e:
            self.conn.rollback()
            raise e

    
    def delete(self, **kwargs) -> int:
        """
        Exclui uma ou mais linhas do banco de dados.

        Argumentos de controle (são removidos de kwargs):
        - table (str): OBRIGATÓRIO. A tabela de onde excluir.
        
        Argumentos de filtro (tudo o que sobrar em kwargs):
        - Usado para construir a cláusula WHERE.
        - Ex: id=1, status='inativo' -> "WHERE id = ? AND status = ?"
        """
        
        # 1. Extrair o argumento de "controle"
        table: str = kwargs.pop('table', None)

        # 2. Validar
        if not table:
            raise ValueError("O argumento 'table' é obrigatório para a função delete.")
        
        # 3. ⚠️ TRAVA DE SEGURANÇA ⚠️
        # Se 'kwargs' estiver vazio após o pop, significa que NENHUM
        # filtro (WHERE) foi fornecido. Impedimos isso.
        if not kwargs:
            raise ValueError("DELETE sem cláusula WHERE não é permitido por segurança. "
                             "Forneça ao menos um filtro (ex: id=1).")

        # 4. Construir a cláusula WHERE (com base no que sobrou em 'kwargs')
        # Ex: "id = ? AND status = ?"
        where_clauses = [f"{key} = ?" for key in kwargs.keys()]
        where_sql = " AND ".join(where_clauses)
        
        # 5. Coletar os parâmetros
        params = tuple(kwargs.values())

        # 6. Montar e executar a query
        query = f"DELETE FROM {table} WHERE {where_sql}"

        try:
            self.cur.execute(query, params)
            
            # Retorna o número de linhas que foram afetadas
            return self.cur.rowcount
        
        except Exception as e:
            self.conn.rollback()
            raise e
