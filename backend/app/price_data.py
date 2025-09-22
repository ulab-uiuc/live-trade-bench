import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from live_trade_bench.fetchers.stock_fetcher import StockFetcher

from .config import MODELS_DATA_FILE, is_trading_day

logger = logging.getLogger(__name__)


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
            if not is_trading_day() and not needs_benchmark_init:
                logger.info("📅 Not a trading day, skipping price update")
                return

            if needs_benchmark_init:
                logger.info("🔄 No benchmark models found, running initialization...")
            else:
                logger.info("🔄 Starting realtime price update...")

            # 读取当前JSON数据
            models_data = self._load_models_data()
            if not models_data:
                logger.warning("⚠️ No models data found, skipping update")
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
            self._save_models_data(models_data)

            logger.info(
                f"✅ Successfully updated {updated_count} stock models + benchmarks"
            )

        except Exception as e:
            logger.error(f"❌ Failed to update realtime prices: {e}")
            raise

    def _load_models_data(self) -> Optional[List[Dict]]:
        """加载现有的模型数据"""
        try:
            with open(MODELS_DATA_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Models data file not found: {MODELS_DATA_FILE}")
            return None
        except Exception as e:
            logger.error(f"Failed to load models data: {e}")
            return None

    def _save_models_data(self, models_data: List[Dict]) -> None:
        """保存更新后的模型数据"""
        with open(MODELS_DATA_FILE, "w") as f:
            json.dump(models_data, f, indent=4)

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
            initial_cash = 1000.0
            model["profit"] = total_value - initial_cash
            model["performance"] = model["profit"] / initial_cash * 100

            # 更新profit history - 添加新的数据点
            self._update_profit_history(model, total_value, model["profit"])

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
            # 获取最早日期的价格
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

    def _update_profit_history(
        self, model: Dict, total_value: float, profit: float
    ) -> None:
        try:
            if "profitHistory" not in model:
                model["profitHistory"] = []

            current_timestamp = datetime.now().isoformat()
            current_date = current_timestamp[:10]  # YYYY-MM-DD

            new_entry = {
                "timestamp": current_timestamp,
                "profit": profit,
                "totalValue": total_value,
            }

            profit_history = model["profitHistory"]

            if profit_history:
                last_entry = profit_history[-1]
                last_entry_date = last_entry["timestamp"][:10]  # YYYY-MM-DD

                if last_entry_date == current_date:
                    profit_history[-1] = new_entry
                    logger.debug(
                        f"Updated today's profit history entry for {model.get('name', 'Unknown')}"
                    )
                else:
                    profit_history.append(new_entry)
                    logger.debug(
                        f"Added new profit history entry for {model.get('name', 'Unknown')}"
                    )
            else:
                profit_history.append(new_entry)
                logger.debug(
                    f"Added first profit history entry for {model.get('name', 'Unknown')}"
                )
            # keep length of profit_history to 500
            # if len(profit_history) > 500:
            #     model["profitHistory"] = profit_history[-500:]

        except Exception as e:
            logger.error(
                f"Failed to update profit history for {model.get('name', 'Unknown')}: {e}"
            )


# 全局实例
price_updater = RealtimePriceUpdater()


def update_realtime_prices_and_values():
    """供定时任务调用的函数"""
    price_updater.update_realtime_prices_and_values()
