import json
import logging
import os
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional

import pytz

from live_trade_bench.fetchers.stock_fetcher import StockFetcher

from .config import (
    MARKET_HOURS,
    MODELS_DATA_FILE,
    TRADING_CONFIG,
    UPDATE_FREQUENCY,
    is_market_hours,
    is_trading_day,
)

logger = logging.getLogger(__name__)

_NEXT_UPDATE_TIMES: Dict[str, Optional[datetime]] = {
    "stock": None,
    "polymarket": None,
}


def get_next_price_update_time(
    market: str = "stock", now_utc: Optional[datetime] = None
) -> Optional[datetime]:
    if market not in _NEXT_UPDATE_TIMES:
        return None

    if _NEXT_UPDATE_TIMES[market] is None:
        reference = now_utc or datetime.now(pytz.UTC)
        _NEXT_UPDATE_TIMES[market] = _compute_next_price_update_time(market, reference)

    return _NEXT_UPDATE_TIMES[market]


def _set_next_price_update_time(market: str, value: Optional[datetime]) -> None:
    if market in _NEXT_UPDATE_TIMES:
        _NEXT_UPDATE_TIMES[market] = value


def _compute_next_price_update_time(market: str, now_utc: datetime) -> datetime:
    if market == "polymarket":
        interval = timedelta(seconds=UPDATE_FREQUENCY["polymarket_prices"])
        return (now_utc + interval).astimezone(pytz.UTC)

    # Default to stock market schedule
    tz = pytz.timezone("US/Eastern")
    est_now = now_utc.astimezone(tz)

    interval = timedelta(seconds=UPDATE_FREQUENCY["realtime_prices"])
    candidate = est_now + interval

    open_hour, open_minute = map(int, MARKET_HOURS["stock_open"].split(":"))
    close_hour, close_minute = map(int, MARKET_HOURS["stock_close"].split(":"))

    close_today = est_now.replace(
        hour=close_hour, minute=close_minute, second=0, microsecond=0
    )

    if candidate <= close_today:
        open_today = est_now.replace(
            hour=open_hour, minute=open_minute, second=0, microsecond=0
        )
        if candidate < open_today:
            candidate = open_today
        return candidate.astimezone(pytz.UTC)

    trading_days = set(MARKET_HOURS["trading_days"])
    next_day = est_now.date()

    while True:
        next_day += timedelta(days=1)
        if next_day.weekday() in trading_days:
            break

    next_open_est = tz.localize(
        datetime.combine(next_day, time(open_hour, open_minute))
    )
    return next_open_est.astimezone(pytz.UTC)


