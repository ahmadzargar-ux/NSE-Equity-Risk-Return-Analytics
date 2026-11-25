SELECT 
	ticker,
	DATE_TRUNC('month',trade_date) AS month,
	avg(daily_return_pct) AS average_daily_return

FROM stock_prices
GROUP BY ticker,DATE_TRUNC('month',trade_date)
ORDER BY ticker,DATE_TRUNC('month',trade_date);