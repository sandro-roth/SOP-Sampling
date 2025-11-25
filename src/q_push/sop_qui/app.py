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

