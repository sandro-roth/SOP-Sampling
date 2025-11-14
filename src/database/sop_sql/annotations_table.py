# This is the Schema to create the function_table
CREATE_ANNOTATION_TABLE = """
CREATE TABLE IF NOT EXISTS annotations (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,

    question TEXT NOT NULL,
    question_id INTEGER,

    alt_question TEXT,

    passage TEXT NOT NULL,
    answer TEXT NOT NULL,

    alt_answer TEXT,

    question_accepted INTEGER DEFAULT 0 CHECK (question_accepted IN (0, 1)),

    fluent INTEGER DEFAULT 1 CHECK (fluent BETWEEN 1 AND 5),
    comprehensive INTEGER DEFAULT 1 CHECK (comprehensive BETWEEN 1 AND 5),
    factual INTEGER DEFAULT 1 CHECK (factual BETWEEN 1 AND 5),

    annotator INTEGER NOT NULL,
    FOREIGN KEY (annotator) REFERENCES user(Id)
);
"""