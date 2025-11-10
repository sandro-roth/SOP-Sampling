import os
from flask import Flask, render_template, request
app = Flask(__name__)

items = []

@app.get('/')
def index():
    return "UI is up and running"


def main():
    port = int(os.getenv("SOP_UI_PORT", "8000"))
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()