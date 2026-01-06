import os
import random
import logging

import pandas as pd
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Sequence, List

log = logging.getLogger(__name__)

@contextmanager
def db_conn(db: str):
    """
    Open a SQLite database connection with foreign key
    enforcement enabled, and return both the connection
    and a cursor object.

    Args:
        db (str): Path to the SQLite database file.
    """

    con = sqlite3.connect(db)
    # ✔ Enable foreign key constraints (SQLite does NOT enable them by default)
    con.execute('PRAGMA foreign_keys = ON;')

    cur = con.cursor()
    try:
       yield con, cur
       con.commit()
    finally:
       con.close()


def sampling(statements: dict, j_file: List[dict], usr_id: int, fun_id: int) -> dict:
    """
    Select a suitable question from 'j_file' for annotation.

    The function randomly samples questions and checks the annotations table to ensure:
    -   Questions with 0 annotations are allowed
    -   Questions with 1 annotation are allowed only if it was annotated by a different user
        but for the same function (func_id).
    -   Questions with 2 annotations are removed from 'j_file'

    It retries up to 'len(j_file) * 3' attempts and raises an error if no suitable question can be found.

    Args:
        statements (dict):
            SQL statement mapping. Must include at least 'SELECT_JOIN' which returns annotation rows
            for a given question id.
        j_file (List[dict]):
            List of question dictionaries. Each dict must contain a 'q_id' key.
            The list may be modified in-place (questions removed when already used twice).
        usr_id (int):
            Primary key of the current user (annotator).
        fun_id (int):
            Primary key of the current function/task the user is annotating for.

    Returns:
        dict: The selected question dictionary from 'j_file'.

    Raises:
        RuntimeError:
            If 'j_file' becomes empty, or if no suitable question is found after serveral attempts.
        ValueError:
            If a question has more than 2 annotations (unexpected database state).
    """

    max_attempts = len(j_file) * 3
    for _ in range (max_attempts):
        if not j_file:
            raise RuntimeError('No questions left in j_file.')

        question = random.choice(j_file)
        q_rand_id = question['q_id']

        with db_conn(os.getenv('DATA_DIR')) as (con, cur):
            anno_a = cur.execute(statements['SELECT_JOIN'], [q_rand_id]).fetchall()

        # If question not in annotation table:
        if len(anno_a) == 0:
            log.info('Question %s is not in annotation table yet', q_rand_id)
            return question

        # If question is annotated once
        elif len(anno_a) == 1:
            # If same function but different User annotate!
            annotator, ano_fun = anno_a[0][1], anno_a[0][4]
            log.info(
                'Question id: %s already annotated:\n user_id=%s (current=%s), func_id=%s (current=%s)',
                q_rand_id, annotator, usr_id, ano_fun, fun_id)
            if annotator != usr_id and ano_fun == fun_id:
                log.info(' ---  SAME FUNCTION BUT DIFFERENT USER ---')
                return question

        elif len(anno_a) == 2:
            log.warning(f'Question_id: {q_rand_id}, has been used twice already so it will be deleted!')
            j_file.remove(question)

        else:
            raise ValueError('Something went wrong. Questions can not annotated more than twice.')

    raise RuntimeError('Could not find a suitable question after several attempts.')


