import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from flask import Flask, render_template, request
from markupsafe import escape


def _laod_env():
    '''
    loading .env var depending on how the script is called
    :return: str, path to .env file
    '''

    # Called from terminal with "export SOP_UI_DOTENV_PATH=..." defined for venv
    explicit = os.getenv('SOP_UI_DOTENV_PATH')
    if explicit and Path(explicit).exists():
        load_dotenv(explicit)
        return explicit

    # Run without sop-ui package from your IDE
    cwd = Path(__file__).resolve()
    candidate = cwd.parents[3] / '.env' if len(cwd.parents) >= 4 else None
    if candidate and candidate.exists():
        load_dotenv(candidate)
        return str(candidate)

    # Fallback to a .env in the cwd
    found = find_dotenv(usecwd=True)
    if found:
        load_dotenv(found)
        return found

    return None

loaded_from = _laod_env()

def create_app():
    app = Flask(__name__)
    items = []

    @app.get('/')
    def home():
        return render_template('index.html', items=items)

    @app.post('/add')
    def add():
        text = request.form.get("text", "").strip()
        if text:
            items.append(escape(text))
        return render_template("_list.html", items=items)

    return app

def main():
    app = create_app()
    port = int(os.getenv("SOP_UI_PORT", "8000"))
    print(f"Loaded SOP_UI_PORT={port} from {ENV_PATH}")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()