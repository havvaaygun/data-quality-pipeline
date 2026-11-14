-- =====================================================================
-- Data Quality Monitoring (PostgreSQL)
-- =====================================================================
-- Load the RAW file as text so format problems survive, then profile it.
-- =====================================================================

DROP TABLE IF EXISTS customers_raw;
CREATE TABLE customers_raw (
    customer_id  TEXT,
    full_name    TEXT,
    email        TEXT,
    city         TEXT,
    signup_date  TEXT,
    total_spend  TEXT,
    age          TEXT
);
-- \copy customers_raw FROM 'data/customers_raw.csv' CSV HEADER;


-- ---------- 1. Missing values per column ----------------------------
SELECT 'email'       AS column, COUNT(*) FILTER (WHERE email IS NULL OR email = '')       AS nulls FROM customers_raw
UNION ALL SELECT 'city',        COUNT(*) FILTER (WHERE city IS NULL OR city = '')          FROM customers_raw
UNION ALL SELECT 'signup_date', COUNT(*) FILTER (WHERE signup_date IS NULL OR signup_date='') FROM customers_raw
UNION ALL SELECT 'total_spend', COUNT(*) FILTER (WHERE total_spend IS NULL OR total_spend='') FROM customers_raw
ORDER BY nulls DESC;


-- ---------- 2. Duplicate rows ---------------------------------------
SELECT COUNT(*) - COUNT(*) FILTER (WHERE rn = 1) AS duplicate_rows
FROM (
    SELECT ROW_NUMBER() OVER (
        PARTITION BY customer_id, full_name, email, city, signup_date, total_spend, age
        ORDER BY customer_id) AS rn
    FROM customers_raw
) t;


-- ---------- 3. Invalid emails ---------------------------------------
SELECT COUNT(*) AS invalid_emails
FROM customers_raw
WHERE email IS NOT NULL AND email <> ''
  AND email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$';


-- ---------- 4. Impossible ages --------------------------------------
SELECT COUNT(*) AS bad_ages
FROM customers_raw
WHERE age ~ '^-?\d+$'
  AND (age::INT < 18 OR age::INT > 100);


-- ---------- 5. Inconsistent formats ---------------------------------
SELECT
    COUNT(*) FILTER (WHERE signup_date !~ '^\d{4}-\d{2}-\d{2}$'
                     AND signup_date IS NOT NULL AND signup_date <> '') AS non_iso_dates,
    COUNT(*) FILTER (WHERE total_spend ~ ',' OR upper(total_spend) ~ 'TL') AS non_numeric_spend
FROM customers_raw;


-- ---------- 6. Standardised city values -----------------------------
SELECT initcap(btrim(city)) AS city_clean, COUNT(*) AS n
FROM customers_raw
WHERE city IS NOT NULL AND city <> ''
GROUP BY initcap(btrim(city))
ORDER BY n DESC;
