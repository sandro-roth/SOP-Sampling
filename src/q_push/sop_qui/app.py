import os
import csv
from pathlib import Path
from io import StringIO

from flask import Flask, render_template, request, session

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
    Parse text content (from file or manual input) into a list of tuples

    Behavior:
        - treat content as CSV
        - each row is one CSV record
        - commas separate columns
        - commas inside fields are allowed if the field is quoted
        - whitespace around columns is stripped
        - empty rows are ignored

    Args:
        text (str): Manual data entry into questions db.
    """
    rows: list[tuple] = []
    reader = csv.reader(StringIO(text))
    for row in reader:
        # skip empty rows
        if not row or all(not cell.strip() for cell in row):
            continue

        cleaned = tuple(cell.strip() for cell in row)
        rows.append(cleaned)

    return rows

def reset_all():
    """Reset form data and preview session."""
    session.pop("pending_rows", None)
    session.pop("has_preview", None)
    return "", "", []


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
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret')
    flask_log = get_logger(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def upload_data():
        errors: list[str] = []
        preview_rows: list[tuple] = []
        file_name = ''
        manual_text = ''
        action = request.form.get("action")

        if request.method == 'POST':
            uploaded_file = request.files.get('data_file')
            manual_text = request.form.get('manual_text', '').strip()

            # Decide source of data: file has priority, otherwise manual text
            has_file = uploaded_file and uploaded_file.filename != ''
            has_manual = bool(manual_text)

            if action == 'clear':
                reset_all()

            elif action == 'preview':
                if not has_file and not has_manual:
                    errors.append('Please upload a file or enter text manually')

                if has_file and not allowed_file(uploaded_file.filenam):
                    errors.append('Only .csv and .txt files are allowed')

                if not errors:
                    rows: list[tuple] = []
                    try:
                        if has_file:
                            file_name = uploaded_file.filename
                            rows = parse_file(uploaded_file)
                            flask_log.info(f'Parsed file {file_name} into {len(rows)} rows.')

                        elif has_manual:
                            rows = parse(manual_text)
                            flask_log.info(f'Parsed manual input into {len(rows)} rows.')

                        if not rows:
                            errors.append('No data found to process')

                        else:
                            session['pending_rows'] = [list(r) for r in rows]
                            session["has_preview"] = True
                            preview_rows = rows[:10]

                    except Exception as e:
                        errors.append(f'Error while processing data: {e}')

            elif action == 'submit':
                rows: list[tuple] = []

                # Use preview data if available
                if session.get('has_preview') and 'pending_rows' in session:
                    stored = session.get('pending_rows', [])
                    rows = [tuple(r) for r in stored]
                    flask_log.info(
                        f'Submitting {len(rows)} rows from previous preview to database'
                    )
                else:
                    if not has_file and not has_manual:
                        errors.append('Please upload a file or enter text manually')

                    if has_file and not allowed_file(uploaded_file.filenam):
                        errors.append('Only .csv and .txt files are allowed')

                    if not errors:
                        try:
                            if has_file:
                                file_name = uploaded_file.filename
                                rows = parse_file(uploaded_file)
                                flask_log.info(
                                    f"Parsed file '{file_name}' into {len(rows)} rows"
                                )
                            else:
                                rows = parse(manual_text)
                                flask_log.info(
                                    f'Parsed manual input into {len(rows)} rows'
                                )
                        except Exception as e:
                            errors.append(f'Error while processing data: {e}')

                if not errors:
                    if not rows:
                        errors.append("No data found to submit")
                    else:
                        # push everything to database
                        print(rows)

                        # clear session preview data and form
                        reset_all()

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