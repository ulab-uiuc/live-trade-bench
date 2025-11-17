# backtest_demo_simple.py
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from live_trade_bench.systems.bitmex_system import BitMEXPortfolioSystem
from live_trade_bench.systems.polymarket_system import PolymarketPortfolioSystem
from live_trade_bench.systems.stock_system import StockPortfolioSystem

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.app.config import get_base_model_configs
from backend.app.models_data import _create_model_data, _serialize_positions

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def get_backtest_config(args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """Get backtest configuration from CLI args or defaults."""
    if args is None:
        # Defaults when no args provided
        return {
            "start_date": "2025-10-01",
            "end_date": "2025-11-01",
            "interval_days": 1,
            "initial_cash": {"polymarket": 500.0, "stock": 1000.0, "bitmex": 1000.0},
            "parallelism": int(os.environ.get("LTB_PARALLELISM", "16")),
            "threshold": 0.2,
            "market_num": 10,
            "stock_num": 15,
            "bitmex_num": 12,
        }

    # Use CLI args with fallback to defaults
    return {
        "start_date": args.start_date or "2025-10-01",
        "end_date": args.end_date or "2025-11-01",
        "interval_days": args.interval_days,
        "initial_cash": {
            "polymarket": args.initial_cash_polymarket,
            "stock": args.initial_cash_stock,
            "bitmex": args.initial_cash_bitmex,
        },
        "parallelism": int(os.environ.get("LTB_PARALLELISM", "16")),
        "threshold": args.threshold,
        "market_num": args.polymarket_count,
        "stock_num": args.stock_count,
        "bitmex_num": args.bitmex_count,
    }


def get_trading_days(
    start_date: str, end_date: str, interval_days: int = 1
) -> List[datetime]:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days: List[datetime] = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    if interval_days > 1:
        days = days[::interval_days]
    return days


def build_systems(
    models: List[Tuple[str, str]],
    trading_days: List[datetime],
    cash_cfg: Dict[str, float],
    run_polymarket: bool = False,
    run_stock: bool = True,
    run_bitmex: bool = False,
    threshold: float = 0.2,
    market_num: int = 5,
    stock_num: int = 15,
    bitmex_num: int = 12,
    custom_stocks: Optional[List[str]] = None,
    custom_bitmex_symbols: Optional[List[str]] = None,
):
    systems: Dict[str, Dict[str, Any]] = {"polymarket": {}, "stock": {}, "bitmex": {}}

    if run_polymarket:
        print("Pre-fetching verified markets...")
        from live_trade_bench.fetchers.polymarket_fetcher import fetch_verified_markets

        verified_markets = fetch_verified_markets(
            trading_days, limit=market_num, threshold=threshold
        )

    if run_stock:
        if custom_stocks:
            print(f"Using custom stock list: {custom_stocks}")
            verified_stocks = custom_stocks
        else:
            print("Pre-fetching trending stock data...")
            from live_trade_bench.fetchers.stock_fetcher import fetch_trending_stocks

            verified_stocks = fetch_trending_stocks(stock_num)

    if run_bitmex:
        if custom_bitmex_symbols:
            print(f"Using custom BitMEX symbols: {custom_bitmex_symbols}")
            bitmex_symbols = custom_bitmex_symbols
        else:
            print("Pre-fetching trending BitMEX contracts...")
            from live_trade_bench.fetchers.bitmex_fetcher import BitMEXFetcher
            fetcher = BitMEXFetcher()
            trending_contracts = fetcher.get_trending_contracts(limit=bitmex_num)
            bitmex_symbols = [c["symbol"] for c in trending_contracts]
            print(f"  Using {len(bitmex_symbols)} BitMEX contracts: {bitmex_symbols[:5]}...")

    for model_name, model_id in models:
        if run_polymarket:
            pm = PolymarketPortfolioSystem()
            pm.set_universe(verified_markets)
            pm.add_agent(
                name=model_name,
                initial_cash=cash_cfg["polymarket"],
                model_name=model_id,
            )
            systems["polymarket"][model_name] = pm

        if run_stock:
            st = StockPortfolioSystem()
            st.set_universe(verified_stocks)
            st.add_agent(
                name=model_name, initial_cash=cash_cfg["stock"], model_name=model_id
            )
            systems["stock"][model_name] = st

        if run_bitmex:
            bx = BitMEXPortfolioSystem()
            bx.set_universe(bitmex_symbols)
            bx.add_agent(
                name=model_name, initial_cash=cash_cfg["bitmex"], model_name=model_id
            )
            systems["bitmex"][model_name] = bx

    return systems


def fetch_shared_data(
    date_str: str, systems: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    market_data: Dict[str, Any] = {"polymarket": {}, "stock": {}, "bitmex": {}}
    news_data: Dict[str, Any] = {"polymarket": {}, "stock": {}, "bitmex": {}}

    for market_type in ("polymarket", "stock", "bitmex"):
        sysmap = systems.get(market_type, {})
        if not sysmap:
            continue
        any_sys = next(iter(sysmap.values()))
        try:
            mkt = any_sys._fetch_market_data(date_str)
            market_data[market_type] = mkt
        except Exception as e:
            print(f"    ❌ {market_type} market fetch failed [{date_str}]: {e}")
            continue
        try:
            nws = any_sys._fetch_news_data(mkt, date_str)
            news_data[market_type] = nws
        except Exception as e:
            print(f"    ❌ {market_type} news fetch failed [{date_str}]: {e}")

    return market_data, news_data


def run_day(
    date_str: str, systems: Dict[str, Dict[str, Any]], parallelism: int
) -> Dict[str, str]:
    print(f"\n===== 📆 {date_str} =====")
    market_data, news_data = fetch_shared_data(date_str, systems)

    def _worker(market_type: str, agent_name: str, system: Any) -> Tuple[str, str, str]:
        mkt = market_data.get(market_type) or {}
        nws = news_data.get(market_type) or {}
        if not mkt:
            print(f"   • {market_type}/{agent_name}: skipped (no market data)")
            return market_type, agent_name, "skipped (no data)"
        try:
            allocations = system._generate_allocations(mkt, nws, date_str)
            system._update_accounts(allocations, mkt, date_str)
            system.cycle_count += 1
            print(f"   • {market_type}/{agent_name}: ✅ allocations applied")
            return market_type, agent_name, "ok"
        except Exception as e:
            print(f"   • {market_type}/{agent_name}: ❌ failed: {e}")
            return market_type, agent_name, f"failed: {e}"

    statuses: Dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, parallelism)) as ex:
        fut_map = {}
        for market_type, sysmap in systems.items():
            for agent_name, sysobj in sysmap.items():
                fut = ex.submit(_worker, market_type, agent_name, sysobj)
                fut_map[fut] = (market_type, agent_name)
        for fut in as_completed(fut_map):
            mt, an = fut_map[fut]
            try:
                _mt, _an, st = fut.result()
                statuses[f"{_mt}:{_an}"] = st
            except Exception as e:
                statuses[f"{mt}:{an}"] = f"failed: {e}"
    return statuses


