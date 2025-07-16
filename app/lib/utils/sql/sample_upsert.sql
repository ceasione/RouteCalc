
INSERT INTO sample (calculation_id, desired_value)
VALUES (
    :calculation_id,
    :desired_value
)
ON CONFLICT(calculation_id) DO UPDATE SET
    desired_value = excluded.desired_value;
