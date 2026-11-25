Select 
	s.ticker,
	latest_date,
	p.cumulative_return_pct

From (
	Select ticker, max(trade_date) as latest_date
From stock_prices
Group By ticker	
) s

JOIN stock_prices p
	ON s.ticker = p.ticker
	AND s.latest_date = p.trade_date
ORDER BY cumulative_return_pct
LIMIT 10;

	