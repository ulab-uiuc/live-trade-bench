from datetime import datetime
from typing import Any, Dict, List

import yfinance as yf

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class OptionFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        super().__init__(min_delay, max_delay)

    def fetch(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            "OptionFetcher does not have a general fetch method. Please use specialized methods such as fetch_option_chain or fetch_option_data."
        )

    def fetch_option_chain(
        self, ticker: str, expiration_date: str | None = None
    ) -> Dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            if expiration_date:
                options = stock.option_chain(expiration_date)
                return {
                    "ticker": ticker,
                    "expiration": expiration_date,
                    "calls": options.calls.to_dict("records"),
                    "puts": options.puts.to_dict("records"),
                    "underlying_price": stock.info.get("regularMarketPrice", 0),
                }
            else:
                expirations = stock.options
                if not expirations:
                    raise RuntimeError(f"No options available for {ticker}")
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
    ) -> Dict[str, Any]:
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
            if option_type in ["calls", "both"]:
                calls_df = options.calls
                if min_strike is not None:
                    calls_df = calls_df[calls_df["strike"] >= min_strike]
                if max_strike is not None:
                    calls_df = calls_df[calls_df["strike"] <= max_strike]
                result["calls"] = calls_df.to_dict("records")
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

    def fetch_option_expirations(self, ticker: str) -> List[str]:
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            if not expirations:
                raise RuntimeError(f"No options available for {ticker}")
            return list(expirations)
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
    ) -> Dict[str, Any]:
        try:
            date_obj = datetime.strptime(expiration_date, "%Y-%m-%d")
            date_str = date_obj.strftime("%y%m%d")
            strike_str = f"{int(strike * 1000):08d}"
            option_type_char = "C" if option_type.lower() == "call" else "P"
            option_symbol = f"{ticker}{date_str}{option_type_char}{strike_str}"
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
    ) -> Dict[str, float]:
        import math

        from scipy.stats import norm

        S = underlying_price
        K = strike
        T = time_to_expiry
        r = risk_free_rate
        sigma = volatility
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        if option_type.lower() == "call":
            delta = float(norm.cdf(d1))
            theta = -S * float(norm.pdf(d1)) * sigma / (
                2 * math.sqrt(T)
            ) - r * K * math.exp(-r * T) * float(norm.cdf(d2))
        else:
            delta = float(norm.cdf(d1)) - 1.0
            theta = -S * float(norm.pdf(d1)) * sigma / (
                2 * math.sqrt(T)
            ) + r * K * math.exp(-r * T) * float(norm.cdf(-d2))
        gamma = float(norm.pdf(d1)) / (S * sigma * math.sqrt(T))
        vega = float(S * float(norm.pdf(d1)) * math.sqrt(T))
        rho = float(
            K * T * math.exp(-r * T) * float(norm.cdf(d2))
            if option_type.lower() == "call"
            else -K * T * math.exp(-r * T) * float(norm.cdf(-d2))
        )
        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "theta": float(theta),
            "vega": float(vega),
            "rho": float(rho),
        }

    def get_atm_options(
        self, ticker: str, expiration_date: str, strike_range: float = 0.1
    ) -> Dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.info.get("regularMarketPrice", 0)
            if current_price == 0:
                raise RuntimeError(f"Unable to get current price for {ticker}")
            min_strike = current_price * (1 - strike_range)
            max_strike = current_price * (1 + strike_range)
            options = self.fetch_option_data(
                ticker=ticker,
                expiration_date=expiration_date,
                option_type="both",
                min_strike=min_strike,
                max_strike=max_strike,
            )
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
        import math

        from scipy.stats import norm

        def black_scholes_price(
            S: float, K: float, T: float, r: float, sigma: float, option_type: str
        ) -> float:
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            if option_type.lower() == "call":
                return float(S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2))
            else:
                return float(K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))

        def black_scholes_vega(
            S: float, K: float, T: float, r: float, sigma: float
        ) -> float:
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            return float(S * math.sqrt(T) * norm.pdf(d1))

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
            sigma = max(0.001, sigma)
        raise RuntimeError("Failed to converge on implied volatility")

    def get_option_chain_summary(
        self, ticker: str, expiration_date: str | None = None
    ) -> Dict[str, Any]:
        try:
            option_chain = self.fetch_option_chain(ticker, expiration_date)
            calls = option_chain["calls"]
            puts = option_chain["puts"]
            underlying_price = option_chain["underlying_price"]
            call_strikes = [call["strike"] for call in calls]
            call_volumes = [call["volume"] for call in calls]
            call_open_interest = [call.get("openInterest", 0) for call in calls]
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
                "put_call_ratio": (
                    sum(put_volumes) / sum(call_volumes) if sum(call_volumes) > 0 else 0
                ),
            }
            return summary
        except Exception as e:
            raise RuntimeError(f"Failed to get option chain summary for {ticker}: {e}")


def fetch_option_chain(
    ticker: str, expiration_date: str | None = None
) -> Dict[str, Any]:
    fetcher = OptionFetcher()
    return fetcher.fetch_option_chain(ticker, expiration_date)


def fetch_option_data(
    ticker: str,
    expiration_date: str,
    option_type: str = "both",
    min_strike: float | None = None,
    max_strike: float | None = None,
) -> Dict[str, Any]:
    fetcher = OptionFetcher()
    return fetcher.fetch_option_data(
        ticker, expiration_date, option_type, min_strike, max_strike
    )


def fetch_option_expirations(ticker: str) -> List[str]:
    fetcher = OptionFetcher()
    return fetcher.fetch_option_expirations(ticker)


def fetch_option_historical_data(
    ticker: str,
    expiration_date: str,
    strike: float,
    option_type: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
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


def get_option_chain_summary(
    ticker: str, expiration_date: str | None = None
) -> Dict[str, Any]:
    fetcher = OptionFetcher()
    return fetcher.get_option_chain_summary(ticker, expiration_date)
