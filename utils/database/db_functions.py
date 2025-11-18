import os
import pandas as pd
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Sequence, List

from pandas.io.sql import table_exists


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
    con.execute("PRAGMA foreign_keys = ON;")

    cur = con.cursor()
    try:
       yield con, cur
       con.commit()
    finally:
       con.close()


def db_pull():
    # randomly select question from question_db_original
    # if question already answered twice in same profession:
    #   tbl_row_delete(db= 'path/to/questions.db', table= 'questions')
    pass


def db_push(data: List[tuple] | List[str], db: str, table: str, statements:dict, user_add: bool = False, user_id: int | None = None) -> None:
    """
    Docstring!

    Args:
        data (List[tuple]):     ...
        db (str):               ...
        table (str):            ...
        statements (dict):      ...
        user_add (bool):        ...
        user_id (int | None):   ...

    Returns:
        Goal of calling the function is altering specific tables there is no return value.

    """

    placeholders = ','.join('?' for _ in range(len(data[0])))
    if db == os.getenv('DATA_DIR_QUESTIONS'):
        with db_conn(db) as (con, cur):
            try:
                c_names = ','.join(validate_rows_for_table_db(cur, table=table, rows=data))
                # check if potential entry already in backup table (print and log!)
                c_data = check_entry(cur=cur, data=data, statements=statements, col_names=c_names)

                # if not add question to original and backup
                exec_cmd = statements['INSERT_INTO'].format(table=table,
                                                            col_names=c_names,
                                                            tuple_q_marks=placeholders)
                exec_cmd_b = statements['INSERT_INTO'].format(table='backup',
                                                            col_names=c_names,
                                                            tuple_q_marks=placeholders)
                cur.executemany(exec_cmd, c_data)
                cur.executemany(exec_cmd_b, c_data)
                con.commit()

            except ValueError as e:
                print(f'Your data structure is invalid ValueError {e}')

    elif db == os.getenv('DATA_DIR'):
        with db_conn(db) as (con, cur):
            if user_add and table=='function':
                try:
                    # data_input =  [('First_name', 'Surname', 'years_in_the_function', 'function')]
                    # check if function in Function table:
                    names = ','.join(get_insert_columns(cur=cur, table=table))
                    if check_entry(cur=cur, data=data, statements=statements, col_names=names, table=table):
                        exec_cmd = statements['INSERT_IN_FUNCTION']
                        cur.execute(exec_cmd, data)
                        con.commit()


                    exec_cmd = statements['SELECT_PK_FUNCTION'].format(function=data[0])
                    pk_function = cur.execute(exec_cmd).fetchall()[0][0]
                    return pk_function
                    #
                    # check if user already in user + function table
                    # if yes return user_id (PK)
                    # else add user and return user_id (PK)
                    #   fetch last PK add 1
                    # return PK
                except:
                    pass

            else:
                anno_table_FK = user_id
                # pust to Annotations table (only condition: FK == PK in User_tabel present!)
                pass


    # --- survey.db
    #   --- user_table + Function_table combined (pushed once and remember User_table PK (Id))
    #   --- check if entry already present (ask user if already registered --> yes and "go back" options"
    #       --- if yes load that PK!
    #   --- Annotation_table
    pass


def tbl_row_delete():
    # if question was asked 2 for same function delete question in original!
    pass


def check_entry(cur: sqlite3.Cursor, data: List[tuple] | List[str], statements: dict,  col_names: str, table: str | None = None) -> List[tuple] | None:
    """
    Checking data entry into DB. Assures no duplication entries into connected database.

    Args:
        cur (sqlite3.Cursor): Sqlite DB connection cursor.
        data (List[tuple]): Entry data set to be tested.
        statements (dict): Dictionary of possible SQLite statements from INSERT to SELECT.
        col_names (str): string of comma separated colum names of table.
        table (str | None]: Table to connect to defaults to 'questions' - table if nothing specified.

    Returns:
        new data set without the entries already present in the current database/table.

    """

    # fetch all from table if None go for table == 'questions'
    exe_cmd = statements['SELECT_ALL'].format(column_names=col_names, table=table or 'questions')
    c_table = cur.execute(exe_cmd).fetchall()

    if isinstance(data[0], str):
        if any(row[0] == data[0] for row in c_table):
            return None
        return data

    else:
        # for row in data check if in table
        rows_delete = [idx for idx, row in enumerate(data) if row in c_table]
        new_data = [row for idx, row in enumerate(data) if idx not in rows_delete]
        # add to log indices with rows of not added entries which are already in tables
        print(f'find_print_statement: /utils/database/db_functions/check_entry\n'
              f'duplicated rows: {rows_delete}')

        return new_data


def get_insert_columns(cur: sqlite3.Cursor, table: str) -> List[str]:
    """
    Return the list of columns that should be provided for INSERT,
    skipping an autoincrement primary key named Id or question_id.
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


def preview_db(db: str, pre_dir:str | None = None, limit: int = 20) -> None:
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
            file.write(f'{pd.read_sql(f"SELECT * FROM {t} LIMIT {limit}", con)}')

    con.close()