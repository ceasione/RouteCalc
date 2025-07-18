
SELECT
    calculation_place_a_name,
    calculation_place_a_name_long,
    calculation_place_b_name,
    calculation_place_b_name_long,
    calculation_map_link,
    calculation_place_chain,
    calculation_chain_map_link,
    calculation_distance,
    calculation_transport_id,
    calculation_transport_name,
    calculation_transport_capacity,
    calculation_price,
    calculation_price_per_ton,
    calculation_price_per_km,
    calculation_is_price_per_ton,
    calculation_currency,
    calculation_currency_rate,
    calculation_pfactor_vehicle,
    calculation_pfactor_departure,
    calculation_pfactor_arrival,
    calculation_pfactor_distance,
    calculation_locale,
    calculation_real_price,
    calculation_starting_depot_id,
    calculation_ending_depot_id
FROM calculation
WHERE calculation_id = :lookup_id;
