import os
import csv
from pathlib import Path
from io import StringIO

from flask import Flask, render_template, request

from utils import setup_logging, get_logger, __load_env

# Setup
cwd = Path(__file__).resolve()
loaded_from = __load_env(cwd=cwd)

def allowed_file(filename: str) -> bool:
    """

    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"csv", "txt"}

def parse_file(file) -> list[tuple]:
    """
    Parse the uploaded file into a list of tuples.

    CSV or TXT:
        - treat both the same
        - each line = one row
        - comma-separated columns
        - empty lines are ignored

    Return:
        List of tuples ready to insert into database
    """

    filename = file.filename or ''
    extension = filename.rsplit('.', 1)[-1].lower()

    if extension not in ['.csv', '.txt' ]:
        raise ValueError('Only .csv and .txt files are supported.')

    content = file.read().decode('utf-8', errors='replace')
    file.seek(0)
    return parse(content)

def parse(text: str) -> list[tuple]:
    """
    Parse manual text input.

    Behavior:
        - each non empty line = one row
        - comma split columns
        - whitespace around columns is stripped

    Args:
        text (str): Manual data entry into questions db.
    """
    rows: list[tuple] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        columns = (part.strip() for part in stripped.split(','))
        rows.append(tuple(columns))

    return rows


def create_app() -> Flask:
    """
    Create and configure the Flask application

    This function initializes a Flask app instance, sets up basic configuration,
    and defines routes for adding parameter Values to Database

    Routes:
        GET /                       – Show upload form
        POST /                      – handle file upload, show preview, push to database placeholder

    Returns:
        ...
    """

    app = Flask(__name__, template_folder=str(cwd.parent / 'templates'), static_folder=str(cwd.parent / 'static'))
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    flask_log = get_logger(__name__)

    @app.routes('/', methods=['GET', 'POST'])
    def upload_data():
        errors: list[str] = []
        preview_rows: list[tuple] = []
        file_name = ''
        manual_text = ''

        if request.method == 'POST':
            uploaded_file = request.files.get('data_file')
            manual_text = request.form.get('manual_text', '').strip()

            # Decide source of data: file has priority, otherwise manual text
            has_file = uploaded_file and uploaded_file.filename != ''
            has_manual = bool(manual_text)

            if not has_file and not has_manual:
                errors.append('Please upload a file or enter text manually')

            if has_file and not allowed_file(uploaded_file.filenam):
                errors.append('Only .csv and .txt files are allowed')

            if not errors:
                try:
                    rows: list[tuple] = []
                    if has_file:
                        file_name = uploaded_file.filename
                        rows = parse_file(uploaded_file)
                        flask_log.info(f'Parsed file {file_name} into {len(rows)} rows.')

                    if has_manual:
                        rows = parse(manual_text)
                        flask_log.info(f'Parsed manual input into {len(rows)} rows.')

                    if not rows:
                        errors.append('No data found to process')

                    else:
                        preview_rows = rows[:10]

                except Exception as e:
                    errors.append(f'Error while processing data: {e}')

        preview_text = repr(preview_rows) if preview_rows else ""
        total_rows = len(preview_rows)

        return render_template('upload_data.html',
                               errors=errors,
                               preview_text=preview_text,
                               preview_rows=preview_rows,
                               file_name=file_name,
                               manual_text=manual_text,
                               total_rows=total_rows)
    return app

def main() -> None:
    """

    """

    setup_logging(app_name='Q_Push_UI', log_dir=os.getenv('Q_PUSH_LOG_DIR'))
    main_log = get_logger(__name__)

    app = create_app()
    port = int(os.getenv('SOP_QP_PORT', '8300'))
    main_log.info(f".env loaded from: {loaded_from}")
    main_log.info(f"SOP_QUI_PORT = {port}")
    app.run(host="0.0.0.0", port=port, debug=False)