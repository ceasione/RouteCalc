
SELECT
    request_intent,
    request_orig_lat,
    request_orig_lng,
    request_orig_name,
    request_orig_name_long,
    request_orig_countrycode,
    request_dest_lat,
    request_dest_lng,
    request_dest_name,
    request_dest_name_long,
    request_dest_countrycode,
    request_vehicle,
    request_phone_num,
    request_locale,
    request_url,
    request_ip
FROM calculation
WHERE calculation_id = :lookup_id;
