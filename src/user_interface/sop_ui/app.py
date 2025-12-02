import os
import json

from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for

from utils import setup_logging, get_logger, __load_env, sampling, db_push, load_yaml

# Setup
cwd = Path(__file__).resolve()
loaded_from = __load_env(cwd=cwd)
log_loc = get_logger(__name__)
statements = load_yaml()
q_bank_path = Path(os.getenv('DATA_DIR_QUESTIONS')).resolve()

def get_next_example_from_db(usr_pk: int, fun_pk: int) -> tuple[int, str, str, str]:
    """
    This function retrieves next question (make sure every question only 2 annotators use predefined function)

    Returns:
         (question_id, question_text, answer_text, passage_text)
    """

    with open(q_bank_path, 'r', encoding='utf-8') as file:
        jason_file = json.load(file)

    question = sampling(statements=statements, j_file=jason_file, usr_id=usr_pk, fun_id=fun_pk)
    log_loc.info(f'{question['q_id']}, {question['question']}, {question['answer']}')

    with open(q_bank_path, 'w', encoding='utf-8') as file:
        json.dump(jason_file, file, ensure_ascii=False, indent=2)

    question_id = question['q_id']
    question_text = question['question']
    answer_text = question['answer']
    passage_text = question['context']

    return question_id, question_text, answer_text, passage_text

def save_annotation_to_db(question_id: int, flu: int, comp: int, fact: int,
                          rej_q: bool, alt_q: str | None, rej_a: bool, alt_a: str | None) -> None:
    """
    Takes Userinterface inputs which describe the answer to the question like how fluent, comprehensive and factual
    the answer is. It is called from the Flask app posting to the /submit_annotation.

    Args:
        question_id (int): Unique ID to keep track of the answered and unanswered questions.
        flu (int): Fluent parameter, describes how fluent the question is with ratings (1-5).
        comp (int): Comprehensive parameter, describes how comprehensive the question is with ratings (1-5).
        fact (int): Factual parameter, describes how factual the questions is with ratings (1-5).
        rej_q (bool): Rejected question, set to True if the question is rejected.
        alt_q (str | None): Alternative question, user input of a question example if original question is rejected.
        rej_a (bool): Rejected answer, set to True if the answer is rejected.
        alt_a (str | None): Alternative answer, user input of an answer example if original answer is rejected.
    """
    pass

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
    flask_log = get_logger(__name__)

    @app.get('/')
    def home():
        # Load one question
        flask_log.info('New Question loaded')

        try:
            question_id, question_text, answer_text, passage_text = get_next_example_from_db(usr_pk=1, fun_pk=2)
        except RuntimeError as e:
            flask_log.info("No more questions for this user/function: %s", e)
            return render_template('index.html', no_questions=True)

        return render_template('index.html', no_question=False,
                               question_id=question_id, question_text=question_text.strip(),
                               answer_text=answer_text.strip(), passage_text=passage_text.strip())

    @app.post('/submit_annotation')
    def submit_annotation():
        # Read values fro UI
        question_id = int(request.form['question_id'])
        fluency = int(request.form['fluency'])
        comprehensive = int(request.form['comprehensiveness'])
        factual = int(request.form['factuality'])

        # Optional alternatives from hidden fields
        alternative_question = request.form.get('alternative_question', '').strip() or None
        alternative_answer = request.form.get('alternative_answer', '').strip() or None

        # Flags: rejected, if alternative is given
        rejected_q = alternative_question is not None
        rejected_a = alternative_answer is not None

        # Store in DB
        flask_log.info(f'\nQuestion_id: {question_id}\nFluency: {fluency}\nComprehensiveness: {comprehensive}\nFactual: {factual}')
        flask_log.info(f'Alternative Question: {alternative_question}')
        flask_log.info(f'Alternative Answer: {alternative_answer}')
        save_annotation_to_db(question_id=question_id, flu=fluency,
                              comp=comprehensive, fact=factual,
                              rej_q=rejected_q, alt_q=alternative_question,
                              rej_a=rejected_a, alt_a=alternative_answer)

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