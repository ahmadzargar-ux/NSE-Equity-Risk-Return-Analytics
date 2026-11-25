SELECT 
	ticker,
	DATE_TRUNC('month',trade_date) AS month,
	(EXP(SUM(LN(1 + daily_return_pct / 100)))-1) *100 AS compounded_monthly_return_pct

FROM stock_prices

GROUP BY 
	ticker, 
	DATE_TRUNC('month',trade_date)

ORDER BY
	ticker, 
	month;