def db_push(data: List[tuple] | List[str], db: str, table: str, statements:dict, user_add: bool = False) -> int | None:
    """
    Insert data into a SQLite database table with duplicate protection.

    This function is a central insert helper for three scenarios:
    -   Adding a new function into 'function' table (user_add = True, table = 'function')
        and returning the function primary key.
    -   Adding a new user into 'user' table (user_add = True, table = 'user')
        and returning the user primary key.
    -   Adding an annotation into the 'annotations' table (user_add = False, table = 'annotations')
        no pk is returned

    Duplicate checks are performed via func: check_entry before inserts.

    Notes:
        - Only runs when "db == os.getenv('DATA_DIR')"
        - The function commits inside the context manager when inserts happen.
        - Errors are logged!

    Args:
        data (List[tuple] | List [str]):
            Payload to insert.
        db (str):
            Path to the SQLite database file.
        table (str):
            Target table name. ('function', 'user' or 'annotations')
        statements (dict):
            SQL statement mapping from /config/statements.yml
        user_add (bool):
            Controls whether this is a user/function insert (True) or annotation insert (False).

    Returns:
        int | None:
            - Returns the primary key for inserted or existing 'user' or 'function' rows.
            - Returns 'None' for annotation inserts or when the function does not hit any branch.
    """

    if db == os.getenv('DATA_DIR'):
        with db_conn(db) as (con, cur):
            if user_add and table == 'function':
                try:
                    # check if function in Function table:
                    names = ','.join(get_insert_columns(cur=cur, table=table))
                    if check_entry(cur=cur, data=data, statements=statements, col_names=names, table=table):
                        exec_cmd = statements['INSERT_IN_FUNCTION']
                        cur.execute(exec_cmd, data)
                        con.commit()
                    else:
                        log.info('function already present')
                    exec_cmd = statements['SELECT_PK_FUNCTION'].format(function=data[0])
                    pk_function = cur.execute(exec_cmd).fetchone()[0]
                    return pk_function
                except ValueError as e:
                    log.error(f'Function could not be added FormatError: {e}')

            if user_add and table == 'user':
                try:
                    # check if user already in User table:
                    names = ','.join(get_insert_columns(cur=cur, table=table))
                    if check_entry(cur=cur, data=data, statements=statements, col_names=names, table=table):
                        exec_cmd = statements['INSERT_IN_USER']
                        cur.execute(exec_cmd, data[0])
                        con.commit()
                    else:
                        log.info('user already present')

                    exec_cmd = statements['SELECT_PK_USER']
                    pk_user = cur.execute(exec_cmd, data[0]).fetchone()[0]
                    return pk_user
                except ValueError as e:
                    log.error(f'User could not be added FormatError: {e}')

            elif not user_add and table == 'annotations':
                try:
                    # check if annotation already in annotations table
                    names = ','.join(get_insert_columns(cur=cur, table=table))
                    if not check_entry(cur=cur, data=data, statements=statements, col_names=names, table=table):
                        raise RuntimeError('Logic error: entry check failed since Annotation already in the table!')

                    # Insert into annotation table
                    exec_cmd = statements['INSERT_IN_ANNOTATION']
                    cur.execute(exec_cmd, data[0])
                except ValueError as e:
                    log.error(f'Annotation could not be added FormatError: {e}')
                except RuntimeError as e:
                    log.error(f"Annotation could not be added RuntimeError: {e}")

def get_user_pk_and_func_by_username(statements: dict, username: str) -> tuple[int, int] | None:
    """
    Look up a user by username and return the user and function primary keys.

    The username is normalized by stripping whitespace and converting to lowercase.
    If the normalized username is empty or not found in the database, 'None' is returned.

    Args:
        statements (dict):
            SQL statement mapping from /config/statements.yml
        username (str):
            Username to search for.

    Returns:
        tuple[int, int] | None:
            (user_pk, func_pk) if user exists, otherwise 'None'
    """

    username = (username or "").strip().lower()
    if not username:
        return None

    with db_conn(os.getenv('DATA_DIR')) as (con, cur):
        row = cur.execute(statements['SELECT_USER_BY_USERNAME'], (username,)).fetchone()

    if not row:
        return None

    user_pk, func_pk = int(row[0]), int(row[1])
    return user_pk, func_pk


