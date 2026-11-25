SELECT
	ticker,
	latest_date,
	annualized_volatility_pct
FROM (
SELECT ticker, max(trade_date) AS latest_date
FROM stock_prices
GROUP BY ticker
) s

JOIN stock_prices p
ON s.ticker = p.ticker
AND s.latest_date = p.latest_date

ORDER BY annualized_volatility_pct DESC
LIMIT 10;