# Fintech SQL Business Queries

**Topic:** digital wallet app. **Tables (Excel files):** `customers.xlsx`, `accounts.xlsx`, `support_tickets.xlsx`, linked by `customer_id`.

All queries are `SELECT` only (information retrieval) and were run in Python on SQLite.

## Q1. How many customers do we have in each city?

```sql
SELECT city, COUNT(*) AS total_customers
FROM customers
GROUP BY city
ORDER BY total_customers DESC;
```

**Result:**

| city      |   total_customers |
|:----------|------------------:|
| Karachi   |               342 |
| Lahore    |               310 |
| Islamabad |               204 |
| Peshawar  |                88 |
| Quetta    |                56 |

## Q2. What is the average balance and average monthly logins for each account type?

```sql
SELECT account_type,
       COUNT(*)                        AS customers,
       ROUND(AVG(avg_balance), 0)      AS average_balance,
       ROUND(AVG(monthly_logins), 1)   AS average_logins
FROM accounts
GROUP BY account_type
ORDER BY average_balance DESC;
```

**Result:**

| account_type   |   customers |   average_balance |   average_logins |
|:---------------|------------:|------------------:|-----------------:|
| Premium        |         194 |            302315 |             29.5 |
| Standard       |         343 |             79683 |             19.7 |
| Basic          |         463 |             15135 |              5.8 |

## Q3. Who are the top 5 customers with the highest balance, and which city are they in?

```sql
SELECT c.customer_id, c.city, a.account_type, a.avg_balance
FROM customers AS c
JOIN accounts AS a ON c.customer_id = a.customer_id
ORDER BY a.avg_balance DESC
LIMIT 5;
```

**Result:**

|   customer_id | city      | account_type   |   avg_balance |
|--------------:|:----------|:---------------|--------------:|
|           222 | Quetta    | Premium        |        465398 |
|           233 | Karachi   | Premium        |        462508 |
|           531 | Karachi   | Premium        |        461079 |
|           371 | Islamabad | Premium        |        430773 |
|           174 | Lahore    | Premium        |        426022 |

## Q4. Which support ticket category is raised most often?

```sql
SELECT category, COUNT(*) AS total_tickets
FROM support_tickets
GROUP BY category
ORDER BY total_tickets DESC;
```

**Result:**

| category        |   total_tickets |
|:----------------|----------------:|
| Refund          |             243 |
| Fee Dispute     |             242 |
| Login Problem   |             232 |
| Failed Transfer |             225 |
| Card Issue      |             223 |

## Q5. Which ticket category takes the longest to resolve on average?

```sql
SELECT category, ROUND(AVG(resolution_hours), 1) AS avg_resolution_hours
FROM support_tickets
GROUP BY category
ORDER BY avg_resolution_hours DESC;
```

**Result:**

| category        |   avg_resolution_hours |
|:----------------|-----------------------:|
| Failed Transfer |                   29.4 |
| Login Problem   |                   25.7 |
| Refund          |                   24.5 |
| Fee Dispute     |                   23.8 |
| Card Issue      |                   22.1 |

## Q6. How many customers have never raised a support ticket?

```sql
SELECT COUNT(*) AS customers_with_no_tickets
FROM customers AS c
LEFT JOIN support_tickets AS t ON c.customer_id = t.customer_id
WHERE t.ticket_id IS NULL;
```

**Result:**

|   customers_with_no_tickets |
|----------------------------:|
|                         395 |

## Q7. What is the churn rate (share of customers who left) for each account type?

```sql
SELECT account_type,
       COUNT(*)                                  AS customers,
       SUM(churned)                              AS churned_customers,
       ROUND(100.0 * SUM(churned) / COUNT(*), 1) AS churn_rate_percent
FROM accounts
GROUP BY account_type
ORDER BY churn_rate_percent DESC;
```

**Result:**

| account_type   |   customers |   churned_customers |   churn_rate_percent |
|:---------------|------------:|--------------------:|---------------------:|
| Basic          |         463 |                 285 |                 61.6 |
| Standard       |         343 |                  72 |                 21   |
| Premium        |         194 |                   5 |                  2.6 |

## Q8. Which city has the happiest customers (highest average ticket satisfaction)?

```sql
SELECT c.city, ROUND(AVG(t.satisfaction), 2) AS avg_satisfaction, COUNT(*) AS tickets
FROM customers AS c
JOIN support_tickets AS t ON c.customer_id = t.customer_id
GROUP BY c.city
ORDER BY avg_satisfaction DESC;
```

**Result:**

| city      |   avg_satisfaction |   tickets |
|:----------|-------------------:|----------:|
| Peshawar  |               3.44 |       113 |
| Lahore    |               3.33 |       404 |
| Karachi   |               3.3  |       368 |
| Quetta    |               3.27 |        71 |
| Islamabad |               3.18 |       209 |

## Q9. Which customers are at risk: 3 or more tickets and fewer than 10 logins a month?

```sql
SELECT c.customer_id, c.city, a.monthly_logins, COUNT(t.ticket_id) AS tickets
FROM customers AS c
JOIN accounts AS a ON c.customer_id = a.customer_id
JOIN support_tickets AS t ON c.customer_id = t.customer_id
WHERE a.monthly_logins < 10
GROUP BY c.customer_id, c.city, a.monthly_logins
HAVING COUNT(t.ticket_id) >= 3
ORDER BY tickets DESC, a.monthly_logins ASC
LIMIT 10;
```

**Result:**

|   customer_id | city      |   monthly_logins |   tickets |
|--------------:|:----------|-----------------:|----------:|
|           836 | Lahore    |                2 |         4 |
|           105 | Islamabad |                3 |         4 |
|           127 | Karachi   |                3 |         4 |
|           151 | Peshawar  |                3 |         4 |
|           359 | Lahore    |                3 |         4 |
|           407 | Karachi   |                3 |         4 |
|           547 | Islamabad |                3 |         4 |
|           591 | Lahore    |                3 |         4 |
|           774 | Lahore    |                3 |         4 |
|           282 | Lahore    |                4 |         4 |

## Q10. How much total money is held in wallets in each city?

```sql
SELECT c.city, ROUND(SUM(a.avg_balance), 0) AS total_balance
FROM customers AS c
JOIN accounts AS a ON c.customer_id = a.customer_id
GROUP BY c.city
ORDER BY total_balance DESC;
```

**Result:**

| city      |   total_balance |
|:----------|----------------:|
| Karachi   |     3.184e+07   |
| Lahore    |     3.11179e+07 |
| Islamabad |     1.74062e+07 |
| Peshawar  |     7.55472e+06 |
| Quetta    |     5.06904e+06 |
