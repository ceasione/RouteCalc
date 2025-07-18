
SELECT sample.desired_value,
       calculation.calculation_real_price,
       calculation.calculation_starting_depot_id,
       calculation.calculation_ending_depot_id,
       calculation.calculation_transport_id
FROM sample
JOIN calculation USING(calculation_id);
