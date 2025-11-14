
INSERT INTO si_sample (
    starting_depot_id,
    ending_depot_id,
    transport_id,
    desired_value
)
VALUES (
    :starting_depot_id,
    :ending_depot_id,
    :transport_id,
    :desired_value
)
ON CONFLICT(
    starting_depot_id,
    ending_depot_id,
    transport_id
) DO UPDATE

SET
    desired_value = excluded.desired_value;
