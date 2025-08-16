"""
Option data fetcher for trading bench.

This module provides functions to fetch option data from Yahoo Finance
using yfinance library, including option chains, Greeks calculations,
and historical option data.
"""

from datetime import datetime

import yfinance as yf

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class OptionFetcher(BaseFetcher):
    """Fetcher for option data from Yahoo Finance."""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Initialize the option fetcher."""
        super().__init__(min_delay, max_delay)

    def fetch(self, *args, **kwargs):
        raise NotImplementedError(
            "OptionFetcher does not have a general fetch method. Please use specialized methods such as fetch_option_chain or fetch_option_data."
        )

    def fetch_option_chain(
        self, ticker: str, expiration_date: str | None = None
    ) -> dict:
        """
        Fetches option chain data for a given ticker and expiration date.
        Args:
            ticker:           Stock ticker symbol.
            expiration_date:  Option expiration date in YYYY-MM-DD format.
                             If None, fetches all available expirations.
        Returns:
            dict: Option chain data with calls and puts for each expiration.
        """
        try:
            # Get the stock object
            stock = yf.Ticker(ticker)

            if expiration_date:
                # Get options for specific expiration
                options = stock.option_chain(expiration_date)

                return {
                    "ticker": ticker,
                    "expiration": expiration_date,
                    "calls": options.calls.to_dict("records"),
                    "puts": options.puts.to_dict("records"),
                    "underlying_price": stock.info.get("regularMarketPrice", 0),
                }
            else:
                # Get all available expiration dates
                expirations = stock.options

                if not expirations:
                    raise RuntimeError(f"No options available for {ticker}")

                # Get option chain for the nearest expiration
                nearest_exp = expirations[0]
                options = stock.option_chain(nearest_exp)

                return {
                    "ticker": ticker,
                    "expiration": nearest_exp,
                    "calls": options.calls.to_dict("records"),
                    "puts": options.puts.to_dict("records"),
                    "underlying_price": stock.info.get("regularMarketPrice", 0),
                    "available_expirations": expirations,
                }

        except Exception as e:
            raise RuntimeError(f"Failed to fetch option chain for {ticker}: {e}")

    def fetch_option_data(
        self,
        ticker: str,
        expiration_date: str,
        option_type: str = "both",
        min_strike: float | None = None,
        max_strike: float | None = None,
    ) -> dict:
        """
        Fetches detailed option data for a given ticker and expiration.
        Args:
            ticker:           Stock ticker symbol.
            expiration_date:  Option expiration date in YYYY-MM-DD format.
            option_type:      'calls', 'puts', or 'both' (default: 'both').
            min_strike:       Minimum strike price filter (optional).
            max_strike:       Maximum strike price filter (optional).
        Returns:
            dict: Filtered option data with calls and/or puts.
        """
        try:
            stock = yf.Ticker(ticker)
            options = stock.option_chain(expiration_date)

            result = {
                "ticker": ticker,
                "expiration": expiration_date,
                "underlying_price": stock.info.get("regularMarketPrice", 0),
                "calls": [],
                "puts": [],
            }

            # Filter and process calls
            if option_type in ["calls", "both"]:
                calls_df = options.calls
                if min_strike is not None:
                    calls_df = calls_df[calls_df["strike"] >= min_strike]
                if max_strike is not None:
                    calls_df = calls_df[calls_df["strike"] <= max_strike]
                result["calls"] = calls_df.to_dict("records")

            # Filter and process puts
            if option_type in ["puts", "both"]:
                puts_df = options.puts
                if min_strike is not None:
                    puts_df = puts_df[puts_df["strike"] >= min_strike]
                if max_strike is not None:
                    puts_df = puts_df[puts_df["strike"] <= max_strike]
                result["puts"] = puts_df.to_dict("records")

            return result

        except Exception as e:
            raise RuntimeError(f"Failed to fetch option data for {ticker}: {e}")

    def fetch_option_expirations(self, ticker: str) -> list[str]:
        """
        Fetches all available option expiration dates for a ticker.
        Args:
            ticker: Stock ticker symbol.
        Returns:
            list: List of available expiration dates in YYYY-MM-DD format.
        """
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options

            if not expirations:
                raise RuntimeError(f"No options available for {ticker}")

            return expirations

        except Exception as e:
            raise RuntimeError(f"Failed to fetch option expirations for {ticker}: {e}")

    def fetch_option_historical_data(
        self,
        ticker: str,
        expiration_date: str,
        strike: float,
        option_type: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """
        Fetches historical price data for a specific option.
        Args:
            ticker:           Stock ticker symbol.
            expiration_date:  Option expiration date in YYYY-MM-DD format.
            strike:           Strike price of the option.
            option_type:      'call' or 'put'.
            start_date:       Start date in YYYY-MM-DD format.
            end_date:         End date in YYYY-MM-DD format.
        Returns:
            dict: Historical option price data with OHLCV values.
        """
        try:
            # Construct option symbol (e.g., AAPL240119C00150000)
            # Format: TICKER + YYMMDD + C/P + STRIKE*1000
            date_obj = datetime.strptime(expiration_date, "%Y-%m-%d")
            date_str = date_obj.strftime("%y%m%d")
            strike_str = f"{int(strike * 1000):08d}"
            option_type_char = "C" if option_type.lower() == "call" else "P"

            option_symbol = f"{ticker}{date_str}{option_type_char}{strike_str}"

            # Download historical data
            df = yf.download(
                tickers=option_symbol,
                start=start_date,
                end=end_date,
                interval="1d",
                progress=False,
                auto_adjust=True,
            )

            if df.empty:
                raise RuntimeError(f"No historical data found for {option_symbol}")

            # Build date-indexed dict
            data = {}
            for idx, row in df.iterrows():
                date_str = idx.strftime("%Y-%m-%d")
                data[date_str] = {
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }

            return {
                "option_symbol": option_symbol,
                "ticker": ticker,
                "expiration": expiration_date,
                "strike": strike,
                "option_type": option_type,
                "price_data": data,
            }

        except Exception as e:
            raise RuntimeError(f"Failed to fetch historical option data: {e}")

    def calculate_option_greeks(
        self,
        underlying_price: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        option_type: str,
    ) -> dict:
        """
        Calculate option Greeks using Black-Scholes model.
        Args:
            underlying_price: Current price of underlying asset.
            strike:           Strike price of the option.
            time_to_expiry:  Time to expiry in years.
            risk_free_rate:  Risk-free interest rate (decimal).
            volatility:      Implied volatility (decimal).
            option_type:     'call' or 'put'.
        Returns:
            dict: Greeks (delta, gamma, theta, vega, rho).
        """
        import math

        from scipy.stats import norm

        # Black-Scholes parameters
        S = underlying_price
        K = strike
        T = time_to_expiry
        r = risk_free_rate
        sigma = volatility

        # Calculate d1 and d2
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Calculate Greeks
        if option_type.lower() == "call":
            delta = norm.cdf(d1)
            theta = -S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) - r * K * math.exp(
                -r * T
            ) * norm.cdf(d2)
        else:  # put
            delta = norm.cdf(d1) - 1
            theta = -S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) + r * K * math.exp(
                -r * T
            ) * norm.cdf(-d2)

        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
        vega = S * norm.pdf(d1) * math.sqrt(T)
        rho = (
            K * T * math.exp(-r * T) * norm.cdf(d2)
            if option_type.lower() == "call"
            else -K * T * math.exp(-r * T) * norm.cdf(-d2)
        )

        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho,
        }

    def get_atm_options(
        self, ticker: str, expiration_date: str, strike_range: float = 0.1
    ) -> dict:
        """
        Get at-the-money options for a given ticker and expiration.
        Args:
            ticker:           Stock ticker symbol.
            expiration_date:  Option expiration date in YYYY-MM-DD format.
            strike_range:     Range around current price to consider ATM (default: 10%).
        Returns:
            dict: ATM options with calls and puts.
        """
        try:
            # Get current stock price
            stock = yf.Ticker(ticker)
            current_price = stock.info.get("regularMarketPrice", 0)

            if current_price == 0:
                raise RuntimeError(f"Unable to get current price for {ticker}")

            # Calculate strike range
            min_strike = current_price * (1 - strike_range)
            max_strike = current_price * (1 + strike_range)

            # Fetch options in the ATM range
            options = self.fetch_option_data(
                ticker=ticker,
                expiration_date=expiration_date,
                option_type="both",
                min_strike=min_strike,
                max_strike=max_strike,
            )

            # Add current price to result
            options["current_price"] = current_price
            options["strike_range"] = {
                "min": min_strike,
                "max": max_strike,
                "range_percent": strike_range * 100,
            }

            return options

        except Exception as e:
            raise RuntimeError(f"Failed to fetch ATM options for {ticker}: {e}")

    def calculate_implied_volatility(
        self,
        option_price: float,
        underlying_price: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        option_type: str,
        tolerance: float = 1e-5,
        max_iterations: int = 100,
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method.
        Args:
            option_price:     Current option price.
            underlying_price: Current underlying asset price.
            strike:           Strike price.
            time_to_expiry:  Time to expiry in years.
            risk_free_rate:  Risk-free interest rate (decimal).
            option_type:     'call' or 'put'.
            tolerance:       Convergence tolerance.
            max_iterations:  Maximum number of iterations.
        Returns:
            float: Implied volatility (decimal).
        """
        import math

        from scipy.stats import norm

        def black_scholes_price(S, K, T, r, sigma, option_type):
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)

            if option_type.lower() == "call":
                return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
            else:
                return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        def black_scholes_vega(S, K, T, r, sigma):
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            return S * math.sqrt(T) * norm.pdf(d1)

        # Initial guess for volatility
        sigma = 0.3

        for i in range(max_iterations):
            price = black_scholes_price(
                underlying_price,
                strike,
                time_to_expiry,
                risk_free_rate,
                sigma,
                option_type,
            )
            vega = black_scholes_vega(
                underlying_price, strike, time_to_expiry, risk_free_rate, sigma
            )

            diff = option_price - price

            if abs(diff) < tolerance:
                return sigma

            sigma = sigma + diff / vega

            # Ensure volatility is positive
            sigma = max(0.001, sigma)

        raise RuntimeError("Failed to converge on implied volatility")

    def get_option_chain_summary(
        self, ticker: str, expiration_date: str | None = None
    ) -> dict:
        """
        Get a summary of option chain data including key statistics.
        Args:
            ticker:           Stock ticker symbol.
            expiration_date:  Option expiration date (optional).
        Returns:
            dict: Summary statistics of the option chain.
        """
        try:
            option_chain = self.fetch_option_chain(ticker, expiration_date)

            calls = option_chain["calls"]
            puts = option_chain["puts"]
            underlying_price = option_chain["underlying_price"]

            # Calculate statistics for calls
            call_strikes = [call["strike"] for call in calls]
            call_volumes = [call["volume"] for call in calls]
            call_open_interest = [call.get("openInterest", 0) for call in calls]

            # Calculate statistics for puts
            put_strikes = [put["strike"] for put in puts]
            put_volumes = [put["volume"] for put in puts]
            put_open_interest = [put.get("openInterest", 0) for put in puts]

            summary = {
                "ticker": ticker,
                "expiration": option_chain["expiration"],
                "underlying_price": underlying_price,
                "calls": {
                    "count": len(calls),
                    "strike_range": {
                        "min": min(call_strikes) if call_strikes else 0,
                        "max": max(call_strikes) if call_strikes else 0,
                    },
                    "total_volume": sum(call_volumes),
                    "total_open_interest": sum(call_open_interest),
                    "avg_volume": sum(call_volumes) / len(calls) if calls else 0,
                },
                "puts": {
                    "count": len(puts),
                    "strike_range": {
                        "min": min(put_strikes) if put_strikes else 0,
                        "max": max(put_strikes) if put_strikes else 0,
                    },
                    "total_volume": sum(put_volumes),
                    "total_open_interest": sum(put_open_interest),
                    "avg_volume": sum(put_volumes) / len(puts) if puts else 0,
                },
                "total_options": len(calls) + len(puts),
                "put_call_ratio": sum(put_volumes) / sum(call_volumes)
                if sum(call_volumes) > 0
                else 0,
            }

            return summary

        except Exception as e:
            raise RuntimeError(f"Failed to get option chain summary for {ticker}: {e}")


