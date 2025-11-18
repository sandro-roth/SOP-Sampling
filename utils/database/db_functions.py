import os
import pandas as pd
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Sequence, List


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

def db_push(data: List[tuple], db: str, table: str, statements:dict) -> None:
    # Connect to questions database
    placeholders = ','.join('?' for _ in range(len(data[0])))
    if db == os.getenv('DATA_DIR_QUESTIONS'):
        with db_conn(db) as (con, cur):
            try:
                c_names = ','.join(validate_rows_for_table_db(cur, table=table, rows=data))
                # check if potential entry already in backup table (print and log!)

                # if not add question to original and backup
                exec_cmd = statements['INSERT_INTO'].format(table='questions',
                                                            col_names=c_names,
                                                            tuple_q_marks=placeholders)
                exec_cmd_b = statements['INSERT_INTO'].format(table='backup',
                                                            col_names=c_names,
                                                            tuple_q_marks=placeholders)
                cur.executemany(exec_cmd, data)
                cur.executemany(exec_cmd_b, data)
                con.commit()

            except ValueError as e:
                print(f'Your data structure is invalid ValueError {e}')

    elif db == os.getenv('DATA_DIR'):
        pass
    # then push data according to template
    # --- question.db
    #   --- only 1 table = 1 template


    # --- survey.db
    #   --- user_table + Function_table combined (pushed once and remember User_table PK (Id))
    #   --- check if entry already present (ask user if already registered --> yes and "go back" options"
    #       --- if yes load that PK!
    #   --- Annotation_table
    pass

def tbl_row_delete():
    # if question was asked 2 for same function delete question in original!
    pass

def check_entry(cur: sqlite3.Cursor, data: List[tuple], table: str | None, statements: dict) -> List[tuple]:
    """
    Checking data entry into DB. Assures no duplication entries into connected database.

    Args:
        cur (sqlite3.Cursor): Sqlite DB connection cursor.
        data (List[tuple]): Entry data set to be tested.
        table (str | None]: Table to connect to defaults to 'questions' - table if nothing specified.
        statements (dict): Dictionary of possible SQLite statements from INSERT to SELECT.

    Returns:
        new data set without the entries already present in the current database/table.

    """
    # fetch all from table if None go for table == 'questions'
    exe_cmd = statements['SELECT_ALL'].format(table=table or 'questions')
    c_table = cur.execute(exe_cmd).fetchall()

    # for row in data check if in table
    rows_delete = [idx for idx, row in enumerate(data) if row in c_table]
    new_data = [row for idx, row in enumerate(data) if idx not in rows_delete]
    # add to log indices with rows of not added entries which are already in tables

    return new_data


def get_insert_columns(cur: sqlite3.Cursor, table: str) -> List[str]:
    """
    Return the list of columns that should be provided for INSERT,
    skipping an autoincrement primary key named Id or question_id.
    """
    cur.execute(f"PRAGMA table_info({table})")
    cols = []
    for cid, name, col_type, notnull, dflt_value, pk in cur.fetchall():
        # If Id is the primary key and auto increment, we do not insert it
        if pk == 1 and (name.lower() == 'Id' or name.lower() == 'question_id'):
            continue
        cols.append(name)
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
    errors = []

    for idx, row in enumerate(rows):
        if len(row) != expected:
            errors.append(f"Row {idx} has {len(row)} values, expected {expected}")

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