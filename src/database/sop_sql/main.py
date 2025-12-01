import os
import json
from pathlib import Path

from utils import setup_logging, get_logger, __load_env, db_conn, preview_db, sampling, load_yaml, db_push
from .function_table import CREATE_FUNCTION_TABLE
from .user_table import CREATE_USER_TABLE
from .annotations_table import CREATE_ANNOTATION_TABLE

def main():
    cwd = Path(__file__).resolve()
    loaded_from = __load_env(cwd=cwd)
    statements = load_yaml()

    setup_logging(app_name='database', log_dir=os.getenv('DB_LOG_DIR'), to_stdout=False)
    db_log = get_logger(__name__)
    db_log.info(f".env loaded from: {loaded_from}")
    db_log.info('---- Database script running ----')

    db_path = os.getenv('DATA_DIR')

    with db_conn(db_path) as (con, cur):
        cur.execute(CREATE_FUNCTION_TABLE)
        cur.execute(CREATE_USER_TABLE)
        cur.execute(CREATE_ANNOTATION_TABLE)


# ---------------------------------------- All of Pushing, Pulling, Deleting -------------------------------------------
# ------------------------------ which is tested here will be moved to src/main ----------------------------------------

    # CHECK PUSHING TO SURVEY.DB / USER AND FUNCTION TABLE --> can only add one entry at once
    f_data, f1_data, f2_data = ['AI Specialist'], ['Wissenschaftlicher Mitarbeiter'], ['Test Engineer']
    pk_function_1 = db_push(data=f_data, db=db_path, table='function', statements=statements, user_add=True)
    pk_function_2 = db_push(data=f1_data, db=db_path, table='function', statements=statements, user_add=True)
    pk_function_3 = db_push(data=f2_data, db=db_path, table='function', statements=statements, user_add=True)


    u_data, u1_data, u2_data = [('Daniel', 'Roth', pk_function_1, 1)], [('Mars', 'Nestle', pk_function_2, 1)], [('Snickers', 'Ovo', pk_function_3, 1)]
    u3_data, u4_data, u5_data = [('Daniel', 'Roth', pk_function_2, 1)], [('Mars', 'Nestle', pk_function_3, 1)], [('Snickers', 'Ovo', pk_function_1, 1)]
    pk_user_1 = db_push(data=u_data, db=db_path, table='user', statements=statements, user_add=True)
    pk_user_2 = db_push(data=u1_data, db=db_path, table='user', statements=statements, user_add=True)
    pk_user_4 = db_push(data=u3_data, db=db_path, table='user', statements=statements, user_add=True)


    # CHECK PUSHING TO SURVEY.DB / ANNOTATIONS TABLE --> can only add one entry at once
    a_data = [('the question?', 1, 'NaN', 'passage', 'the answer', 'alternative answer', 1, 2, 3, 4, pk_user_1)]
    db_push(data=a_data, db=db_path, table='annotations', statements=statements)
    a_data = [('the question?', 2, 'NaN', 'passage', 'the answer', 'alternative answer', 1, 2, 3, 4, pk_user_1)]
    db_push(data=a_data, db=db_path, table='annotations', statements=statements)
    a_data = [('the question?', 3, 'NaN', 'passage', 'the answer', 'alternative answer', 1, 3, 3, 4, pk_user_2)]
    db_push(data=a_data, db=db_path, table='annotations', statements=statements)
    a_data = [('the question?', 4, 'NaN', 'passage', 'the answer', 'alternative answer', 1, 2, 3, 4, pk_user_2)]
    db_push(data=a_data, db=db_path, table='annotations', statements=statements)
    a_data = [('the question?', 4, 'NaN', 'passage', 'the answer', 'alternative answer', 1, 2, 3, 4, pk_user_4)]
    db_push(data=a_data, db=db_path, table='annotations', statements=statements)


    # CHECK SAMPLING FUNCTION
    q_bank_path = Path(os.getenv('DATA_DIR_QUESTIONS')).resolve()
    with open(q_bank_path, 'r', encoding='utf-8') as file:
        jason_file = json.load(file)

    question = sampling(statements=statements, j_file=jason_file, usr_id=pk_user_1, fun_id=pk_function_2)
    print(question['q_id'], question['question'], question['answer'])

    # Update question JSON file
    with open(q_bank_path, 'w', encoding='utf-8') as file:
        json.dump(jason_file, file, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

    preview_db(db_path)

if __name__ == '__main__':
    main()