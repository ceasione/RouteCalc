
-- si_sample is a self-indexed sample storage table
-- Data you insert is a part of PRIMARY KEY
-- Like a Set in Python except hashing is absent

CREATE TABLE IF NOT EXISTS si_sample (
    starting_depot_id INTEGER NOT NULL,
    ending_depot_id INTEGER NOT NULL,
    transport_id INTEGER NOT NULL,
    desired_value REAL NOT NULL,
    PRIMARY KEY (starting_depot_id, ending_depot_id, transport_id)
);
