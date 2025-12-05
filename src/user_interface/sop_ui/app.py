import os
import json

from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session

from utils import setup_logging, get_logger, __load_env, sampling, db_push, load_yaml

# Setup
cwd = Path(__file__).resolve()
loaded_from = __load_env(cwd=cwd)
log_loc = get_logger(__name__)
statements = load_yaml()
q_bank_path = Path(os.getenv('DATA_DIR_QUESTIONS')).resolve()
q_bank = None
db_path = os.getenv('DATA_DIR')


def load_q_bank():
    global q_bank
    if q_bank is None:
        with open(q_bank_path, 'r', encoding='utf-8') as file:
            q_bank = json.load(file)
    return q_bank

def get_next_example_from_db(usr_pk: int, fun_pk: int) -> tuple[int, str, str, str]:
    """
    This function retrieves next question (make sure every question only 2 annotators use predefined function)

    Returns:
         (question_id, question_text, answer_text, passage_text)
    """

    jason_file = load_q_bank()
    question = sampling(statements=statements, j_file=jason_file, usr_id=usr_pk, fun_id=fun_pk)
    log_loc.info(f"{question['q_id']}, {question['question']}, {question['answer']}")

    with open(q_bank_path, 'w', encoding='utf-8') as file:
        json.dump(jason_file, file, ensure_ascii=False, indent=2)

    return question['q_id'], question['question'], question['answer'], question['context']

def get_example_by_id(q_id: int) -> tuple[int, str, str, str]:
    """

    :param q_id:
    :return:
    """

    data = load_q_bank()
    if not isinstance(data, list):
        raise RuntimeError('Question bank must be a list of objects')

    for q in data:
        if q.get('q_id') == q_id:
            return q["q_id"], q["question"], q["answer"], q["context"]
    raise RuntimeError(f"No question found with q_id={q_id}")


def save_annotation_to_db(qstn: str, q_id: int,  alt_q: str | None, passg: str, ansr: str, alt_a: str | None,
                          flu: int, comp: int, fact: int, ann_id: int, q_acc: bool = True) -> None:
    """
    Takes Userinterface inputs which describe the answer to the question like how fluent, comprehensive and factual
    the answer is. It is called from the Flask app posting to the /submit_annotation.

    Args:
        qstn (str): Question text in the Question Bank going to be rated.
        q_id (int): Foreign-key of questions in the Question Bank.
        alt_q (str | None): Question text provided by the annotator if they reject the original question.
        passg (str): Passage text in the Question Bank.
        ansr (str): Passage answer in the Question Bank.
        alt_a (str | None): Answer text provided by the annotator if they reject the original answer.
        flu (int): Fluent parameter, describes how fluent the question is with ratings (1-5).
        comp (int): Comprehensive parameter, describes how comprehensive the question is with ratings (1-5).
        fact (int): Factual parameter, describes how factual the questions is with ratings (1-5).
        ann_id (int): Annotator Foreign-key of User table (current user).
        q_acc (bool): Question accepted boolean default True.

    """
    a_data = [(qstn, q_id, alt_q, passg, ansr, alt_a, q_acc, flu, comp, fact, ann_id)]
    db_push(data=a_data, db=db_path, table='annotations', statements=statements)

def create_app() -> Flask:
    """
    Create and configure the Flask application.

    This function initializes a Flask app instance, sets up basic configuration,
    and defines routes for adding parameter Values to Database

    Routes:
        GET /                       – Render the main page showing calling a question from the DB.
        POST /submit_annotation     – Add the values of fluency, comprehensiveness and factual to the DB.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, template_folder=str(cwd.parent / 'templates'))
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
    flask_log = get_logger(__name__)

    @app.get('/')
    def home():
        user_pk = session.get("user_pk")
        func_pk = session.get("func_pk")

        # If not in session yet, this is probably the first request after redirect
        if user_pk is None or func_pk is None:
            user_pk = request.args.get("user_pk", type=int)
            func_pk = request.args.get("func_pk", type=int)

            if user_pk is None or func_pk is None:
                flask_log.error("Missing user_pk or func_pk in query parameters and session")
                return "Missing user id or function id", 400

            # Store in session for all future requests
            session["user_pk"] = user_pk
            session["func_pk"] = func_pk

        flask_log.info("New question loaded for user_pk=%s func_pk=%s", user_pk, func_pk)
        try:
            question_id, question_text, answer_text, passage_text = get_next_example_from_db(usr_pk=user_pk, fun_pk=func_pk)
        except RuntimeError as e:
            flask_log.info("No more questions for this user/function: %s", e)
            return render_template('index.html', no_questions=True)

        return render_template('index.html', no_question=False,
                               question_id=question_id, question_text=question_text.strip(),
                               answer_text=answer_text.strip(), passage_text=passage_text.strip())

    @app.post('/submit_annotation')
    def submit_annotation():
        # Read values from UI
        user_pk = session.get("user_pk")
        question_id = int(request.form['question_id'])
        fluency = int(request.form['fluency'])
        comprehensive = int(request.form['comprehensiveness'])
        factual = int(request.form['factuality'])

        # Optional alternatives from hidden fields
        alt_quest = request.form.get('alternative_question', '').strip() or None
        alt_ans = request.form.get('alternative_answer', '').strip() or None

        # Load original example from JSON via id
        try:
            q_id_db, question_text, answer_text, passage_text = get_example_by_id(question_id)
        except RuntimeError as e:
            flask_log.error("Could not load question %s from JSON: %s", question_id, e)
            return "Question not found", 400

        # Store in DB
        flask_log.info(f'\nQuestion_id: {question_id}\nFluency: {fluency}\nComprehensiveness: {comprehensive}\nFactual: {factual}')
        flask_log.info(f'Alternative Question: {alt_quest}')
        flask_log.info(f'Alternative Answer: {alt_ans}')

        save_annotation_to_db(qstn=question_text, q_id=question_id, alt_q=alt_quest, passg=passage_text, ansr=answer_text,
                              alt_a=alt_ans, flu=fluency, comp=comprehensive, fact=factual, ann_id=user_pk, q_acc=True)

        # Load next question
        return redirect(url_for('home'))
    return app

def main() -> None:
    """
    Entry point for running the Flask application.

    This function creates the Flask app instance, reads the desired port
    from the environment variable `SOP_UI_PORT` (defaulting to 8000),
    and starts the development server.

    It also prints information about the loaded .env file and the chosen port
    for easier debugging and transparency during startup.

    Returns:
        None
    """
    setup_logging(app_name='user_interface', log_dir=os.getenv('GUI_LOG_DIR'))
    log = get_logger(__name__)

    app = create_app()
    port = int(os.getenv("SOP_UI_PORT", "8000"))
    log.info(f".env loaded from: {loaded_from}")
    log.info(f"SOP_UI_PORT = {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()