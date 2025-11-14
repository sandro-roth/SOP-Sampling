import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

def __load_env(cwd) -> str | None:
    """
    Load environment variables from a suitable .env file.

    The function searches for a .env file in several prioritized locations:
    1. A path explicitly defined in the environment variable `SOP_UI_DOTENV_PATH`.
    2. A `.env` file located three directories above the current working file
       (used when running directly from an IDE or development environment).
    3. A `.env` file found automatically in the current working directory.

    Once found, the .env file is loaded using `python-dotenv`.

    Args:
        cwd (Path) : current working directory where the _load_env is called from

    Returns:
        str | None: The path to the loaded .env file, or None if no .env file was found.
    """
    explicit = os.getenv('SOP_DOTENV_PATH')
    if explicit and Path(explicit).exists():
        load_dotenv(explicit)
        return explicit

    candidate = cwd.parents[3] / '.env' if len(cwd.parents) >= 4 else None
    if candidate and candidate.exists():
        load_dotenv(candidate)
        return str(candidate)

    found = find_dotenv(usecwd=True)
    if found:
        load_dotenv(found)
        return found

    return None