USE movr;

CREATE VIEW customer_summary_view AS
SELECT
    sum(rides.revenue),
    users.name,
    rides.end_time
FROM users
JOIN rides ON users.id = rides.rider_id
GROUP BY users.name, rides.end_time;
