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
        preview: list[tuple] = []
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
                pass
        