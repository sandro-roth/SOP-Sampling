import sqlite3

def db_conn(db: str) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    """
    Open a SQLite database connection and return both
    the connection and a cursor object.

    Args:
        db (str): Path to the SQLite database file.

    Returns:
        tuple[Connection, Cursor]: (connection, cursor)
    """
    con = sqlite3.connect(db)
    cur = con.cursor()
    return con, cur

def db_pull():
    pass

def db_push():
    pass