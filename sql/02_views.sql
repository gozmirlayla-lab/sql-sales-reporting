-- Ne pas sommer invoices.total_cents après une jointure vers invoice_lines.
CREATE VIEW v_sales AS
SELECT l.line_id, i.invoice_id, i.customer_id, i.invoice_date,
       i.billing_country, t.track_id, g.name AS genre,
       l.quantity, l.unit_price_cents * l.quantity AS revenue_cents
FROM invoice_lines l
JOIN invoices i ON i.invoice_id = l.invoice_id
JOIN tracks t ON t.track_id = l.track_id
LEFT JOIN genres g ON g.genre_id = t.genre_id;

CREATE VIEW v_monthly AS
SELECT substr(invoice_date,1,7) AS month,
       COUNT(*) AS orders, COUNT(DISTINCT customer_id) AS active_customers,
       SUM(total_cents) AS revenue_cents,
       1.0 * SUM(total_cents) / COUNT(*) AS average_order_cents
FROM invoices GROUP BY substr(invoice_date,1,7);

CREATE VIEW v_customer_value AS
SELECT c.customer_id, c.country, COUNT(i.invoice_id) AS orders,
       COALESCE(SUM(i.total_cents),0) AS revenue_cents,
       MAX(i.invoice_date) AS last_order
FROM customers c LEFT JOIN invoices i ON i.customer_id=c.customer_id
GROUP BY c.customer_id, c.country;
