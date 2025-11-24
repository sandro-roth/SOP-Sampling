import os

from flask import Flask, render_template, request
from pathlib import Path

from utils import setup_logging, get_logger, __load_env



# Setup
cwd = Path(__file__).resolve()
loaded_from = __load_env(cwd=cwd)

# Example function choices for the dropdown
FUNCTION_CHOICES = [
    "Physician",
    "Nurse",
    "Researcher",
    "Student",
    "Technician",
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
                success_message = "User data saved successfully."
                # Reset it to empty values
                form_data = {'first_name': '',
                             'last_name': '',
                             'function': '',
                             'years_in_function': ''}


        return render_template(
            'user_mask.html',
            functions=FUNCTION_CHOICES,
            errors=errors,
            success_message=success_message,
            form_data=form_data,
        )
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