def check_entry(cur: sqlite3.Cursor, data: List[tuple] | List[str], statements: dict,  col_names: str, table: str | None = None) -> List[tuple] | None:
    """
    Check whether given entries already exist in a table and filter duplicates.

    The function loads all rows from the given table and compares them against the provided 'data'

    Behavior depends on the 'data' input shape:
    -   If 'data[0]' is a 'str':
        Treats it as a single value to compare against the first column of each row.
        Returns 'None' if it already exists, otherwise returns 'data' unchanged.
    -   If 'data' is a list of tuples:
        Removes rows that are already present in the table and returns remaining rows.
        If all rows are duplicates, an empty list is returned.

    Args:
        cur (sqlite3.Cursor):               Active SQLite cursor.
        data (List[tuple] | List[str]):     Entry Data to check.
        statements (dict):                  SQL statement mapping from /config/statements.yml
        col_names (str):                    Comma-separated column names to fetch from the table for the dup. check.
        table (str | None):                 Table name to query. If 'None' SQL template handles it.

    Returns:
        List[tuple] | None:
            - 'None' if a single string entry already exists.
            - Otherwise, a filtered list containing only entries not yet present.

    Raises:
        ValueError:
            If the function cannot interpret the provided 'data' type/shape.
    """

    # fetch all from table
    exe_cmd = statements['SELECT_ALL'].format(column_names=col_names, table=table)
    c_table = cur.execute(exe_cmd).fetchall()

    if isinstance(data[0], str):
        if any(row[0] == data[0] for row in c_table):
            return None
        return data

    elif isinstance(data, list):
        # for row in data check if in table
        rows_delete = [idx for idx, row in enumerate(data) if row in c_table]
        new_data = [row for idx, row in enumerate(data) if idx not in rows_delete]
        # add to log indices with rows of not added entries which are already in tables
        return new_data

    raise ValueError(f'Entry could not be checked with check_entry() "{type(data)}" could not be processed')


def get_insert_columns(cur: sqlite3.Cursor, table: str) -> List[str]:
    """
    Get insertable column names for a table, excluding autoincrement primary keys.

    The function inspects the table schema and returns all column names except a pk key
    column named 'id' or 'question_id'.

    Args:
        cur (sqlite3.Cursor):   Active SQLite cursor.
        table (str):            Table name to inspect.

    Returns:
        List[str]: Column names that should be provided in an INSERT statement.
    """

    cur.execute(f"PRAGMA table_info({table})")
    rows = cur.fetchall()
    cols = [name for cid, name, col_type, notnull, dflt_value, pk in rows
            if not (pk == 1 and name.lower() in ('id', 'question_id'))]

    return cols


def validate_rows_for_table_db(cur: sqlite3.Cursor, table: str, rows: Sequence[Sequence]) -> List[str]:
    """
    Validate rows by checking length against columns from the database.
    Returns number of rows in the input data

    Args:
        cur (sqlite3.Cursor): Sqlite DB connection cursor.
        table (str): table name of sqlite DB to connect to.
        rows (Sequence[Sequence]): Data entries, added to the table.

    Returns:
        List of column names for table of interest
    """

    columns = get_insert_columns(cur, table)
    expected = len(columns)
    errors = [f'Row {idx} has {len(row)} values, expected {expected}' for idx, row in enumerate(rows) if len(row) != expected]

    if errors:
        raise ValueError("Invalid rows for table {table}: " + " | ".join(errors))

    return columns


def preview_db(db: str, pre_dir:str | None = None, limit: int | None = 100) -> None:
    """
        Preview the contents of all tables in a SQLite database.

        This function connects to the given SQLite file, lists all tables,
        and prints the first few rows of each table using pandas for easy viewing.

        Args:
            db (str):
                Path to the SQLite `.db` file.
            pre_dir (str | None):
                Path to previews directory. Defaults to $PREVIEW_DIR if not specified.
            limit (int, optional):
                Maximum number of rows to display per table.
                Defaults to 5.

        Prints:
            - A list of all table names found in the database.
            - For each table, a pandas DataFrame showing up to `limit` rows.
        """

    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]

    pre_dir = Path(pre_dir or os.getenv('PREVIEW_DIR'))
    pre_dir.mkdir(parents=True, exist_ok=True)

    for t in tables:
        with open (f'{pre_dir / t}.txt', 'w') as file:
            if limit is None:
                df = pd.read_sql(f'SELECT * from {t}', con)
            else:
                df = pd.read_sql(f'SELECT * FROM {t} LIMIT {limit}', con)
            df.to_string(buf=file, max_cols=None, index=False)

    con.close()