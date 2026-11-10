-- 1) Create the database
CREATE DATABASE IF NOT EXISTS fintech_db;
USE fintech_db;

-- 2) Create the 3 tables
CREATE TABLE customers (
    customer_id    INT PRIMARY KEY,
    age            INT,
    gender         VARCHAR(10),
    city           VARCHAR(30),
    monthly_income FLOAT
);

CREATE TABLE accounts (
    account_id           INT PRIMARY KEY,
    customer_id          INT,
    account_type         VARCHAR(20),
    avg_balance          FLOAT,
    monthly_transactions INT,
    monthly_logins       INT,
    churned              INT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE support_tickets (
    ticket_id        INT PRIMARY KEY,
    customer_id      INT,
    category         VARCHAR(30),
    resolution_hours FLOAT,
    satisfaction     FLOAT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
