# This is the Schema to create the question_table
CREATE_QUESTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    passage TEXT NOT NULL
);
"""
CREATE_BACKUP = """
CREATE TABLE IF NOT EXISTS backup (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    passage TEXT NOT NULL
);
"""