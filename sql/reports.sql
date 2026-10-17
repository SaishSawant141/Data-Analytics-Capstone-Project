-- Query 1: Order totals
-- | total_orders | total_revenue | avg_order_value |
-- | ------------ | ------------- | --------------- |
-- | 180          | 99860.2       | 554.78          |

SELECT COUNT(*) AS total_orders,
ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue,
ROUND(AVG(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS avg_order_value
FROM orders o JOIN products p ON o.product_id = p.product_id;

-- Query 2: Order totals 
-- | total_orders | rating_count | difference |
-- | ------------ | ------------ | ---------- |
-- | 180          | 165          | 15         |

SELECT COUNT(*) AS total_orders, COUNT(rating) as rating_count, COUNT(*) - COUNT(rating) AS difference FROM orders;

-- Query 3: LEFT JOIN with a genuine zero-match row
-- | customer_id | name   |
-- | ----------- | ------ |
-- | C045        | Vihaan |

-- LEFT JOIN Query
SELECT c.customer_id, c.name 
FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id 
GROUP BY c.customer_id, c.name HAVING COUNT(o.order_id) = 0;

-- Independent Query
SELECT customer_id, name FROM customers WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);

-- Query 4: GROUP BY + HAVING
-- | city      | total_orders | returned_orders | return_rate_pct |
-- | --------- | ------------ | --------------- | --------------- |
-- | Jaipur    | 19           | 8               | 42.1            |
-- | Lucknow   | 49           | 15              | 30.6            |
-- | Bangalore | 33           | 8               | 24.2            |

SELECT c.city as city, COUNT(o.order_id) as total_orders, SUM(o.returned) as returned_orders,
ROUND((SUM(o.returned)/COUNT(o.order_id)*100.0),1) as return_rate_pct
FROM orders o JOIN customers c on o.customer_id = c.customer_id
GROUP BY c.city HAVING return_rate_pct > 20 ORDER BY return_rate_pct DESC;


-- Query 5: Ranking with ORDER BY + LIMIT/OFFSET

-- Query with LIMIT 5
-- | customer_id | name    | total_spend |
-- | ----------- | ------- | ----------- |
-- | C043        | Reyansh | 12920       |
-- | C026        | Isha    | 8371.6      |
-- | C008        | Meera   | 4564.6      |
-- | C011        | Arjun   | 4111        |
-- | C042        | Sanya   | 3785        |

-- Tie-break(order by c.customer_id ASC) ensures distinct ranking when customers have equal total_spend.
SELECT c.customer_id, c.name,
ROUND((SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100))), 2) AS total_spend
FROM orders o JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name ORDER BY total_spend DESC, c.customer_id ASC LIMIT 5;

-- Query with LIMIT 3 OFFSET 2
-- | customer_id | name  | total_spend |
-- | ----------- | ----- | ----------- |
-- | C008        | Meera | 4564.6      |
-- | C011        | Arjun | 4111        |
-- | C042        | Sanya | 3785        |

SELECT c.customer_id, c.name,
ROUND((SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100))), 2) AS total_spend
FROM orders o JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name ORDER BY total_spend DESC, c.customer_id ASC LIMIT 3 OFFSET 2;

-- Query 6: Three-table JOIN with GROUP BY
-- | category     | order_count | category_revenue |
-- | ------------ | ----------- | ---------------- |
-- | Haircare     | 54          | 44956.1          |
-- | Skincare     | 60          | 27346            |
-- | Babycare     | 30          | 16805            |
-- | PersonalCare | 36          | 10753.1          |

SELECT p.category AS category, COUNT(o.order_id) AS order_count, 
ROUND((SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100))), 2) AS category_revenue
FROM orders o JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY p.category ORDER BY category_revenue DESC;

-- Query 7: LIKE pattern match
-- | customer_names |
-- | -------------- |
-- | Aarav          |
-- | Aditi          |
-- | Ananya         |
-- | Arjun          |
-- | Aryan          |
-- | Anika          |
-- | Aditya         |
-- | Aisha          |
-- | Ayaan          |
-- | Aria           |

SELECT name AS customer_names FROM customers WHERE name LIKE "A%";

-- Query 8: DISTINCT
-- | acquisition_source |
-- | ------------------ |
-- | Organic            |
-- | Referral           |
-- | Ad                 |
-- | Social             |

SELECT DISTINCT(acquisition_source) FROM customers;

-- Query 9: ALTER TABLE + UPDATE with CASE
-- | loyalty_tier | COUNT(\*) |
-- | ------------ | --------- |
-- | Gold         | 28        |
-- | Silver       | 17        |

ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers SET loyalty_tier = CASE WHEN city_tier = 1 THEN 'Gold' ELSE 'Silver' END;

SELECT loyalty_tier, COUNT(*) FROM customers GROUP BY loyalty_tier;