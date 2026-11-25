-- Create the stock_prices table for the NSE Equity Risk & Return Analytics project.
-- Run this script only when setting up a NEW, empty nse_analytics database.
-- The table already exists in your current database, so do not rerun this there.

CREATE TABLE stock_prices (
    trade_date DATE NOT NULL,
    adj_close DOUBLE PRECISION NOT NULL,
    close_price DOUBLE PRECISION NOT NULL,
    high_price DOUBLE PRECISION NOT NULL,
    low_price DOUBLE PRECISION NOT NULL,
    open_price DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    ticker VARCHAR(30) NOT NULL,
    daily_return_pct DOUBLE PRECISION,
    abs_daily_return_pct DOUBLE PRECISION,
    cumulative_return_pct DOUBLE PRECISION NOT NULL,
    annualized_volatility_pct DOUBLE PRECISION,
    PRIMARY KEY (ticker, trade_date)
);
