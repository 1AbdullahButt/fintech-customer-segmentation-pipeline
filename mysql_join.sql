-- 3) JOIN the 3 tables into one master dataset
SELECT
    c.customer_id, c.age, c.gender, c.city, c.monthly_income,
    a.account_type, a.avg_balance, a.monthly_transactions,
    a.monthly_logins, t.ticket_count, t.avg_resolution_hours,
    t.avg_satisfaction, a.churned
FROM customers AS c
JOIN accounts AS a
    ON c.customer_id = a.customer_id
LEFT JOIN (
    SELECT customer_id,
           COUNT(*)              AS ticket_count,
           AVG(resolution_hours) AS avg_resolution_hours,
           AVG(satisfaction)     AS avg_satisfaction
    FROM support_tickets
    GROUP BY customer_id
) AS t
    ON c.customer_id = t.customer_id;