def fetch_option_chain(ticker: str, expiration_date: str | None = None) -> dict:
    """Backward compatibility function."""
    fetcher = OptionFetcher()
    return fetcher.fetch_option_chain(ticker, expiration_date)


def fetch_option_data(
    ticker: str,
    expiration_date: str,
    option_type: str = "both",
    min_strike: float | None = None,
    max_strike: float | None = None,
) -> dict:
    """Backward compatibility function."""
    fetcher = OptionFetcher()
    return fetcher.fetch_option_data(
        ticker, expiration_date, option_type, min_strike, max_strike
    )


def fetch_option_expirations(ticker: str) -> list[str]:
    """Backward compatibility function."""
    fetcher = OptionFetcher()
    return fetcher.fetch_option_expirations(ticker)


def fetch_option_historical_data(
    ticker: str,
    expiration_date: str,
    strike: float,
    option_type: str,
    start_date: str,
    end_date: str,
) -> dict:
    """Backward compatibility function."""
    fetcher = OptionFetcher()
    return fetcher.fetch_option_historical_data(
        ticker, expiration_date, strike, option_type, start_date, end_date
    )


def calculate_option_greeks(
    underlying_price: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    option_type: str,
) -> dict:
    """Backward compatibility function."""
    fetcher = OptionFetcher()
    return fetcher.calculate_option_greeks(
        underlying_price,
        strike,
        time_to_expiry,
        risk_free_rate,
        volatility,
        option_type,
    )


def get_atm_options(
    ticker: str, expiration_date: str, strike_range: float = 0.1
) -> dict:
    """Backward compatibility function."""
    fetcher = OptionFetcher()
    return fetcher.get_atm_options(ticker, expiration_date, strike_range)


def calculate_implied_volatility(
    option_price: float,
    underlying_price: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    option_type: str,
    tolerance: float = 1e-5,
    max_iterations: int = 100,
) -> float:
    """Backward compatibility function."""
    fetcher = OptionFetcher()
    return fetcher.calculate_implied_volatility(
        option_price,
        underlying_price,
        strike,
        time_to_expiry,
        risk_free_rate,
        option_type,
        tolerance,
        max_iterations,
    )


def get_option_chain_summary(ticker: str, expiration_date: str | None = None) -> dict:
    """Backward compatibility function."""
    fetcher = OptionFetcher()
    return fetcher.get_option_chain_summary(ticker, expiration_date)