def _load_models_data() -> Optional[List[Dict]]:
    try:
        with open(MODELS_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Models data file not found: {MODELS_DATA_FILE}")
        return None
    except Exception as exc:
        logger.error(f"Failed to load models data: {exc}")
        return None


def _save_models_data(models_data: List[Dict]) -> None:
    with open(MODELS_DATA_FILE, "w") as fh:
        json.dump(models_data, fh, indent=4)


def _update_profit_history(model: Dict, total_value: float, profit: float) -> None:
    try:
        history = model.setdefault("profitHistory", [])
        current_timestamp = datetime.now().isoformat()
        current_date = current_timestamp[:10]
        new_entry = {
            "timestamp": current_timestamp,
            "profit": profit,
            "totalValue": total_value,
        }

        if history:
            last_entry = history[-1]
            last_date = last_entry.get("timestamp", "")[:10]
            if last_date == current_date:
                history[-1] = new_entry
            else:
                history.append(new_entry)
        else:
            history.append(new_entry)
    except Exception as exc:
        logger.error(
            f"Failed to update profit history for {model.get('name', 'Unknown')}: {exc}"
        )


class RealtimePriceUpdater:
    def __init__(self):
        self.stock_fetcher = StockFetcher()

    def _is_first_startup(self) -> bool:
        """检查是否需要初始化benchmark模型（没有benchmark模型）"""
        try:
            # 文件不存在时肯定需要初始化
            if not os.path.exists(MODELS_DATA_FILE):
                return True

            with open(MODELS_DATA_FILE, "r") as f:
                data = json.load(f)

            # 检查是否存在benchmark模型 (QQQ/VOO)
            benchmark_models = [
                m for m in data if m.get("id") in ["qqq-benchmark", "voo-benchmark"]
            ]
            has_benchmarks = len(benchmark_models) > 0

            logger.debug(
                f"Found {len(benchmark_models)} benchmark models, needs initialization: {not has_benchmarks}"
            )
            return not has_benchmarks

        except Exception as e:
            logger.error(f"Failed to check benchmark status: {e}")
            return True  # 出错时默认认为需要初始化

    def update_realtime_prices_and_values(self) -> None:
        """主要入口函数：更新所有模型的实时价格和计算值"""
        try:
            needs_benchmark_init = self._is_first_startup()

            # 检查是否为交易日，但需要初始化benchmark时允许运行
            if not needs_benchmark_init:
                if not is_trading_day():
                    logger.info("📅 Not a trading day, skipping price update")
                    next_time = _compute_next_price_update_time(
                        "stock", datetime.now(pytz.UTC)
                    )
                    _set_next_price_update_time("stock", next_time)
                    return

                if not is_market_hours():
                    logger.info("🕒 Outside market hours, skipping price update")
                    next_time = _compute_next_price_update_time(
                        "stock", datetime.now(pytz.UTC)
                    )
                    _set_next_price_update_time("stock", next_time)
                    return

            if needs_benchmark_init:
                logger.info("🔄 No benchmark models found, running initialization...")
            else:
                logger.info("🔄 Starting realtime price update...")

            # 读取当前JSON数据
            models_data = _load_models_data()
            if not models_data:
                logger.warning("⚠️ No models data found, skipping update")
                next_time = _compute_next_price_update_time(
                    "stock", datetime.now(pytz.UTC)
                )
                _set_next_price_update_time("stock", next_time)
                return

            # 收集所有需要更新的股票symbols
            symbols = self._collect_all_symbols(models_data)
            logger.info(f"📊 Updating prices for {len(symbols)} symbols: {symbols}")

            # 批量获取实时价格
            price_cache = self._fetch_prices_batch(symbols)

            # 更新所有stock模型的实时数据
            updated_count = 0
            for model in models_data:
                if model.get("category") == "stock":
                    if self._update_single_model_realtime_data(model, price_cache):
                        updated_count += 1

            # 添加/更新QQQ和VOO benchmark模型
            self._update_benchmark_models(models_data, price_cache)

            # 保存更新后的数据
            _save_models_data(models_data)

            logger.info(
                f"✅ Successfully updated {updated_count} stock models + benchmarks"
            )

            next_time = _compute_next_price_update_time("stock", datetime.now(pytz.UTC))
            _set_next_price_update_time("stock", next_time)
            logger.info(f"🕒 Next realtime price update target: {next_time.isoformat()}")

        except Exception as e:
            logger.error(f"❌ Failed to update realtime prices: {e}")
            raise

    def _collect_all_symbols(self, models_data: List[Dict]) -> List[str]:
        """收集所有需要更新价格的股票symbols"""
        symbols = set()

        # 从stock模型中收集symbols
        for model in models_data:
            if model.get("category") == "stock":
                portfolio = model.get("portfolio", {})
                positions = portfolio.get("positions", {})
                symbols.update(positions.keys())

        # 添加QQQ和VOO
        symbols.add("QQQ")
        symbols.add("VOO")

        return list(symbols)

    def _fetch_prices_batch(self, symbols: List[str]) -> Dict[str, float]:
        """批量获取股票实时价格"""
        price_cache = {}

        for symbol in symbols:
            try:
                price = self.stock_fetcher.get_current_price(symbol)
                if price is not None and price > 0:
                    price_cache[symbol] = price
                    logger.debug(f"✅ {symbol}: ${price:.2f}")
                else:
                    logger.warning(f"⚠️ Failed to get price for {symbol}")
            except Exception as e:
                logger.error(f"❌ Error fetching price for {symbol}: {e}")

        return price_cache

    def _update_single_model_realtime_data(
        self, model: Dict, price_cache: Dict[str, float]
    ) -> bool:
        """更新单个stock模型的实时数据"""
        try:
            portfolio = model.get("portfolio", {})
            positions = portfolio.get("positions", {})
            cash = portfolio.get("cash", 0.0)

            # 更新每个position的current_price并计算新的total_value
            total_value = cash

            for symbol, position in positions.items():
                if symbol in price_cache:
                    new_price = price_cache[symbol]
                    position["current_price"] = new_price
                    total_value += position["quantity"] * new_price
                else:
                    # 如果没有获取到新价格，使用现有价格
                    current_price = position.get("current_price", 0.0)
                    total_value += position["quantity"] * current_price

            # 更新portfolio的total_value
            portfolio["total_value"] = total_value

            # 更新模型级别的profit和performance（基于stock初始资金1000）
            initial_cash = TRADING_CONFIG["initial_cash_stock"]
            model["profit"] = total_value - initial_cash
            model["performance"] = model["profit"] / initial_cash * 100

            # 更新profit history - 添加新的数据点
            _update_profit_history(model, total_value, model["profit"])

            logger.debug(
                f"Updated {model['name']}: total_value=${total_value:.2f}, profit=${model['profit']:.2f}, performance={model['performance']:.4f}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update model {model.get('name', 'Unknown')}: {e}")
            return False

    def _update_benchmark_models(
        self, models_data: List[Dict], price_cache: Dict[str, float]
    ) -> None:
        """添加或更新QQQ和VOO benchmark模型"""

        # 找到stock模型中最早的allocation history日期
        earliest_date = self._find_earliest_allocation_date(models_data)
        if not earliest_date:
            logger.warning("⚠️ No allocation history found, skipping benchmark update")
            return

        # 移除现有的benchmark模型
        models_data[:] = [m for m in models_data if m.get("category") != "benchmark"]

        # 为QQQ和VOO创建benchmark模型
        for symbol in ["QQQ", "VOO"]:
            if symbol in price_cache:
                benchmark_model = self._create_benchmark_model(
                    symbol, earliest_date, price_cache[symbol]
                )
                if benchmark_model:
                    models_data.append(benchmark_model)
                    logger.info(f"📈 Added benchmark model for {symbol}")

    def _find_earliest_allocation_date(self, models_data: List[Dict]) -> Optional[str]:
        """找到所有stock模型中最早的allocation历史日期"""
        earliest_date = "2025-08-18"

        for model in models_data:
            if model.get("category") == "stock":
                allocation_history = model.get("allocationHistory", [])
                for entry in allocation_history:
                    timestamp = entry.get("timestamp", "")
                    if timestamp:
                        date_str = timestamp[:10]  # 取YYYY-MM-DD部分
                        if earliest_date is None or date_str < earliest_date:
                            earliest_date = date_str

        return earliest_date

    def _create_benchmark_model(
        self, symbol: str, earliest_date: str, current_price: float
    ) -> Optional[Dict]:
        """创建QQQ或VOO的benchmark模型"""
        try:
            # 固定基准价格，避免不同环境的复权差异
            baseline_prices = {
                "QQQ": 577.11,
                "VOO": 591.36,
            }

            if symbol in baseline_prices:
                earliest_price = baseline_prices[symbol]
            else:
                earliest_price = self.stock_fetcher.get_price(symbol, earliest_date)

            if earliest_price is None or earliest_price <= 0:
                logger.warning(
                    f"⚠️ Failed to get earliest price for {symbol} on {earliest_date}"
                )
                return None

            # 计算return rate
            profit = current_price - earliest_price
            performance = profit / earliest_price * 100

            benchmark_names = {
                "QQQ": "QQQ (Invesco QQQ Trust)",
                "VOO": "VOO (Vanguard S&P 500 ETF)",
            }

            benchmark_model = {
                "id": f"{symbol.lower()}-benchmark",
                "name": benchmark_names.get(symbol, f"{symbol} ETF"),
                "category": "benchmark",
                "status": "active",
                "performance": performance,
                "profit": profit,
                "trades": 0,
                "asset_allocation": {symbol: 1.0},
                "benchmark_data": {
                    "symbol": symbol,
                    "earliest_price": earliest_price,
                    "earliest_date": earliest_date,
                    "current_price": current_price,
                },
            }

            logger.info(
                f"📊 {symbol} benchmark: earliest=${earliest_price:.2f}, current=${current_price:.2f}, return={performance:.4f}"
            )
            return benchmark_model

        except Exception as e:
            logger.error(f"Failed to create benchmark model for {symbol}: {e}")
            return None

    # keep length of profit_history to 500 if needed in future


class PolymarketPriceUpdater:
    def __init__(self) -> None:
        self.initial_cash = TRADING_CONFIG["initial_cash_polymarket"]

    def update_realtime_prices_and_values(self) -> None:
        try:
            models_data = _load_models_data()
            if not models_data:
                logger.warning("⚠️ No models data found, skipping polymarket update")
                return

            price_cache = self._build_price_cache()
            if not price_cache:
                logger.warning("⚠️ No polymarket price data available, skipping update")
                return

            updated_count = 0
            for model in models_data:
                if model.get("category") != "polymarket":
                    continue
                if self._update_single_model(model, price_cache):
                    updated_count += 1

            _save_models_data(models_data)
            logger.info(f"✅ Successfully updated {updated_count} polymarket models")

        except Exception as exc:
            logger.error(f"❌ Failed to update polymarket prices: {exc}")
            raise
        finally:
            next_time = _compute_next_price_update_time(
                "polymarket", datetime.now(pytz.UTC)
            )
            _set_next_price_update_time("polymarket", next_time)
            logger.info(
                f"🕒 Next polymarket price update target: {next_time.isoformat()}"
            )

    def _build_price_cache(self) -> Dict[str, float]:
        system = self._get_polymarket_system()
        if system is None:
            return {}

        try:
            market_data = system._fetch_market_data()
        except Exception as exc:
            logger.error(f"❌ Failed to fetch polymarket market data: {exc}")
            return {}

        price_cache: Dict[str, float] = {}
        for symbol, payload in market_data.items():
            price = payload.get("price")
            if price is None:
                continue
            try:
                price_cache[symbol] = float(price)
            except (TypeError, ValueError):
                continue
        return price_cache

    def _get_polymarket_system(self):
        try:
            from .main import get_polymarket_system

            system = get_polymarket_system()
            if system is not None:
                return system
        except Exception:
            pass

        try:
            from live_trade_bench.systems import PolymarketPortfolioSystem

            return PolymarketPortfolioSystem.get_instance()
        except Exception as exc:
            logger.error(f"❌ Unable to access polymarket system: {exc}")
            return None

    def _update_single_model(
        self, model: Dict[str, Any], price_cache: Dict[str, float]
    ) -> bool:
        try:
            portfolio = model.get("portfolio", {})
            positions = portfolio.get("positions", {}) or {}
            cash = float(portfolio.get("cash", 0.0))
            total_value = cash

            for symbol, position in positions.items():
                price = price_cache.get(symbol)
                if price is not None:
                    position["current_price"] = price
                else:
                    price = float(position.get("current_price", 0.0))

                quantity = float(position.get("quantity", 0.0))
                total_value += quantity * price

            portfolio["total_value"] = total_value

            profit = total_value - self.initial_cash
            model["profit"] = profit
            model["performance"] = (
                (profit / self.initial_cash) * 100 if self.initial_cash else 0.0
            )

            _update_profit_history(model, total_value, profit)

            logger.debug(
                f"Updated polymarket model {model.get('name', 'Unknown')}: total_value=${total_value:.2f}, profit=${profit:.2f}"
            )
            return True

        except Exception as exc:
            logger.error(
                f"❌ Failed to update polymarket model {model.get('name', 'Unknown')}: {exc}"
            )
            return False


class BitMEXPriceUpdater:
    """Price updater for BitMEX perpetual contracts."""

    def __init__(self) -> None:
        self.initial_cash = 1000.0  # BitMEX initial cash

    def update_realtime_prices_and_values(self) -> None:
        """Update BitMEX contract prices and account values (synced with stock market hours)."""
        try:
            # Check if it's trading hours (sync with stock market to prevent file conflicts)
            if not is_trading_day():
                logger.info("📅 Not a trading day, skipping BitMEX price update")
                return

            if not is_market_hours():
                logger.info("🕒 Outside market hours, skipping BitMEX price update")
                return

            logger.info("🔄 Starting BitMEX price update...")
            models_data = _load_models_data()
            if not models_data:
                logger.warning("⚠️ No models data found, skipping BitMEX update")
                return

            price_cache = self._build_price_cache()
            if not price_cache:
                logger.warning("⚠️ No BitMEX price data available, skipping update")
                return

            updated_count = 0
            for model in models_data:
                if model.get("category") != "bitmex":
                    continue
                if self._update_single_model(model, price_cache):
                    updated_count += 1

            # Add/update crypto benchmarks (BTC-HOLD, ETH-HOLD)
            self._update_crypto_benchmark_models(models_data, price_cache)

            _save_models_data(models_data)
            logger.info(f"✅ Successfully updated {updated_count} BitMEX models + benchmarks")

        except Exception as exc:
            logger.error(f"❌ Failed to update BitMEX prices: {exc}")
            raise

    def _build_price_cache(self) -> Dict[str, float]:
        """Fetch current prices for all BitMEX contracts."""
        system = self._get_bitmex_system()
        if system is None:
            return {}

        try:
            # Fetch market data including current prices
            market_data = system._fetch_market_data()
        except Exception as exc:
            logger.error(f"❌ Failed to fetch BitMEX market data: {exc}")
            return {}

        price_cache: Dict[str, float] = {}
        for symbol, payload in market_data.items():
            price = payload.get("current_price")
            if price is None:
                continue
            try:
                price_cache[symbol] = float(price)
            except (TypeError, ValueError):
                continue

        logger.debug(f"📊 Fetched prices for {len(price_cache)} BitMEX contracts")
        return price_cache

    def _get_bitmex_system(self):
        """Get BitMEX system instance."""
        try:
            from .main import get_bitmex_system

            system = get_bitmex_system()
            if system is not None:
                return system
        except Exception:
            pass

        try:
            from live_trade_bench.systems import BitMEXPortfolioSystem

            return BitMEXPortfolioSystem.get_instance()
        except Exception as exc:
            logger.error(f"❌ Unable to access BitMEX system: {exc}")
            return None

    def _update_single_model(
        self, model: Dict[str, Any], price_cache: Dict[str, float]
    ) -> bool:
        """Update a single BitMEX model with new prices."""
        try:
            portfolio = model.get("portfolio", {})
            positions = portfolio.get("positions", {}) or {}
            cash = float(portfolio.get("cash", 0.0))
            total_value = cash

            for symbol, position in positions.items():
                price = price_cache.get(symbol)
                if price is not None:
                    position["current_price"] = price
                else:
                    price = float(position.get("current_price", 0.0))

                quantity = float(position.get("quantity", 0.0))
                total_value += quantity * price

            portfolio["total_value"] = total_value

            profit = total_value - self.initial_cash
            model["profit"] = profit
            model["performance"] = (
                (profit / self.initial_cash) * 100 if self.initial_cash else 0.0
            )

            _update_profit_history(model, total_value, profit)

            logger.debug(
                f"Updated BitMEX model {model.get('name', 'Unknown')}: total_value=${total_value:.2f}, profit=${profit:.2f}"
            )
            return True

        except Exception as exc:
            logger.error(
                f"❌ Failed to update BitMEX model {model.get('name', 'Unknown')}: {exc}"
            )
            return False

    def _update_crypto_benchmark_models(
        self, models_data: List[Dict], price_cache: Dict[str, float]
    ) -> None:
        """Add or update BTC-HOLD and ETH-HOLD benchmark models."""
        # Find earliest allocation date from BitMEX models
        earliest_date = self._find_earliest_bitmex_date(models_data)
        if not earliest_date:
            logger.warning("⚠️ No BitMEX allocation history found, skipping crypto benchmarks")
            return

        # Remove existing bitmex benchmark models
        models_data[:] = [
            m for m in models_data
            if m.get("category") != "bitmex-benchmark"
        ]

        # Create benchmarks for BTC and ETH
        benchmarks = [
            ("XBTUSD", "BTC-HOLD (Bitcoin Buy & Hold)"),
            ("ETHUSD", "ETH-HOLD (Ethereum Buy & Hold)"),
        ]

        for symbol, name in benchmarks:
            if symbol in price_cache:
                benchmark_model = self._create_crypto_benchmark(
                    symbol, name, earliest_date, price_cache[symbol]
                )
                if benchmark_model:
                    models_data.append(benchmark_model)
                    logger.info(f"📈 Added crypto benchmark: {name}")

    def _find_earliest_bitmex_date(self, models_data: List[Dict]) -> Optional[str]:
        """Find the earliest allocation date from all BitMEX models."""
        earliest_date = None

        for model in models_data:
            if model.get("category") == "bitmex":
                allocation_history = model.get("allocationHistory", [])
                for entry in allocation_history:
                    timestamp = entry.get("timestamp", "")
                    if timestamp:
                        date_str = timestamp[:10]  # Extract YYYY-MM-DD
                        if earliest_date is None or date_str < earliest_date:
                            earliest_date = date_str

        return earliest_date

    def _create_crypto_benchmark(
        self, symbol: str, name: str, earliest_date: str, current_price: float
    ) -> Optional[Dict]:
        """Create a crypto buy-and-hold benchmark model."""
        try:
            from live_trade_bench.fetchers.bitmex_fetcher import BitMEXFetcher

            fetcher = BitMEXFetcher()

            # Get historical price for earliest date
            from datetime import datetime, timedelta
            earliest_dt = datetime.strptime(earliest_date, "%Y-%m-%d")
            start_dt = earliest_dt - timedelta(days=1)
            end_dt = earliest_dt + timedelta(days=1)

            try:
                history = fetcher.get_price_history(symbol, start_dt, end_dt, "1d")
                if history and len(history) > 0:
                    earliest_price = float(history[0].get("close", 0))
                else:
                    logger.warning(f"⚠️ No historical price for {symbol} on {earliest_date}")
                    return None
            except Exception as e:
                logger.error(f"Failed to fetch historical price for {symbol}: {e}")
                return None

            if earliest_price is None or earliest_price <= 0:
                logger.warning(f"⚠️ Invalid earliest price for {symbol}")
                return None

            # Calculate return
            profit = current_price - earliest_price
            performance = profit / earliest_price * 100

            benchmark_id = symbol.lower().replace("usd", "-hold")

            benchmark_model = {
                "id": benchmark_id,
                "name": name,
                "category": "bitmex-benchmark",
                "status": "active",
                "performance": performance,
                "profit": profit,
                "trades": 0,
                "asset_allocation": {symbol: 1.0},
                "benchmark_data": {
                    "symbol": symbol,
                    "earliest_price": earliest_price,
                    "earliest_date": earliest_date,
                    "current_price": current_price,
                },
            }

            logger.info(
                f"📊 {symbol} benchmark: earliest=${earliest_price:.2f}, "
                f"current=${current_price:.2f}, return={performance:.2f}%"
            )
            return benchmark_model

        except Exception as e:
            logger.error(f"Failed to create crypto benchmark for {symbol}: {e}")
            return None


# 全局实例
stock_price_updater = RealtimePriceUpdater()
polymarket_price_updater = PolymarketPriceUpdater()
bitmex_price_updater = BitMEXPriceUpdater()


def update_stock_prices_and_values() -> None:
    stock_price_updater.update_realtime_prices_and_values()


def update_polymarket_prices_and_values() -> None:
    polymarket_price_updater.update_realtime_prices_and_values()


def update_bitmex_prices_and_values() -> None:
    """Update BitMEX perpetual contract prices (24/7 crypto markets)."""
    bitmex_price_updater.update_realtime_prices_and_values()


def update_realtime_prices_and_values() -> None:
    """Backward-compatible alias for stock price updates."""
    update_stock_prices_and_values()
