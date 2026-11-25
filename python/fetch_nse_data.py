
import time
import logging

import pandas as pd
import yfinance as yf


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

TICKERS = [
    # Banking and financial services
    "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "BAJFINANCE.NS",
    "BAJAJFINSV.NS",

    # Information technology
    "TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS",

    # Energy
    "RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS",

    # Consumer goods
    "ITC.NS", "HINDUNILVR.NS", "TITAN.NS", "ASIANPAINT.NS",

    # Automobiles
    "MARUTI.NS", "M&M.NS", "EICHERMOT.NS",

    # Pharmaceuticals
    "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS",

    # Infrastructure and metals
    "LT.NS", "ULTRACEMCO.NS", "ADANIPORTS.NS",
    "TATASTEEL.NS", "JSWSTEEL.NS",
]

PERIOD = "5y"
OUTPUT_FILE = "nse_historical_data.csv"
MAX_ATTEMPTS = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)


# --------------------------------------------------
# 2. DOWNLOAD DATA
# --------------------------------------------------

def download_stock_data(ticker, period=PERIOD):
    """Download and standardize historical data for one stock."""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logging.info(
                "Downloading %s (attempt %s/%s)",
                ticker, attempt, MAX_ATTEMPTS
            )

            data = yf.download(
                ticker,
                period=period,
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False,
            )

            if data.empty:
                raise ValueError("Download returned no rows.")

            # Flatten MultiIndex columns returned by yfinance.
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            data = data.reset_index()

            data.columns = [
                str(column).strip().replace(" ", "_")
                for column in data.columns
            ]

            data["Ticker"] = ticker

            validate_stock_data(data, ticker)

            logging.info(
                "%s: downloaded %s rows",
                ticker, len(data)
            )

            return data

        except Exception as error:
            logging.warning(
                "%s failed on attempt %s: %s",
                ticker, attempt, error
            )

            if attempt < MAX_ATTEMPTS:
                time.sleep(2 * attempt)

    raise RuntimeError(
        f"Failed to download valid data for {ticker} "
        f"after {MAX_ATTEMPTS} attempts."
    )


# --------------------------------------------------
# 3. VALIDATE DATA
# --------------------------------------------------

