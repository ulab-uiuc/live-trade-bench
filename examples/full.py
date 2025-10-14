#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lagged / Hold Rebalancing Analysis with Fixed Window, Missing-Price Policies,
Optional Excess Returns (via benchmark CSV), and Turnover/Cost Diagnostics.
"""
import argparse
import csv
import json
import math
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

os.environ.setdefault("MPLCONFIGDIR", str((Path("data") / "mpl-cache").resolve()))
from matplotlib import pyplot as plt  # noqa: E402

DEFAULT_MAX_LAG = 10
DEFAULT_SKIP_DAYS = 0
ANNUALIZATION_DAYS = 252
SUPPRESS_SKIP_MODELS = {"qqq-benchmark", "voo-benchmark"}
MISSING_POLICIES = {"keep", "renorm", "drop"}


def _timestamp_to_date(ts: Optional[str]) -> Optional[str]:
    if not ts:
        return None
    return ts[:10]


def _clean_float(value: str) -> Optional[float]:
    try:
        return float(value.replace(",", ""))
    except Exception:
        return None


def parse_stock_price(prompt: str, symbol: str) -> Optional[float]:
    pattern = re.compile(
        rf"^{re.escape(symbol)}:\s*Current price is \$?([\d.,]+)", re.MULTILINE
    )
    m = pattern.search(prompt)
    return _clean_float(m.group(1)) if m else None


def extract_question_map(snapshot: Dict) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for entry in snapshot.get("allocations_array", []):
        name = entry.get("name")
        question = entry.get("question")
        if name and question:
            mapping[name] = question.strip()
    return mapping


def parse_polymarket_price(prompt: str, question: str, outcome: str) -> Optional[float]:
    if not question:
        return None
    qpat = re.compile(
        rf"Question:\s*{re.escape(question)}\s*(.*?)(?=Question:|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    mm = qpat.search(prompt)
    if not mm:
        return None
    block = mm.group(1)
    opat = re.compile(
        rf"\s*-\s*Betting\s+{re.escape(outcome.upper())}\s+current price:\s*([0-9.]+)",
        re.IGNORECASE,
    )
    om = opat.search(block)
    return _clean_float(om.group(1)) if om else None


def build_price_cache(models: List[Dict]) -> Dict[Tuple[str, str], float]:
    cache: Dict[Tuple[str, str], float] = {}
    missing: Dict[str, List[str]] = defaultdict(list)
    for model in models:
        category = model.get("category", "")
        history = model.get("allocationHistory", [])
        for snap in history:
            date_str = _timestamp_to_date(snap.get("timestamp"))
            if not date_str:
                continue
            prompt = snap.get("llm_input", {}).get("prompt", "")
            if not prompt:
                continue
            allocations = snap.get("allocations", {})
            qmap = extract_question_map(snap) if category == "polymarket" else {}
            for sym in allocations.keys():
                if sym == "CASH":
                    cache[(sym, date_str)] = 1.0
                    continue
                price = None
                if category == "stock":
                    price = parse_stock_price(prompt, sym)
                elif category == "polymarket":
                    q = qmap.get(sym)
                    if (not q) and "_" in sym:
                        q = sym.rsplit("_", 1)[0].strip()
                    outcome = sym.rsplit("_", 1)[-1] if "_" in sym else ""
                    price = parse_polymarket_price(prompt, q or "", outcome)
                if price is not None:
                    cache[(sym, date_str)] = price
                else:
                    missing[sym].append(date_str)
    if missing:
        print("Warning: Missing prices parsed from prompts (sample):")
        for idx, (sym, dates) in enumerate(missing.items()):
            if idx >= 10:
                print("  ...")
                break
            preview = ", ".join(sorted(set(dates))[:5])
            suffix = " ..." if len(set(dates)) > 5 else ""
            print(f"  - {sym}: {preview}{suffix}")
    return cache


def get_asset_price(
    cache: Dict[Tuple[str, str], float], symbol: str, date: str
) -> Optional[float]:
    return cache.get((symbol, date))


def load_benchmark_csv(path: Optional[str]) -> Dict[str, float]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        print(f"[Benchmark] CSV not found: {path}")
        return {}
    out: Dict[str, float] = {}
    with p.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = str(row.get("Date") or row.get("date") or "").strip()[:10]
            close = row.get("Close") or row.get("Adj Close") or row.get("close")
            if not date or close is None:
                continue
            try:
                out[date] = float(close)
            except Exception:
                continue
    if not out:
        print(f"[Benchmark] CSV read but no usable rows: {path}")
    return out


def make_benchmark_returns(close_map: Dict[str, float]) -> Dict[str, float]:
    if not close_map:
        return {}
    dates = sorted(close_map.keys())
    r: Dict[str, float] = {}
    for i in range(1, len(dates)):
        d, prev = dates[i], dates[i - 1]
        c, p = close_map[d], close_map[prev]
        if p and p != 0:
            r[d] = (c - p) / p
    return r


@dataclass
class DayCalc:
    ret: Optional[float]
    sum_w_priced: float
    turnover: float


def _one_day_lagged_return(
    history_sorted: List[Dict],
    price_cache: Dict[Tuple[str, str], float],
    idx: int,
    lag_days: int,
    rf_daily: float,
    missing_policy: str,
    bench_ret: Optional[float],
    prev_alloc_idx_for_turnover: Optional[int],
) -> DayCalc:
    curr = history_sorted[idx]
    prev = history_sorted[idx - 1]
    alloc_idx = idx - 1 - lag_days
    if alloc_idx < 0:
        return DayCalc(None, 0.0, 0.0)
    alloc_snap = history_sorted[alloc_idx]
    curr_date = _timestamp_to_date(curr.get("timestamp"))
    prev_date = _timestamp_to_date(prev.get("timestamp"))
    if not curr_date or not prev_date:
        return DayCalc(None, 0.0, 0.0)

    allocations = alloc_snap.get("allocations", {})
    num = 0.0
    denom = 0.0

    cash_w = allocations.get("CASH", 0.0) or 0.0
    if cash_w != 0:
        num += cash_w * rf_daily
        denom += cash_w

    priced_num = 0.0
    priced_denom = 0.0
    for sym, w in allocations.items():
        if sym == "CASH" or w is None:
            continue
        w = float(w)
        curr_p = get_asset_price(price_cache, sym, curr_date)
        prev_p = get_asset_price(price_cache, sym, prev_date)
        if curr_p is not None and prev_p is not None and prev_p != 0:
            r = (curr_p - prev_p) / prev_p
            priced_num += w * r
            priced_denom += w
        else:
            if missing_policy == "keep":
                denom += w
            elif missing_policy == "drop":
                pass
            elif missing_policy == "renorm":
                pass

    if missing_policy in ("keep", "drop"):
        num += priced_num
        denom += priced_denom
    elif missing_policy == "renorm":
        if priced_denom + cash_w > 0:
            num = priced_num + cash_w * rf_daily
            denom = priced_denom + cash_w
        else:
            return DayCalc(None, 0.0, 0.0)

    if denom <= 0:
        return DayCalc(None, 0.0, 0.0)

    day_ret = num / denom
    if bench_ret is not None:
        day_ret = day_ret - bench_ret

    turnover = 0.0
    if (
        prev_alloc_idx_for_turnover is not None
        and 0 <= prev_alloc_idx_for_turnover < len(history_sorted)
    ):
        prev_alloc_snap = history_sorted[prev_alloc_idx_for_turnover]
        prev_alloc = prev_alloc_snap.get("allocations", {})
        syms = set(list(prev_alloc.keys()) + list(allocations.keys()))
        l1 = 0.0
        for s in syms:
            w0 = float(prev_alloc.get(s, 0.0) or 0.0)
            w1 = float(allocations.get(s, 0.0) or 0.0)
            l1 += abs(w1 - w0)
        turnover = 0.5 * l1

    return DayCalc(day_ret, denom, turnover)


def compute_lagged_returns(
    history: List[Dict],
    price_cache: Dict[Tuple[str, str], float],
    lag_days: int,
    start_idx: int,
    rf_daily: float,
    missing_policy: str,
    bench_rets: Dict[str, float],
) -> Tuple[List[float], List[float]]:
    if len(history) < 2:
        return [], []
    hist = sorted(history, key=lambda x: x.get("timestamp") or "")
    rets: List[float] = []
    turns: List[float] = []
    for idx in range(start_idx, len(hist)):
        curr_date = _timestamp_to_date(hist[idx].get("timestamp"))
        bench_r = bench_rets.get(curr_date) if bench_rets else None
        prev_ref = (idx - 2 - lag_days) if (idx - 2 - lag_days) >= 0 else None
        dc = _one_day_lagged_return(
            hist,
            price_cache,
            idx,
            lag_days,
            rf_daily,
            missing_policy,
            bench_r,
            prev_ref,
        )
        if dc.ret is not None:
            rets.append(dc.ret)
            turns.append(dc.turnover)
    return rets, turns


def compute_hold_returns(
    history: List[Dict],
    price_cache: Dict[Tuple[str, str], float],
    hold_days: int,
    start_idx: int,
    rf_daily: float,
    missing_policy: str,
    bench_rets: Dict[str, float],
) -> Tuple[List[float], List[float]]:
    if len(history) < 2:
        return [], []
    hist = sorted(history, key=lambda x: x.get("timestamp") or "")
    rets: List[float] = []
    turns: List[float] = []
    last_weight_idx = None
    for idx in range(start_idx, len(hist)):
        curr_date = _timestamp_to_date(hist[idx].get("timestamp"))
        prev_idx = idx - 1
        day_no = idx - start_idx
        if (day_no == 0) or (day_no % hold_days == 0):
            last_weight_idx = prev_idx
        if last_weight_idx is None:
            last_weight_idx = prev_idx
        lag_days = prev_idx - last_weight_idx
        bench_r = bench_rets.get(curr_date) if bench_rets else None
        prev_ref = (idx - 2 - lag_days) if (idx - 2 - lag_days) >= 0 else None
        dc = _one_day_lagged_return(
            hist,
            price_cache,
            idx,
            lag_days,
            rf_daily,
            missing_policy,
            bench_r,
            prev_ref,
        )
        if dc.ret is not None:
            rets.append(dc.ret)
            turns.append(dc.turnover)
    return rets, turns


def calc_metrics(
    values: List[float], turns: List[float], tc_bps: float
) -> Dict[str, float]:
    if not values:
        return {
            "mean_return": math.nan,
            "std_return": math.nan,
            "sharpe": math.nan,
            "annualized_return": math.nan,
            "turnover": math.nan,
            "cost": math.nan,
            "samples": 0,
        }
    v = np.array(values, dtype=float)
    t = np.array(turns, dtype=float) if turns else np.zeros_like(v)
    cost = (tc_bps / 10000.0) * t
    net = v - cost
    mean = float(np.mean(net))
    std = float(np.std(net, ddof=1)) if len(net) > 1 else 0.0
    sharpe = (mean / std) * math.sqrt(ANNUALIZATION_DAYS) if std > 0 else math.nan
    if np.any(net <= -1.0):
        ann = math.nan
    else:
        cumulative = float(np.prod(1.0 + net))
        try:
            ann = cumulative ** (ANNUALIZATION_DAYS / len(net)) - 1.0
        except Exception:
            ann = math.nan
    return {
        "mean_return": mean,
        "std_return": std,
        "sharpe": sharpe,
        "annualized_return": ann,
        "turnover": float(np.mean(t)) if len(t) > 0 else math.nan,
        "cost": float(np.mean(cost)) if len(cost) > 0 else 0.0,
        "samples": int(len(net)),
    }


def common_start_index(history_len: int, max_k: int, skip_initial_days: int) -> int:
    return 1 + skip_initial_days + max_k


def plot_metric_across_models(
    results: List[Dict], metric_key: str, output_path: Path, *, title: str, ylabel: str
) -> None:
    valid = []
    for res in results:
        if "error" in res:
            continue
        values = [v.get(metric_key) for v in res["metrics"].values()]
        if not values or all((isinstance(x, float) and math.isnan(x)) for x in values):
            continue
        valid.append(res)
    if not valid:
        print(f"No valid data to plot for {metric_key}")
        return

    fig, ax = plt.subplots(figsize=(14, 6))
    color_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])

    # 收集所有模型的 k，用于设定紧凑的 x 轴范围
    all_lags = []
    for res in valid:
        all_lags.extend(sorted(res["metrics"].keys()))
    if all_lags:
        xmin = float(min(all_lags))
        xmax = float(max(all_lags))
    else:
        xmin, xmax = 0.0, 1.0

    for i, res in enumerate(valid):
        metric_map = res["metrics"]
        lags = sorted(metric_map.keys())
        series = [metric_map[lag].get(metric_key, math.nan) for lag in lags]
        name = res.get("model_name") or res.get("model_id") or "unknown"
        color = color_cycle[i % max(1, len(color_cycle))] if color_cycle else None
        ax.plot(
            lags,
            series,
            marker="o",
            markersize=2,
            linewidth=1.0,
            alpha=0.8,
            color=color,
            label=name,
        )

    ax.set_xlabel("k")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.3, linestyle="--")

    # -------- 关键：收紧右侧空白 --------
    # 1) 关闭 x 方向的自动留白，并设置非常轻的 padding
    ax.margins(x=0.0)
    # 2) 明确设置 xlim，左右各留很小的 0.2 边距（可按需调成 0.1~0.3）
    ax.set_xlim(xmin - 0.2, xmax + 0.2)

    # 图例：如果模型很多，放在图外；否则放在图内减少右侧留白
    if len(valid) > 12:
        # 放在图外，但把为图例预留的右侧画布从 20% 缩到 8%（原来是 0.8）
        ax.legend(
            loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=8
        )
        fig.tight_layout(rect=[0.0, 0.0, 0.92, 0.97])  # 原来是 0.8，这里调到 0.92 更紧凑
    else:
        # 放在图内，进一步减少整体空白
        ax.legend(loc="upper left", frameon=False, fontsize=8, ncol=1)
        fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved plot: {output_path}")


def plot_top5_mean_return(
    results: List[Dict], output_path: Path, *, title: str
) -> None:
    """
    Plot mean return rate with top 5 models highlighted and others in gray.
    Also shows the average curve of all models.
    """
    valid = []
    for res in results:
        if "error" in res:
            continue
        values = [v.get("mean_return") for v in res["metrics"].values()]
        if not values or all((isinstance(x, float) and math.isnan(x)) for x in values):
            continue
        valid.append(res)

    if not valid:
        print("No valid data to plot for top5_mean_rr")
        return

    # Identify top 5 models based on mean_return at k=0
    model_scores = []
    for res in valid:
        k0_metric = res["metrics"].get(0, {})
        mean_ret_k0 = k0_metric.get("mean_return", math.nan)
        if not math.isnan(mean_ret_k0):
            model_scores.append((res, mean_ret_k0))

    # Sort by k=0 mean return (descending)
    model_scores.sort(key=lambda x: x[1], reverse=True)
    top5_models = set(id(res) for res, _ in model_scores[:5])

    fig, ax = plt.subplots(figsize=(14, 6))
    color_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])

    # Collect all k values
    all_lags = []
    for res in valid:
        all_lags.extend(sorted(res["metrics"].keys()))
    if all_lags:
        xmin = float(min(all_lags))
        xmax = float(max(all_lags))
    else:
        xmin, xmax = 0.0, 1.0

    # Collect data for mean curve calculation
    mean_data = defaultdict(list)

    # Plot individual models
    color_idx = 0
    for res in valid:
        metric_map = res["metrics"]
        lags = sorted(metric_map.keys())
        series = [metric_map[lag].get("mean_return", math.nan) for lag in lags]
        name = res.get("model_name") or res.get("model_id") or "unknown"

        # Collect data for mean curve
        for k, val in zip(lags, series):
            if not math.isnan(val):
                mean_data[k].append(val)

        is_top5 = id(res) in top5_models

        if is_top5:
            color = (
                color_cycle[color_idx % max(1, len(color_cycle))]
                if color_cycle
                else None
            )
            color_idx += 1
            ax.plot(
                lags,
                series,
                marker="o",
                markersize=2,
                linewidth=1.0,
                alpha=0.8,
                color=color,
                label=name,
            )
        else:
            # Gray for non-top5
            ax.plot(
                lags,
                series,
                marker="o",
                markersize=1,
                linewidth=0.5,
                alpha=0.3,
                color="gray",
            )

    # Plot mean curve
    if mean_data:
        mean_lags = sorted(mean_data.keys())
        mean_series = [float(np.mean(mean_data[k])) for k in mean_lags]
        ax.plot(
            mean_lags,
            mean_series,
            linestyle="--",
            linewidth=2.0,
            color="black",
            label="All Models Mean",
            alpha=0.7,
        )

    ax.set_xlabel("k")
    ax.set_ylabel("Mean Daily Return")
    ax.set_title(title)
    ax.grid(alpha=0.3, linestyle="--")
    ax.margins(x=0.0)
    ax.set_xlim(xmin - 0.2, xmax + 0.2)

    # Legend
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=8)
    fig.tight_layout(rect=[0.0, 0.0, 0.92, 0.97])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved plot: {output_path}")


def save_metrics_json(results: List[Dict], output_path: Path) -> None:
    serializable = []
    for res in results:
        if "metrics" in res:
            metrics = {
                str(k): v for k, v in sorted(res["metrics"].items(), key=lambda x: x[0])
            }
            serializable.append(
                {
                    "model_id": res.get("model_id"),
                    "model_name": res.get("model_name"),
                    "category": res.get("category"),
                    "metrics": metrics,
                }
            )
        else:
            serializable.append(res)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(serializable, f, indent=2)
    print(f"Saved metrics data: {output_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lagged/Hold Rebalancing Analysis")
    p.add_argument(
        "--data",
        default="../backend/models_data_1009_refreshed.json",
        help="Path to models JSON.",
    )
    p.add_argument(
        "--output-dir", default="../data/lastest", help="Directory for outputs."
    )
    p.add_argument(
        "--max-lag",
        type=int,
        default=DEFAULT_MAX_LAG,
        help="Max k (lag days for lagged; hold_days = k+1 for hold-mode).",
    )
    p.add_argument(
        "--skip-initial-days",
        type=int,
        default=DEFAULT_SKIP_DAYS,
        help="Skip N initial days before analysis window.",
    )
    p.add_argument(
        "--rf-annual",
        type=float,
        default=0.04,
        help="Annual risk-free rate for CASH, e.g., 0.04 for 4%%.",
    )
    p.add_argument(
        "--tc-bps",
        type=float,
        default=0.0,
        help="Transaction cost in bps per unit turnover.",
    )
    p.add_argument(
        "--mode", choices=["lagged", "hold"], default="lagged", help="Rebalance mode."
    )
    p.add_argument(
        "--missing-policy",
        choices=list(MISSING_POLICIES),
        default="renorm",
        help="Missing price handling policy.",
    )
    p.add_argument(
        "--use-excess",
        action="store_true",
        default=True,
        help="Compute excess returns vs benchmark.",
    )
    p.add_argument(
        "--benchmark-csv",
        type=str,
        default="QQQ.csv",
        help="CSV file with columns Date,Close for benchmark.",
    )
    return p.parse_args()


def _fmt(x: Optional[float]) -> str:
    return (
        f"{x:.4f}"
        if (x is not None and not (isinstance(x, float) and math.isnan(x)))
        else "nan"
    )


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with data_path.open() as f:
        models = [m for m in json.load(f) if m.get("id") not in SUPPRESS_SKIP_MODELS]
    print(f"Loaded {len(models)} models from {data_path}")

    price_cache = build_price_cache(models)
    print(f"Collected {len(price_cache)} price entries")

    bench_close = load_benchmark_csv(args.benchmark_csv) if args.use_excess else {}
    bench_rets = make_benchmark_returns(bench_close) if bench_close else {}

    rf_daily = float(args.rf_annual) / ANNUALIZATION_DAYS

    results: List[Dict] = []
    for model in models:
        hist = model.get("allocationHistory", [])
        if len(hist) < 2:
            results.append(
                {
                    "model_id": model.get("id"),
                    "model_name": model.get("name"),
                    "category": model.get("category"),
                    "error": "Insufficient allocation history",
                }
            )
            continue

        hist_sorted = sorted(hist, key=lambda x: x.get("timestamp") or "")
        hist_len = len(hist_sorted)

        if args.mode == "lagged":
            feasible_max = max(0, min(args.max_lag, hist_len - 2))
            start_idx = 1 + args.skip_initial_days + feasible_max
        else:
            feasible_max = args.max_lag
            start_idx = 1 + args.skip_initial_days

        metrics_by_k: Dict[int, Dict[str, float]] = {}

        for k in range(0, feasible_max + 1):
            if args.mode == "lagged":
                rets, turns = compute_lagged_returns(
                    hist_sorted,
                    price_cache,
                    k,
                    start_idx,
                    rf_daily,
                    args.missing_policy,
                    bench_rets,
                )
            else:
                hold_days = max(1, k + 1)
                rets, turns = compute_hold_returns(
                    hist_sorted,
                    price_cache,
                    hold_days,
                    start_idx,
                    rf_daily,
                    args.missing_policy,
                    bench_rets,
                )
            m = calc_metrics(rets, turns, args.tc_bps)
            metrics_by_k[k] = m

        res = {
            "model_id": model.get("id"),
            "model_name": model.get("name"),
            "category": model.get("category"),
            "metrics": metrics_by_k,
        }
        results.append(res)

        name = model.get("name", model.get("id", "Unknown"))
        ks = sorted(metrics_by_k.keys())
        k0 = ks[0] if ks else 0
        kL = ks[-1] if ks else args.max_lag
        m0 = metrics_by_k.get(k0, {})
        mL = metrics_by_k.get(kL, {})
        print(
            f"[{name}] k={k0} Sharpe={_fmt(m0.get('sharpe'))}, Mean={_fmt(m0.get('mean_return'))}, Vol={_fmt(m0.get('std_return'))} "
            f"| k={kL} Sharpe={_fmt(mL.get('sharpe'))}, Mean={_fmt(mL.get('mean_return'))}, Vol={_fmt(mL.get('std_return'))}, "
            f"Turn={_fmt(mL.get('turnover'))}, Cost={_fmt(mL.get('cost'))}, samples={mL.get('samples', 0)}"
        )

    agg = defaultdict(
        lambda: {
            "sharpe": defaultdict(list),
            "mean": defaultdict(list),
            "vol": defaultdict(list),
            "turn": defaultdict(list),
            "cost": defaultdict(list),
        }
    )

    for res in results:
        if "metrics" not in res:
            continue
        cat = res.get("category", "unknown")
        for k, m in res["metrics"].items():
            if not math.isnan(m.get("sharpe", math.nan)):
                agg[cat]["sharpe"][int(k)].append(m["sharpe"])
            if not math.isnan(m.get("mean_return", math.nan)):
                agg[cat]["mean"][int(k)].append(m["mean_return"])
            if not math.isnan(m.get("std_return", math.nan)):
                agg[cat]["vol"][int(k)].append(m["std_return"])
            if not math.isnan(m.get("turnover", math.nan)):
                agg[cat]["turn"][int(k)].append(m["turnover"])
            if not math.isnan(m.get("cost", math.nan)):
                agg[cat]["cost"][int(k)].append(m["cost"])

    for cat in sorted(agg.keys()):
        S = agg[cat]["sharpe"]
        R = agg[cat]["mean"]
        V = agg[cat]["vol"]
        Tn = agg[cat]["turn"]
        C = agg[cat]["cost"]
        keys = sorted(set(S.keys()) | set(R.keys()) | set(V.keys()))
        print(
            f"\n===== Mean across {cat} models (mode={args.mode}, missing={args.missing_policy}, excess={'yes' if args.use_excess else 'no'}) ====="
        )
        print("k | Sharpe | MeanRet | Vol | Turnover | Cost")
        for k in keys:
            s = float(np.mean(S[k])) if k in S else math.nan
            r = float(np.mean(R[k])) if k in R else math.nan
            v = float(np.mean(V[k])) if k in V else math.nan
            tn = float(np.mean(Tn[k])) if k in Tn else math.nan
            c = float(np.mean(C[k])) if k in C else math.nan
            print(f"{k:2d} | {s:7.4f} | {r: .6f} | {v: .6f} | {tn: .4f} | {c: .6f}")

    metrics_path = (
        out_dir
        / f"metrics_{args.mode}_{args.missing_policy}{'_excess' if args.use_excess else ''}.json"
    )
    save_metrics_json(results, metrics_path)

    by_cat = defaultdict(list)
    for r in results:
        by_cat[r.get("category", "unknown")].append(r)

    for cat, group in by_cat.items():
        base = f"{args.mode}_{args.missing_policy}{'_excess' if args.use_excess else ''}_{cat}"
        plot_metric_across_models(
            group,
            "sharpe",
            out_dir / f"{base}_sharpe.pdf",
            title=f"Sharpe vs k ({cat})",
            ylabel="Sharpe",
        )
        plot_metric_across_models(
            group,
            "mean_return",
            out_dir / f"{base}_mean.pdf",
            title=f"Average Daily Return vs k ({cat})",
            ylabel="Mean Daily Return",
        )
        plot_metric_across_models(
            group,
            "std_return",
            out_dir / f"{base}_vol.pdf",
            title=f"Volatility vs k ({cat})",
            ylabel="Daily Volatility",
        )
        plot_metric_across_models(
            group,
            "turnover",
            out_dir / f"{base}_turnover.pdf",
            title=f"Turnover vs k ({cat})",
            ylabel="Turnover (0.5*L1)",
        )
        plot_top5_mean_return(
            group,
            out_dir / f"{base}_top5_mean_rr.pdf",
            title=f"Top 5 Mean Return vs k ({cat})",
        )

    print("Analysis complete.")


if __name__ == "__main__":
    main()
