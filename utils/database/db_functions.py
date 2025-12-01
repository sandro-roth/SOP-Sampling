import os
import random

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


def db_pull(statements: dict) -> List[tuple] | None:
    dub_thr = int(os.getenv('DUP_THRESHOLD'))
    with db_conn(os.getenv('DATA_DIR_QUESTIONS')) as (con, cur):
        try:
            pk_list = cur.execute(statements['SELECT_LENGTH']).fetchall()
            q_rand_id = random.choice(pk_list)[0]
        except IndexError as e:
            print(f'All questions have been answered: {e}')
            return None

        # FOR NOW SHOULD BE UPDATED!! ---------------------------------------
        # if q_rand_id / function in joined tables more than $TWICE
        # --> Drop this question from questions table and recurse to db_pull
        # FOR NOW SHOULD BE UPDATED!! ---------------------------------------

        with db_conn(os.getenv('DATA_DIR')) as (con2, cur2):
            anno_answer = cur2.execute(statements['SELECT_JOIN'], [q_rand_id]).fetchall()
            counts = {}
            duplicate = []
            for item in anno_answer:
                counts[item] = counts.get(item, 0) + 1

                if counts[item] > dub_thr:
                    duplicate.append(item)

        if duplicate:
            tbl_row_delete(con=con, cur=cur, statements=statements, row=duplicate[0][0])
            # call db_pull again for another question!

        else:
            rdm_entry = cur.execute(statements['SELECT_QUESTION'],[q_rand_id]).fetchone()
            # questions table entry: (question_id, question, answer, passage)
            # (6, 'is it still windy?', 'only a little', 'weather report')
            return rdm_entry

def sampling(statements: dict, j_file: List[dict]) -> dict:
    #print(j_file[0].keys())
    question = random.choice(j_file)
    q_rand_id = question['q_id']
    with db_conn(os.getenv('DATA_DIR')) as (con, cur):
        anno_a = cur.execute(statements['SELECT_JOIN'], [q_rand_id]).fetchall()
        # If question not in annotation table:
        if len(anno_a) == 0:
            print(type(question))
            print(question)
            return question
        # If question is annotated once
        elif len(anno_a) == 1:
            # If same function but different User annotate!
            pass
            # Else call sampling function again to get another question

        elif len(anno_a) == 2:
            # drop question from JSON file
            # call sampling function again to get another question
            pass

        else:
            raise ValueError('Something went wrong. Questions can not annotated more than twice.')





def db_push(data: List[tuple] | List[str], db: str, table: str, statements:dict, user_add: bool = False) -> int | None:
    """
    Docstring!

    Args:
        data (List[tuple]):     ...
        db (str):               ...
        table (str):            ...
        statements (dict):      ...
        user_add (bool):        ...

    Returns:
        Goal of calling the function is altering specific tables there is no return value.

    """

    placeholders = ','.join('?' for _ in range(len(data[0])))
    if db == os.getenv('DATA_DIR_QUESTIONS'):
        with db_conn(db) as (con, cur):
            try:
                name_list = validate_rows_for_table_db(cur, table=table, rows=data)
                c_names = ','.join(name_list)
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
            if user_add and table == 'function':
                try:
                    # check if function in Function table:
                    names = ','.join(get_insert_columns(cur=cur, table=table))
                    if check_entry(cur=cur, data=data, statements=statements, col_names=names, table=table):
                        exec_cmd = statements['INSERT_IN_FUNCTION']
                        cur.execute(exec_cmd, data)
                        con.commit()
                    else:
                        print('function already present')
                    exec_cmd = statements['SELECT_PK_FUNCTION'].format(function=data[0])
                    pk_function = cur.execute(exec_cmd).fetchone()[0]
                    return pk_function
                except ValueError as e:
                    print(f'Function could not be added FormatError: {e}')

            if user_add and table == 'user':
                try:
                    # check if user already in User table:
                    names = ','.join(get_insert_columns(cur=cur, table=table))
                    if check_entry(cur=cur, data=data, statements=statements, col_names=names, table=table):
                        exec_cmd = statements['INSERT_IN_USER']
                        cur.execute(exec_cmd, data[0])
                        con.commit()
                    else:
                        print('user already present')

                    exec_cmd = statements['SELECT_PK_USER']
                    pk_user = cur.execute(exec_cmd, data[0]).fetchone()[0]
                    return pk_user
                except ValueError as e:
                    print(f'User could not be added FormatError: {e}')

            elif not user_add and table == 'annotations':
                try:
                    # check if annotation already in annotations table
                    names = ','.join(get_insert_columns(cur=cur, table=table))
                    if not check_entry(cur=cur, data=data, statements=statements, col_names=names, table=table):
                        raise RuntimeError('Logic error: entry check failed!')

                    # Insert into annotation table
                    exec_cmd = statements['INSERT_IN_ANNOTATION']
                    cur.execute(exec_cmd, data[0])
                except ValueError as e:
                    print(f'Annotation could not be added FormatError: {e}')
                except RuntimeError as e:
                    print(f"Annotation could not be added RuntimeError: {e}")


def tbl_row_delete(con:sqlite3.Connection, cur: sqlite3.Cursor, statements:dict, row:int) -> None:
    cur.execute(statements['DELETE_ROW'], [row])
    con.commit()


def check_entry(cur: sqlite3.Cursor, data: List[tuple] | List[str], statements: dict,  col_names: str, table: str | None = None) -> List[tuple] | None:
    """
    Checking data entry into DB. Assures no duplication entries into connected database.

    Args:
        cur (sqlite3.Cursor): Sqlite DB connection cursor.
        data (List[tuple]): Entry data set to be tested.
        statements (dict): Dictionary of possible SQLite statements from INSERT to SELECT.
        col_names (str): string of comma separated colum names of table.
        table (str | None): Table to connect to defaults to 'questions' - table if nothing specified.

    Returns:
        new data set without the entries already present in the current database/table.

    """

    # fetch all from table if None go for table == 'questions'
    exe_cmd = statements['SELECT_ALL'].format(column_names=col_names, table=table or 'backup')
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