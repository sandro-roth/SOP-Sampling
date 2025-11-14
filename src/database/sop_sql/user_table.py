# This is the Schema to create the function_table
CREATE_USER_TABLE = """
CREATE TABLE IF NOT EXISTS function (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    function_name TEXT NOT NULL
);
"""