def collect_results(
    systems: Dict[str, Dict[str, Any]], start_date: str, end_date: str
) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {"polymarket": {}, "stock": {}, "bitmex": {}}
    for market_type, sysmap in systems.items():
        for agent_name, system in sysmap.items():
            for acc_agent_name, account in system.accounts.items():
                init_cash = account.initial_cash
                final_val = account.get_total_value()
                ret_pct = (
                    ((final_val - init_cash) / init_cash * 100)
                    if init_cash > 0
                    else 0.0
                )
                out[market_type][acc_agent_name] = {
                    "initial_value": init_cash,
                    "final_value": final_val,
                    "return_percentage": ret_pct,
                    "period": f"{start_date} to {end_date}",
                }
    return out


def print_rankings(results: Dict[str, Dict[str, Any]], models: List[Tuple[str, str]], run_polymarket: bool = True, run_stock: bool = True, run_bitmex: bool = False):
    name_to_id = {n: mid for n, mid in models}

    market_types = []
    if run_stock:
        market_types.append("stock")
    if run_polymarket:
        market_types.append("polymarket")
    if run_bitmex:
        market_types.append("bitmex")

    for market_type in market_types:
        bucket = results.get(market_type, {})
        if not bucket:
            continue
        print(f"\n🎯 {market_type.upper()} RESULTS")
        print("-" * 40)
        ranked = sorted(
            bucket.items(),
            key=lambda x: x[1].get("return_percentage", 0.0),
            reverse=True,
        )
        for i, (agent, perf) in enumerate(ranked, 1):
            print(
                f"   #{i} {agent} ({name_to_id.get(agent, '?')}): "
                f"{perf['return_percentage']:+.2f}%  "
                f"(${perf['initial_value']:,.2f} → ${perf['final_value']:,.2f})"
            )

    all_rows = []
    for mkt in market_types:
        for agent, perf in results.get(mkt, {}).items():
            all_rows.append((mkt, agent, perf))
    if all_rows:
        best = max(all_rows, key=lambda x: x[2]["return_percentage"])
        bmkt, bagent, bperf = best
        print("\n🏅 OVERALL BEST")
        print("-" * 40)
        print(f"   Agent:  {bagent}")
        print(f"   Market: {bmkt}")
        print(f"   Return: {bperf['return_percentage']:+.2f}%")

    total = sum(len(results.get(k, {})) for k in results)
    print("\n📊 PERFORMANCE STATS")
    print("-" * 40)
    print(f"   Total Agents: {total}")
    if run_stock:
        print(f"   Stock Agents: {len(results.get('stock', {}))}")
    if run_polymarket:
        print(f"   Polymarket Agents: {len(results.get('polymarket', {}))}")
    if run_bitmex:
        print(f"   BitMEX Agents: {len(results.get('bitmex', {}))}")


