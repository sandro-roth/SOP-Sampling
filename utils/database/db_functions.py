from contextlib import contextmanager
import sqlite3

@contextmanager
def db_conn(db: str):
    """
    Open a SQLite database connection and return both
    the connection and a cursor object.

    Args:
        db (str): Path to the SQLite database file.
    """
    con = sqlite3.connect(db)
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