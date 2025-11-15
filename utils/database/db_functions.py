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