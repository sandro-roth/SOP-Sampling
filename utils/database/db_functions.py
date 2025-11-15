from contextlib import contextmanager
import sqlite3
import pandas as pd

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
    pass

def db_push():
    pass

def preview_db(db: str, limit=5):
    """
        Preview the contents of all tables in a SQLite database.

        This function connects to the given SQLite file, lists all tables,
        and prints the first few rows of each table using pandas for easy viewing.

        Args:
            db (str):
                Path to the SQLite `.db` file.
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

    print("Found tables:", tables)
    print()

    for t in tables:
        print(f"Table: {t}")
        df = pd.read_sql(f"SELECT * FROM {t} LIMIT {limit}", con)
        print(df)
        print("-" * 40)

    con.close()