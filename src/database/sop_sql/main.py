import os
from pathlib import Path

from utils import setup_logging, get_logger, __load_env, db_conn
from .function_table import CREATE_FUNCTION_TABLE

def main():
    cwd = Path(__file__).resolve()
    loaded_from = __load_env(cwd=cwd)
    setup_logging(app_name='database', log_dir=os.getenv('DB_LOG_DIR'), to_stdout=False)
    db_log = get_logger(__name__)
    db_log.info(f".env loaded from: {loaded_from}")
    db_log.info('---- Database script running ----')

    with db_conn(os.getenv('DATA_DIR')) as (con, cur):
        cur.execute(CREATE_FUNCTION_TABLE)
    # if no tables create them


# Interact class (loading a table then write methods to pull, push/add, delete)


if __name__ == '__main__':
    main()