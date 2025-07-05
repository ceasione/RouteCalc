CREATE TABLE IF NOT EXISTS calculation (
    -- Primary Key
    calculation_id CHAR(40) PRIMARY KEY,  -- SHA-1-like hex digest (40 chars)

    -- RequestDTO fields
    request_intent TEXT NOT NULL,
    request_orig_lat REAL,
    request_orig_lng REAL,
    request_orig_name TEXT,
    request_orig_name_long TEXT,
    request_orig_countrycode CHAR(2),
    request_dest_lat REAL,
    request_dest_lng REAL,
    request_dest_name TEXT,
    request_dest_name_long TEXT,
    request_dest_countrycode CHAR(2),
    request_vehicle INTEGER NOT NULL,
    request_phone_num TEXT,
    request_locale CHAR(5),
    request_url TEXT,
    request_ip TEXT,

    -- CalculationDTO fields
    calculation_place_a_name TEXT,
    calculation_place_a_name_long TEXT,
    calculation_place_b_name TEXT,
    calculation_place_b_name_long TEXT,
    calculation_map_link TEXT,
    calculation_place_chain TEXT,
    calculation_chain_map_link TEXT,
    calculation_distance REAL NOT NULL,
    calculation_transport_id INTEGER NOT NULL,
    calculation_transport_name TEXT,
    calculation_transport_capacity TEXT,
    calculation_price REAL NOT NULL,
    calculation_price_per_ton REAL NOT NULL,
    calculation_price_per_km REAL NOT NULL,
    calculation_is_price_per_ton BOOLEAN,
    calculation_currency CHAR(3),
    calculation_currency_rate REAL,
    calculation_pfactor_vehicle TEXT,
    calculation_pfactor_departure TEXT,
    calculation_pfactor_arrival TEXT,
    calculation_pfactor_distance TEXT,
    calculation_locale CHAR(5)
);

-- Redundant with PRIMARY KEY, but added for visual clarity
-- CREATE INDEX IF NOT EXISTS idx_calculation_id ON calculation (calculation_id);
