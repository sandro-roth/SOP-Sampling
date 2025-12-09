import os
import requests

from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
from pathlib import Path

from utils import setup_logging, get_logger, __load_env, load_yaml, db_push, preview_db

# Setup
cwd = Path(__file__).resolve()
loaded_from = __load_env(cwd=cwd)
statements = load_yaml()
db_path = os.getenv('DATA_DIR')
UI_HOST = os.getenv('SOP_UI_HOST', 'ui')  # Service name from docker compose
UI_PORT = os.getenv('SOP_UI_PORT', '8000')

# Example function choices for the dropdown
FUNCTION_CHOICES = [
    "Arzt / Ärztin",
    "Pflegekraft",
    "Student",
    "Other"
]

def create_app() -> Flask:
    """
    Create and configure the Flask application.

    This function initializes a Flask app instance, sets up basic configuration,
    and defines routes for adding parameter Values to Database

    Routes:
        GET /                       –
        POST /submit_annotation     –

    Returns:
        Flask: The configured Flask application instance.
    """

    app = Flask(__name__,
                template_folder=str(cwd.parent / 'templates'),
                static_folder=str(cwd.parent / 'static'))
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    flask_log = get_logger(__name__)


    @app.route('/', methods=['GET', 'POST'])
    def user_mask():
        flask_log.info('Mask init ...')
        errors: list[str] = []
        success_message = ""

        # Set empty values to keep user input on validation errors
        form_data = {'first_name': '',
                     'last_name': '',
                     'function': '',
                     'years_in_function': ''}

        if request.method == 'POST':
            # Read values
            form_data['first_name'] = request.form.get('first_name', '').strip()
            form_data['last_name'] = request.form.get('last_name', '').strip()
            form_data['function'] = request.form.get('function', '').strip()
            raw_years = request.form.get('years_in_function', '').strip()

            # Validate
            if not form_data['first_name']:
                errors.append('First name is required.')
            if not form_data['last_name']:
                errors.append('Last name is required.')
            if not form_data['function']:
                errors.append('Function is required.')

            if not raw_years:
                errors.append('Years in function is required')
            else:
                try:
                    years_int = int(raw_years)
                    if years_int < 0:
                        errors.append('Years in function must be zero or positive')
                except ValueError:
                    errors.append('Years in function must be an integer')
                else:
                    form_data['years_in_function'] = str(years_int)

            if not errors:
                flask_log.info(f'Received user mask data: {form_data}')

                pk_func = db_push(data=[form_data['function']], db=db_path, table='function', statements=statements, user_add=True)
                usr_data = [(form_data['first_name'], form_data['last_name'], pk_func, int(form_data['years_in_function']))]
                pk_usr = db_push(data=usr_data, db=db_path, table='user', statements=statements, user_add=True)

                # redirect intern auf Proxy Route /annotate
                return redirect(url_for(
                    'annotate',
                    user_pk=pk_usr,
                    func_pk=pk_func
                ))

        return render_template(
            'user_mask.html',
            functions=FUNCTION_CHOICES,
            errors=errors,
            success_message=success_message,
            form_data=form_data,
        )

    @app.route('/annotate', methods=['GET'])
    def annotate():
        user_pk = request.args.get("user_pk")
        func_pk = request.args.get("func_pk")

        ui_url = f"http://{UI_HOST}:{UI_PORT}/"

        params = {}
        if user_pk and func_pk:
            params = {"user_pk": user_pk, "func_pk": func_pk}

        try:
            ui_resp = requests.get(
                ui_url,
                params=params or None,
                cookies=request.cookies,
                timeout=5,
            )
        except requests.RequestException as e:
            flask_log.error("Error contacting UI service: %s", e)
            return "UI service unavailable", 502

        excluded_headers = {
            "content-encoding", "content-length",
            "transfer-encoding", "connection"
        }
        headers = [
            (name, value)
            for name, value in ui_resp.headers.items()
            if name.lower() not in excluded_headers
        ]
        return Response(ui_resp.content, ui_resp.status_code, headers)

    @app.route('/submit_annotation', methods=['POST'])
    def proxy_submit_annotation():
        ui_url = f"http://{UI_HOST}:{UI_PORT}/submit_annotation"

        try:
            ui_resp = requests.post(
                ui_url,
                data=request.form,
                cookies=request.cookies,
                timeout=5,
                allow_redirects=False,
            )
        except requests.RequestException as e:
            flask_log.error("Error contacting UI service (submit): %s", e)
            return "UI service unavailable", 502

        # sop_ui answers with redirect to '/'
        if ui_resp.status_code in (301, 302, 303, 307, 308):
            location = ui_resp.headers.get("Location", "/")
            if location == "/":
                # home in sop_ui, here it is /annotate
                return redirect(url_for("annotate"))
            else:
                # other redirects get passed
                return redirect(location)

        excluded_headers = {
            "content-encoding", "content-length",
            "transfer-encoding", "connection"
        }
        headers = [
            (name, value)
            for name, value in ui_resp.headers.items()
            if name.lower() not in excluded_headers
        ]
        return Response(ui_resp.content, ui_resp.status_code, headers)

    @app.route("/api/db-preview", methods=["GET"])
    def db_preview():
        """Preview all DB tables as echtes JSON für pandas."""
        flask_log.info("DB preview requested")

        import sqlite3
        import pandas as pd

        db_file = db_path
        limit = request.args.get("limit", default=100, type=int)

        if not db_file:
            flask_log.error("DATA_DIR is not set")
            return jsonify({"error": "DATA_DIR is not set"}), 500

        con = sqlite3.connect(db_file)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]

        result: dict[str, list[dict]] = {}

        for t in tables:
            if limit is None:
                df = pd.read_sql(f"SELECT * FROM {t}", con)
            else:
                df = pd.read_sql(f"SELECT * FROM {t} LIMIT {limit}", con)
            # jede Zeile als dict, perfekt für pandas auf Clientseite
            result[t] = df.to_dict(orient="records")

        con.close()
        return jsonify(result)

    return app


def main() -> None:
    """

    """

    setup_logging(app_name='User_Mask', log_dir=os.getenv('UUI_LOG_DIR'))
    log = get_logger(__name__)

    app = create_app()
    port = int(os.getenv("SOP_UUI_PORT", "8100"))
    log.info(f".env loaded from: {loaded_from}")
    log.info(f"SOP_UUI_PORT = {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()