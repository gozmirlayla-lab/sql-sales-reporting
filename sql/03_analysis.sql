-- name: monthly_growth
-- Question 1 : comment évolue le CA mensuel ? Premier mois sans taux.
WITH history AS (
 SELECT *, LAG(revenue_cents) OVER (ORDER BY month) AS previous_cents
 FROM v_monthly
)
SELECT *, ROUND(100.0*(revenue_cents-previous_cents)/NULLIF(previous_cents,0),2)
 AS growth_percent FROM history ORDER BY month;

-- name: countries
-- Question 2 : quels pays de facturation contribuent au CA ?
SELECT billing_country, COUNT(*) AS orders,
 COUNT(DISTINCT customer_id) AS buyers, SUM(total_cents) AS revenue_cents,
 ROUND(100.0*SUM(total_cents)/(SELECT SUM(total_cents) FROM invoices),2) AS share_percent
FROM invoices GROUP BY billing_country ORDER BY revenue_cents DESC, billing_country;

-- name: genres
-- Question 3 : quelles catégories contribuent au CA et aux volumes ?
SELECT genre, SUM(quantity) AS units, SUM(revenue_cents) AS revenue_cents,
 DENSE_RANK() OVER (ORDER BY SUM(revenue_cents) DESC) AS revenue_rank
FROM v_sales GROUP BY genre ORDER BY revenue_rank, genre;

-- name: customers_above_average
-- Question 4 : quels clients dépassent le CA moyen par client ?
SELECT customer_id, country, orders, revenue_cents,
 DENSE_RANK() OVER (ORDER BY revenue_cents DESC) AS value_rank
FROM v_customer_value
WHERE revenue_cents > (SELECT AVG(revenue_cents) FROM v_customer_value)
ORDER BY value_rank, customer_id;

-- name: repeat_purchase
-- Question 5 : quelle part des acheteurs a plusieurs factures sur la période ?
SELECT COUNT(*) AS buyers,
 SUM(CASE WHEN orders>=2 THEN 1 ELSE 0 END) AS repeat_buyers,
 ROUND(100.0*SUM(CASE WHEN orders>=2 THEN 1 ELSE 0 END)/COUNT(*),2) AS repeat_percent
FROM v_customer_value WHERE orders>0;

-- name: reconciliation
-- Contrôle financier indépendant : totaux facture versus détail.
SELECT i.invoice_id, i.total_cents,
 COALESCE(SUM(l.unit_price_cents*l.quantity),0) AS detail_cents
FROM invoices i LEFT JOIN invoice_lines l ON l.invoice_id=i.invoice_id
GROUP BY i.invoice_id,i.total_cents
HAVING i.total_cents <> COALESCE(SUM(l.unit_price_cents*l.quantity),0);