def save_models_data(
    systems: Dict[str, Dict[str, Any]],
    out_path: str = "backend/models_data_init.json",
):
    all_models_data = []
    for market_type, sysmap in systems.items():
        for agent_name, system in sysmap.items():
            if not (hasattr(system, "accounts") and hasattr(system, "agents")):
                continue
            for acc_agent_name, account in system.accounts.items():
                if acc_agent_name not in system.agents:
                    continue
                agent = system.agents[acc_agent_name]
                model_data = _create_model_data(agent, account, market_type)
                all_models_data.append(_serialize_positions(model_data))
    with open(out_path, "w") as f:
        json.dump(all_models_data, f, indent=4)
    print(
        f"\n💾 Saved backtest data → {out_path}  ({len(all_models_data)} model entries)"
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for backtest configuration."""
    parser = argparse.ArgumentParser(
        description="Run backtests for trading models across multiple exchanges",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Time period
    parser.add_argument(
        "--start-date",
        type=str,
        default="2025-10-01",
        help="Backtest start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2025-11-01",
        help="Backtest end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--interval-days",
        type=int,
        default=1,
        help="Interval between trading days",
    )

    # Exchange selection
    parser.add_argument(
        "--exchanges",
        type=str,
        default="stock,polymarket,bitmex",
        help="Comma-separated list of exchanges to test (stock,polymarket,bitmex)",
    )

    # Asset counts (for auto-fetching trending assets)
    parser.add_argument(
        "--stock-count",
        type=int,
        default=15,
        help="Number of trending stocks to fetch",
    )
    parser.add_argument(
        "--polymarket-count",
        type=int,
        default=10,
        help="Number of Polymarket markets to fetch",
    )
    parser.add_argument(
        "--bitmex-count",
        type=int,
        default=12,
        help="Number of BitMEX contracts to fetch",
    )

    # Custom asset lists (override auto-fetching)
    parser.add_argument(
        "--stocks",
        type=str,
        default=None,
        help="Custom stock symbols (comma-separated, e.g., AAPL,TSLA,MSFT)",
    )
    parser.add_argument(
        "--bitmex-symbols",
        type=str,
        default=None,
        help="Custom BitMEX symbols (comma-separated, e.g., XBTUSDT,PEPEUSDT)",
    )

    # Initial cash
    parser.add_argument(
        "--initial-cash-stock",
        type=float,
        default=1000.0,
        help="Initial cash for stock trading",
    )
    parser.add_argument(
        "--initial-cash-polymarket",
        type=float,
        default=500.0,
        help="Initial cash for Polymarket trading",
    )
    parser.add_argument(
        "--initial-cash-bitmex",
        type=float,
        default=1000.0,
        help="Initial cash for BitMEX trading",
    )

    # Polymarket specific
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.2,
        help="Polymarket volume threshold filter",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    print("🔮 Parallel Backtest (Per-agent systems)")

    # Parse exchange selection
    exchanges = [x.strip().lower() for x in args.exchanges.split(",")]
    run_polymarket = "polymarket" in exchanges
    run_stock = "stock" in exchanges
    run_bitmex = "bitmex" in exchanges

    # Parse custom asset lists
    custom_stocks = [s.strip() for s in args.stocks.split(",")] if args.stocks else None
    custom_bitmex_symbols = (
        [s.strip() for s in args.bitmex_symbols.split(",")]
        if args.bitmex_symbols
        else None
    )

    cfg = get_backtest_config(args)
    all_models = get_base_model_configs()

    # Filter to GPT + Anthropic only
    models = [
        (name, model_id)
        for name, model_id in all_models
        if model_id.startswith("openai/") or model_id.startswith("anthropic/")
    ]

    print(f"⚡ Using {len(models)} models (GPT + Anthropic only)")
    print(f"   Filtered from {len(all_models)} total models")
    market_count = sum([run_polymarket, run_stock, run_bitmex])
    market_names = []
    if run_stock:
        market_names.append("stock")
    if run_polymarket:
        market_names.append("polymarket")
    if run_bitmex:
        market_names.append("bitmex")

    print(f"🤖 {len(models)} models × {market_count} markets ({', '.join(market_names)})")
    days = get_trading_days(cfg["start_date"], cfg["end_date"], cfg["interval_days"])
    print(f"📅 Trading days: {len(days)}  ({cfg['start_date']} → {cfg['end_date']})")
    print(f"⚙️  Parallelism: {cfg['parallelism']} (env LTB_PARALLELISM)")

    systems = build_systems(
        models, days, cfg["initial_cash"],
        run_polymarket=run_polymarket,
        run_stock=run_stock,
        run_bitmex=run_bitmex,
        threshold=cfg["threshold"],
        market_num=cfg["market_num"],
        stock_num=cfg["stock_num"],
        bitmex_num=cfg["bitmex_num"],
        custom_stocks=custom_stocks,
        custom_bitmex_symbols=custom_bitmex_symbols,
    )

    for i, d in enumerate(days, 1):
        date_str = d.strftime("%Y-%m-%d")
        print(f"\n=== Day {i}/{len(days)} ===")
        run_day(date_str, systems, cfg["parallelism"])

    results = collect_results(systems, cfg["start_date"], cfg["end_date"])
    print_rankings(results, models, run_polymarket=run_polymarket, run_stock=run_stock, run_bitmex=run_bitmex)
    save_models_data(systems)
    print("\n✅ Backtest complete.")


if __name__ == "__main__":
    main()
