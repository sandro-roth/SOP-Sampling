# This is the Schema to create the function_table
CREATE_USER_TABLE = """
CREATE TABLE IF NOT EXISTS user (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    First_name TEXT NOT NULL,
    Surname TEXT NOT NULL,
    function INTEGER NOT NULL,
    years_in_the_function INTEGER,
    FOREIGN KEY (function) REFERENCES function(Id)
);
"""