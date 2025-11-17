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
    pass

def db_push(data, db: str, table) -> None:
    # Connect to db (check with db it is)
    if db == os.getenv('DATA_DIR_QUESTIONS'):
        with db_conn(db) as (con, cur):
            validate_rows_for_table_db(cur, table=table, rows=data)
            # check if potential entry already in backup table (print and log!)
            # else add question to original and backup db (with template)
            pass
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

def db_row_delete():
    # if question was asked 2 for same function delete question in original!
    pass

def check_entry():
    # check if data entry already in db
    pass

def get_insert_columns(cur: sqlite3.Cursor, table: str) -> List[str]:
    """
    Return the list of columns that should be provided for INSERT,
    skipping an autoincrement primary key named Id.
    """
    cur.execute(f"PRAGMA table_info({table})")
    cols = []
    for cid, name, col_type, notnull, dflt_value, pk in cur.fetchall():
        # If Id is the primary key and auto increment, we do not insert
        # it
        if pk == 1 and name.lower() == "id":
            continue
        cols.append(name)
    return cols

def validate_rows_for_table_db(cur: sqlite3.Cursor, table: str, rows: Sequence[Sequence]) -> bool:
    """
    Validate rows by checking length against columns from the database.
    Returns True if validation passes.
    """
    columns = get_insert_columns(cur, table)
    expected = len(columns)
    errors = []

    for idx, row in enumerate(rows):
        if len(row) != expected:
            errors.append(f"Row {idx} has {len(row)} values, expected {expected}")

    if errors:
        raise ValueError("Invalid rows for table {table}: " + " | ".join(errors))

    else:
        return True


def preview_db(db: str, pre_dir:str | None = None, limit: int = 5) -> None:
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