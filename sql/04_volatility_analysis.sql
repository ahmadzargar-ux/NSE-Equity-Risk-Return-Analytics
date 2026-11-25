SELECT
	s.ticker,
	s.latest_date,
	p.annualized_volatility_pct
FROM (
SELECT ticker, max(trade_date) AS latest_date
FROM stock_prices
GROUP BY ticker
) s

JOIN stock_prices p
ON s.ticker = p.ticker
AND s.latest_date = p.trade_date

ORDER BY annualized_volatility_pct DESC
LIMIT 10;