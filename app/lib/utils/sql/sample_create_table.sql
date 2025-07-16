
CREATE TABLE IF NOT EXISTS sample (
    sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_id CHAR(40) NOT NULL UNIQUE,
    desired_value REAL NOT NULL,
    FOREIGN KEY (calculation_id) REFERENCES calculation(calculation_id)
);
