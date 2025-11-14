# This is the Schema to create the function_table
CREATE_FUNCTION_TABLE = """
CREATE TABLE IF NOT EXISTS function (
    Id SERIAL PRIMARY KEY,
    function VARCHAR(20), NOT NULL
);
"""