def validate_stock_data(data, ticker):
    """Raise an error when essential data-quality checks fail."""

    required = [
        "Date", "Open", "High", "Low",
        "Close", "Volume", "Ticker"
    ]

    missing_columns = [
        column for column in required
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    if data.empty:
        raise ValueError("Dataset is empty.")

    if data["Date"].isna().any():
        raise ValueError("Missing dates found.")

    if data["Date"].duplicated().any():
        raise ValueError("Duplicate dates found.")

    price_columns = ["Open", "High", "Low", "Close"]

    if data[price_columns].isna().any().any():
        raise ValueError("Missing OHLC prices found.")

    if data["Volume"].isna().any():
        raise ValueError("Missing volume found.")

    if (data[price_columns] <= 0).any().any():
        raise ValueError("Zero or negative prices found.")

    if (data["Volume"] < 0).any():
        raise ValueError("Negative volume found.")

    if (data["High"] < data["Low"]).any():
        raise ValueError("High is below Low.")

    if (data["High"] < data[["Open", "Close"]].max(axis=1)).any():
        raise ValueError("High is below Open or Close.")

    if (data["Low"] > data[["Open", "Close"]].min(axis=1)).any():
        raise ValueError("Low is above Open or Close.")

    if not data["Ticker"].eq(ticker).all():
        raise ValueError("Unexpected ticker values found.")


# --------------------------------------------------
# 4. DOWNLOAD ALL COMPANIES
# --------------------------------------------------

def download_all_stocks():
    successful_data = []
    failed_tickers = {}

    for ticker in TICKERS:
        try:
            stock_data = download_stock_data(ticker)
            successful_data.append(stock_data)

        except Exception as error:
            failed_tickers[ticker] = str(error)
            logging.error("%s permanently failed: %s", ticker, error)

        # Brief pause between companies.
        time.sleep(1)

    if not successful_data:
        raise RuntimeError(
            "No companies downloaded successfully."
        )

    combined_data = pd.concat(
        successful_data,
        ignore_index=True
    )
    combined_data = combined_data.sort_values(
        ["Ticker", "Date"]
    ).reset_index(drop=True)

    combined_data["Daily_Return_Pct"] = (
            combined_data.groupby("Ticker")["Adj_Close"]
            .pct_change(fill_method=None) * 100
    )
    combined_data["Abs_Daily_Return_Pct"] = (
        combined_data["Daily_Return_Pct"].abs()
    )
    combined_data["Cumulative_Return_Pct"] = (
            (
                combined_data.groupby("Ticker")["Adj_Close"]
                .transform(lambda prices: prices / prices.iloc[0] * 100)
            ) - 100
    )
    combined_data["Annualized_Volatility_Pct"] = (
        combined_data.groupby("Ticker")["Daily_Return_Pct"]
        .transform(
            lambda returns: returns.rolling(window=252, min_periods=200)
                            .std() * (252 ** 0.5)
        )
    )
    # Final combined-data validation.
    duplicate_records = combined_data.duplicated(
        subset=["Ticker", "Date"]
    )

    if duplicate_records.any():
        raise ValueError(
            "Duplicate ticker-date records found. "
            "CSV was not saved."
        )

    combined_data = combined_data.sort_values(
        ["Ticker", "Date"]
    ).reset_index(drop=True)

    combined_data.to_csv(
        OUTPUT_FILE,
        index=False,
        date_format="%Y-%m-%d",
    )

    # Report the outcome.
    print("\n" + "=" * 45)
    print("DOWNLOAD SUMMARY")
    print("=" * 45)
    print(f"Requested companies: {len(TICKERS)}")
    print(f"Successful companies: {len(successful_data)}")
    print(f"Failed companies: {len(failed_tickers)}")
    print(f"Total observations: {len(combined_data)}")
    print(
        "Unique companies in output:",
        combined_data["Ticker"].nunique()
    )
    print(
        "Duplicate ticker-date records:",
        combined_data.duplicated(
            subset=["Ticker", "Date"]
        ).sum()
    )
    print(f"Output file: {OUTPUT_FILE}")

    print("\nRows per company:")
    print(combined_data.groupby("Ticker").size().to_string())

    if failed_tickers:
        print("\nFAILED TICKERS")
        for ticker, error in failed_tickers.items():
            print(f"{ticker}: {error}")

    return combined_data


# --------------------------------------------------
# 5. ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    combined_data = download_all_stocks()

    print("\n--- DATA QUALITY AUDIT ---")
    print("Total rows:", len(combined_data))
    print("Unique companies:", combined_data["Ticker"].nunique())

    print("\nMissing values:")
    print(combined_data.isna().sum())

    print("\nDate range:")
    print(combined_data["Date"].min(), "to", combined_data["Date"].max())

    print("\nCompanies present:")
    print(sorted(combined_data["Ticker"].unique()))

    print("\n--- DAILY RETURN CHECK ---")
    print(
        combined_data[
            ["Ticker", "Date", "Adj_Close", "Daily_Return_Pct"]
        ].head(10)
    )

    print(
        "Missing daily returns:",
        combined_data["Daily_Return_Pct"].isna().sum()
    )
    print("\n--- RETURN METRICS CHECK ---")
    print(
        combined_data[
            ["Ticker", "Date", "Daily_Return_Pct",
             "Abs_Daily_Return_Pct"]
        ].head(10)
    )
    print("\n--- CUMULATIVE PERFORMANCE CHECK ---")
    print(
        combined_data.groupby("Ticker")["Cumulative_Return_Pct"]
        .agg(["first", "last", "min", "max"])
        .head(10)
    )
    print("\n--- VOLATILITY CHECK ---")
    print(
        combined_data.groupby("Ticker")["Annualized_Volatility_Pct"]
        .last()
        .sort_values(ascending=False)
        .head(10)
    )