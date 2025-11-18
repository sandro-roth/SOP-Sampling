import os
from pathlib import Path

from utils import setup_logging, get_logger, __load_env, db_conn, preview_db, db_push, load_yaml
from .function_table import CREATE_FUNCTION_TABLE
from .user_table import CREATE_USER_TABLE
from .annotations_table import CREATE_ANNOTATION_TABLE
from .question_bank import CREATE_QUESTIONS_TABLE, CREATE_BACKUP

def main():
    cwd = Path(__file__).resolve()
    loaded_from = __load_env(cwd=cwd)
    statements = load_yaml()

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
        cur.execute(CREATE_BACKUP)


# ---------------------------------------- All of Pushing, Pulling, Deleting -------------------------------------------
# ------------------------------ which is tested here will be moved to src/main ----------------------------------------
    # CHECK PUSHING TO QUESTION.DB
    question_data = [
        ('is it possible', 'yes it is', 'the passage this is from'),
        ('does it look different', 'no it does not', 'no passage'),
        ('is this the third time?', 'maybe it is ', 'passage one'),
        ('....?', '....!', '....')
    ]
    db_push(data=question_data, db=qdb_path, table='questions', statements=statements)


    # CHECK PUSHING TO SURVEY.DB / USER AND FUNCTION TABLE
    f_data = ['AI Specialist']
    pk_function = db_push(data=f_data, db=db_path, table='function', statements=statements, user_add=True)
    print(f'The primary_key for the function {f_data}:\n'
          f'{pk_function}')

    u_data = [('Sandro', 'Roth', pk_function, 1)]
    pk_user = db_push(data=u_data, db=db_path, table='user', statements=statements, user_add=True)
    print(f'The primary_key for the user {u_data}:\n'
          f'{pk_user}')

    # CHECK PUSHING TO SURVEY.DB / ANNOTATIONS TABLE
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

    preview_db(db_path)
    preview_db(qdb_path)

if __name__ == '__main__':
    main()