import os
from pathlib import Path

from utils import setup_logging, get_logger, __load_env, db_conn, preview_db
from .function_table import CREATE_FUNCTION_TABLE
from .user_table import CREATE_USER_TABLE
from .annotations_table import CREATE_ANNOTATION_TABLE
from .question_bank import CREATE_QUESTIONS_TABLE

def main():
    cwd = Path(__file__).resolve()
    loaded_from = __load_env(cwd=cwd)

    setup_logging(app_name='database', log_dir=os.getenv('DB_LOG_DIR'), to_stdout=False)
    db_log = get_logger(__name__)
    db_log.info(f".env loaded from: {loaded_from}")
    db_log.info('---- Database script running ----')

    db_path = os.getenv('DATA_DIR')
    qdb_path = os.getenv('DATA_DIR_QUESTIONS')

    with db_conn(db_path) as (con, cur):
        cur.execute(CREATE_FUNCTION_TABLE)
        cur.execute(CREATE_USER_TABLE)
        cur.execute(CREATE_ANNOTATION_TABLE)

    with db_conn(qdb_path) as (con, cur):
        cur.execute(CREATE_QUESTIONS_TABLE)

    preview_db(db_path)
    preview_db(qdb_path)


# Interact class (loading a table then write methods to pull, push/add, delete)


if __name__ == '__main__':
    main()