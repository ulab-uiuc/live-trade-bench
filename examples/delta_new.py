#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Window-Delta (Rolling k-Hold) engine + self-contained price preparation.

This module implements the fixed-window rolling comparison used in the slides:

Definitions (for a window anchored at t of length H):
  - Asset daily return: r_{i,u+1} = P_{i,u+1}/P_{i,u} - 1
  - Portfolio daily return using weights w over (u -> u+1):
      r_port(u; w) = [sum_{i∈S_u} w_i r_{i,u+1} + w_cash·rf] / [sum_{i∈S_u} w_i + w_cash]
    where S_u are assets with both prices available on u and u+1.
  - Daily-update (k=1) cumulative over the window:
      R_t→t+H^(1) = Π_{u=t}^{t+H-1} (1 + r_port(u; W_u)) - 1
  - k-hold (weights rebalance only at t, t+k, t+2k, ...):
      let s(u; t,k) = t + floor((u-t)/k)·k,
      R_t→t+H^(k) = Π_{u=t}^{t+H-1} (1 + r_port(u; W_{s(u; t,k)})) - 1
  - Window delta: Δ_t^(k) = R_t→t+H^(1) − R_t→t+H^(k)

We aggregate across all valid anchors t: mean / median / winrate.

Inputs expected by this module follow the repository's model snapshots:
  history: List[Dict] with fields:
    - 'timestamp' (ISO string)
    - 'allocations' (symbol -> weight), with optional 'CASH'
  price_cache: Dict[(symbol, date_str)] -> price (float), where date_str is 'YYYY-MM-DD'

This module is standalone (no network). Price preparation and optional fetching
is handled elsewhere (see examples/new_k.py). The engine honours the same
missing-price policy and coverage threshold as the script.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict as _dd
from dataclasses import dataclass
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib import rcParams
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
OUT_DIR = ROOT / "data" / "neww"

# Policy and thresholds should match examples/new_k.py
COVERAGE_MIN = 0.3
MISSING_POLICY_DEFAULT = "keep"

# Fetch toggles (copied from new_k.py)
TRY_FETCH_MISSING = True
FETCH_LIMIT = 1000
PREFETCH_ALL = True
USE_EOD_FIRST = True
USE_STOCK_EOD_FIRST = True
PREFETCH_STOCK = True

# Window-Delta defaults
K_SET_DEFAULT = [1, 2, 4, 8, 16]
WINDOW_H = 10
TC_BPS = 0.0

# Match seaborn styling used by visualize_metrics.py
sns.set_theme(style="white")


def _timestamp_to_date(ts: Optional[str]) -> Optional[str]:
    if not ts:
        return None
    return ts[:10]


def _find_models_path() -> Path:
    preferred = [
        BACKEND / "models_data_1013_refreshed.json",
        BACKEND / "models_data.json",
    ]
    for p in preferred:
        if p.exists():
            return p
    candidates = [Path(p) for p in glob(str(BACKEND / "models_data_*.json"))]
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    raise FileNotFoundError("No models_data JSON found under backend/")


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
    for entry in snapshot.get("allocations_array", []) or []:
        name = entry.get("name")
        question = entry.get("question")
        if name and question:
            mapping[name] = str(question).strip()
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


def get_asset_price(
    cache: Dict[Tuple[str, str], float], symbol: str, date: str
) -> Optional[float]:
    return cache.get((symbol, date))


@dataclass
class DayCalc:
    ret: Optional[float]
    priced_non_cash: float
    total_non_cash: float


def one_day_return_with_alloc_idx(
    history_sorted: List[Dict],
    price_cache: Dict[Tuple[str, str], float],
    curr_idx: int,
    alloc_idx: int,
    rf_daily: float,
    missing_policy: str,
) -> DayCalc:
    """Compute portfolio return over (u -> u+1) using weights from alloc_idx.

    - curr_idx = u (must satisfy 0 <= u < len(hist)-1)
    - alloc_idx supplies the weights snapshot (e.g., u for daily-update, or
      t + floor((u-t)/k)*k for k-hold inside a window anchored at t).
    Coverage handling mirrors the immediate-mode logic from examples/new_k.py.
    """
    if curr_idx < 0 or curr_idx + 1 >= len(history_sorted) or alloc_idx < 0:
        return DayCalc(None, 0.0, 0.0)

    curr = history_sorted[curr_idx]
    nxt = history_sorted[curr_idx + 1]
    alloc_snap = history_sorted[alloc_idx]

    curr_date = _timestamp_to_date(curr.get("timestamp"))
    next_date = _timestamp_to_date(nxt.get("timestamp"))
    if not curr_date or not next_date:
        return DayCalc(None, 0.0, 0.0)

    allocations = alloc_snap.get("allocations", {}) or {}
    num = 0.0
    denom = 0.0

    cash_w = float(allocations.get("CASH", 0.0) or 0.0)
    if cash_w != 0.0:
        num += cash_w * rf_daily
        denom += cash_w

    priced_num = 0.0
    priced_denom = 0.0
    total_non_cash = 0.0
    for sym, w in allocations.items():
        if sym == "CASH" or w is None:
            continue
        w = float(w)
        total_non_cash += w
        p0 = get_asset_price(price_cache, sym, curr_date)
        p1 = get_asset_price(price_cache, sym, next_date)
        if p0 is not None and p1 is not None and p0 != 0:
            r = (p1 - p0) / p0
            priced_num += w * r
            priced_denom += w
        else:
            if missing_policy == "keep":
                denom += w
            elif missing_policy in ("drop", "renorm"):
                pass

    if missing_policy in ("keep", "drop"):
        num += priced_num
        denom += priced_denom
    elif missing_policy == "renorm":
        if priced_denom + cash_w > 0:
            num = priced_num + cash_w * rf_daily
            denom = priced_denom + cash_w
        else:
            return DayCalc(None, priced_denom, total_non_cash)

    if denom <= 0:
        return DayCalc(None, priced_denom, total_non_cash)

    day_ret = num / denom
    return DayCalc(day_ret, priced_denom, total_non_cash)


def compute_window_delta_metrics(
    history: List[Dict],
    price_cache: Dict[Tuple[str, str], float],
    k_values: List[int],
    window_h: int,
    *,
    rf_daily: float = 0.0,
    missing_policy: str = MISSING_POLICY_DEFAULT,
    tc_bps: float = 0.0,
) -> Dict[int, Dict[str, float]]:
    """Fixed-window rolling comparison statistics.

    Returns: {k: {mean, median, winrate, samples}}
    Cost (optional): daily cost applied only on rebalance days, with per-day
    rate tc_bps (basis points). For simplicity, we do not compute turnovers in
    this module; when tc_bps>0, we approximate as follows:
      - Daily-update path: rebalances every day, so we subtract a flat cost each
        day: cost1 = tc_bps/10000.
      - k-hold path: rebalances only when crossing block boundaries u in
        {t, t+k, t+2k, ...}, so cost2 is subtracted only at those steps.
    If you need exact L1 turnover-based cost, prefer the implementation inside
    examples/new_k.py which has access to full weight snapshots.
    """
    if len(history) < 2:
        return {
            int(k): {
                "mean": math.nan,
                "median": math.nan,
                "winrate": math.nan,
                "samples": 0,
            }
            for k in k_values
        }

    hist = sorted(history, key=lambda x: x.get("timestamp") or "")
    last_start = len(hist) - 1 - int(window_h)
    if last_start < 0:
        return {
            int(k): {
                "mean": math.nan,
                "median": math.nan,
                "winrate": math.nan,
                "samples": 0,
            }
            for k in k_values
        }

    out: Dict[int, Dict[str, float]] = {}
    for k in k_values:
        kk = max(1, int(k))
        deltas: List[float] = []
        for t in range(0, last_start + 1):
            prod_daily = 1.0
            prod_hold = 1.0
            valid_days = 0
            for u in range(t, t + window_h):
                # daily-update: weights from u
                dc1 = one_day_return_with_alloc_idx(
                    hist, price_cache, u, u, rf_daily, missing_policy
                )
                # k-hold: weights from block start
                hold_idx = t + ((u - t) // kk) * kk
                dc2 = one_day_return_with_alloc_idx(
                    hist, price_cache, u, hold_idx, rf_daily, missing_policy
                )

                cov1 = (
                    1.0
                    if dc1.total_non_cash == 0.0
                    else (dc1.priced_non_cash / dc1.total_non_cash)
                )
                cov2 = (
                    1.0
                    if dc2.total_non_cash == 0.0
                    else (dc2.priced_non_cash / dc2.total_non_cash)
                )
                if not (
                    dc1.ret is not None
                    and (dc1.total_non_cash == 0.0 or cov1 >= COVERAGE_MIN)
                    and dc2.ret is not None
                    and (dc2.total_non_cash == 0.0 or cov2 >= COVERAGE_MIN)
                ):
                    continue

                r1 = dc1.ret or 0.0
                r2 = dc2.ret or 0.0

                # Approximate per-day costs (optional)
                if tc_bps > 0.0:
                    r1 -= tc_bps / 10000.0
                    step_start = t + ((u - t) // kk) * kk
                    next_step_start = t + (((u + 1) - t) // kk) * kk
                    if next_step_start != step_start:  # a rebalance at block boundary
                        r2 -= tc_bps / 10000.0

                prod_daily *= 1.0 + r1
                prod_hold *= 1.0 + r2
                valid_days += 1

            if valid_days > 0:
                R1 = prod_daily - 1.0
                Rk = prod_hold - 1.0
                deltas.append(R1 - Rk)

        if deltas:
            arr = np.array(deltas, dtype=float)
            out[int(k)] = {
                "mean": float(np.mean(arr)),
                "median": float(np.median(arr)),
                "winrate": float(np.mean(arr > 0)),
                "samples": int(arr.size),
                "q25": float(np.percentile(arr, 25)),
                "q75": float(np.percentile(arr, 75)),
                "std": float(np.std(arr, ddof=0)),
            }
        else:
            out[int(k)] = {
                "mean": math.nan,
                "median": math.nan,
                "winrate": math.nan,
                "samples": 0,
                "q25": math.nan,
                "q75": math.nan,
                "std": math.nan,
            }

    return out


def _collect_date_range(models: List[Dict]) -> Tuple[Optional[str], Optional[str]]:
    dates: List[str] = []
    for m in models:
        for snap in m.get("allocationHistory", []) or []:
            ts = (snap.get("timestamp") or "")[:10]
            if ts:
                dates.append(ts)
    if not dates:
        return None, None
    return min(dates), max(dates)


def _gather_stock_tickers(models: List[Dict]) -> List[str]:
    tickers: set[str] = set()
    for m in models:
        if m.get("category") != "stock":
            continue
        for snap in m.get("allocationHistory", []) or []:
            for sym in (snap.get("allocations", {}) or {}).keys():
                if sym and sym != "CASH":
                    tickers.add(str(sym))
    return sorted(tickers)


def _prefetch_stock_prices(
    models: List[Dict], stock_price_memo: Dict[Tuple[str, str], Optional[float]]
) -> Tuple[List[str], int]:
    try:
        from live_trade_bench.fetchers.stock_fetcher import StockFetcher

        start, end = _collect_date_range(models)
        if not start or not end:
            return ([], 0)
        tickers = _gather_stock_tickers(models)
        if not tickers:
            return ([], 0)
        fetcher = StockFetcher(min_delay=0.2, max_delay=0.5)
        filled = 0
        for tkr in tickers:
            try:
                df = fetcher._download_price_data(tkr, start, end, interval="1d")  # type: ignore[attr-defined]
            except Exception:
                df = None
            if df is None or df is False:
                continue
            try:
                cols = list(df.columns)
                close_col = "Close"
                for c in ("Close", "Adj Close", "close", "adjclose"):
                    if c in cols:
                        close_col = c
                        break
                for idx, row in df.iterrows():
                    d = idx.strftime("%Y-%m-%d")
                    try:
                        val = row[close_col]
                        p = float(val.iloc[0]) if hasattr(val, "iloc") else float(val)
                    except Exception:
                        continue
                    if d and (tkr, d) not in stock_price_memo:
                        stock_price_memo[(tkr, d)] = p
                        filled += 1
            except Exception:
                continue
        return (tickers, filled)
    except Exception as e:
        print(f"[stock_prefetch] failed: {e}")
        return ([], 0)


def _build_question_token_map(models: List[Dict]) -> Dict[str, Dict[str, str]]:
    if not TRY_FETCH_MISSING:
        return {}
    try:
        from live_trade_bench.fetchers.polymarket_fetcher import PolymarketFetcher

        start, end = _collect_date_range(models)
        if not start or not end:
            return {}
        params = {
            "start_date_max": f"{end}T23:59:59Z",
            "end_date_min": f"{start}T00:00:00Z",
            "limit": max(FETCH_LIMIT, 1000),
        }
        fetcher = PolymarketFetcher(min_delay=0.1, max_delay=0.2)
        markets = fetcher._fetch_markets(params)  # type: ignore[attr-defined]
        qmap: Dict[str, Dict[str, str]] = {}
        for m in markets:
            if not isinstance(m, dict) or not m.get("id"):
                continue
            q = (m.get("question") or "").strip()
            raw_token_ids = m.get("clobTokenIds", [])
            raw_outcomes = m.get("outcomes", [])
            if isinstance(raw_token_ids, str):
                try:
                    import json as _json

                    token_ids = _json.loads(raw_token_ids)
                except Exception:
                    token_ids = []
            else:
                token_ids = raw_token_ids
            if isinstance(raw_outcomes, str):
                try:
                    import json as _json

                    outcomes = _json.loads(raw_outcomes)
                except Exception:
                    outcomes = []
            else:
                outcomes = raw_outcomes
            if (
                q
                and isinstance(outcomes, list)
                and isinstance(token_ids, list)
                and len(outcomes) == len(token_ids)
            ):
                mp = {}
                for o, t in zip(outcomes, token_ids):
                    if o and t:
                        mp[str(o).capitalize()] = str(t)
                if mp:
                    qmap[q] = mp
        return qmap
    except Exception as e:
        print(f"[fetch] build token map failed: {e}")
        return {}


def _gather_needed_tokens(
    models: List[Dict], q_token_map: Dict[str, Dict[str, str]]
) -> List[str]:
    tokens: set[str] = set()
    for m in models:
        if m.get("category") != "polymarket":
            continue
        for snap in m.get("allocationHistory", []) or []:
            qmap: Dict[str, str] = {}
            for e in snap.get("allocations_array") or []:
                if e and e.get("name") and e.get("question"):
                    qmap[e.get("name")] = str(e.get("question")).strip()
            allocs = snap.get("allocations", {}) or {}
            for sym in allocs.keys():
                if sym == "CASH":
                    continue
                q = qmap.get(sym) or (
                    sym.rsplit("_", 1)[0].strip() if "_" in sym else ""
                )
                outcome = sym.rsplit("_", 1)[-1].capitalize() if "_" in sym else ""
                tok = q_token_map.get(q, {}).get(outcome)
                if tok:
                    tokens.add(str(tok))
    return sorted(tokens)


def _prefetch_all_prices(
    models: List[Dict],
    q_token_map: Dict[str, Dict[str, str]],
    price_memo: Dict[Tuple[str, str], Optional[float]],
) -> Tuple[int, int]:
    if not TRY_FETCH_MISSING or not PREFETCH_ALL or not q_token_map:
        return (0, 0)
    try:
        from live_trade_bench.fetchers.polymarket_fetcher import PolymarketFetcher

        start, end = _collect_date_range(models)
        if not start or not end:
            return (0, 0)
        tokens = _gather_needed_tokens(models, q_token_map)
        if not tokens:
            return (0, 0)
        fetcher = PolymarketFetcher(min_delay=0.2, max_delay=0.5)
        filled = 0
        for tok in tokens:
            try:
                hist = fetcher._fetch_daily_history(tok, start, end, fidelity=1440)  # type: ignore[attr-defined]
            except Exception:
                hist = []
            for h in hist:
                d = h.get("date")
                p = h.get("price")
                if d and (tok, d) not in price_memo:
                    try:
                        price_memo[(tok, d)] = float(p)
                        filled += 1
                    except Exception:
                        continue
        return (len(tokens), filled)
    except Exception as e:
        print(f"[prefetch] failed: {e}")
        return (0, 0)


def _fetch_price_on_date(token_id: str, date: str) -> Optional[float]:
    if not TRY_FETCH_MISSING:
        return None
    try:
        from live_trade_bench.fetchers.polymarket_fetcher import PolymarketFetcher

        fetcher = PolymarketFetcher(min_delay=0.1, max_delay=0.2)
        return fetcher.get_price(token_id, date=date)
    except Exception:
        return None


def build_price_cache(models: List[Dict]) -> Dict[Tuple[str, str], float]:
    cache: Dict[Tuple[str, str], float] = {}
    missing: Dict[str, List[str]] = {}
    fetched_ok = 0
    fetched_try = 0
    q_token_map: Dict[str, Dict[str, str]] = {}
    price_memo: Dict[Tuple[str, str], Optional[float]] = {}
    stock_price_memo: Dict[Tuple[str, str], Optional[float]] = {}

    if TRY_FETCH_MISSING:
        q_token_map = _build_question_token_map(models)
        if PREFETCH_ALL and q_token_map:
            t_count, filled = _prefetch_all_prices(models, q_token_map, price_memo)
            print(f"[prefetch] tokens: {t_count} | filled prices: {filled}")
    if PREFETCH_STOCK and USE_STOCK_EOD_FIRST:
        s_tickers, s_filled = _prefetch_stock_prices(models, stock_price_memo)
        print(f"[stock_prefetch] tickers: {len(s_tickers)} | filled prices: {s_filled}")

    missing = _dd(list)
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
                did_fetch = False
                if category == "stock":
                    if USE_STOCK_EOD_FIRST:
                        price = stock_price_memo.get((sym, date_str))
                    if price is None:
                        price = parse_stock_price(prompt, sym)
                elif category == "polymarket":
                    q = qmap.get(sym)
                    if (not q) and "_" in sym:
                        q = sym.rsplit("_", 1)[0].strip()
                    outcome = sym.rsplit("_", 1)[-1] if "_" in sym else ""
                    token_id = (
                        q_token_map.get(q or "", {}).get(
                            str(outcome).capitalize(), None
                        )
                        if TRY_FETCH_MISSING
                        else None
                    )
                    if USE_EOD_FIRST and token_id:
                        memo_key = (token_id, date_str)
                        fetched = price_memo.get(memo_key)
                        if fetched is not None:
                            price = fetched
                        else:
                            fetched_try += 1
                            fetched = _fetch_price_on_date(token_id, date_str)
                            price_memo[memo_key] = fetched
                            if fetched is not None:
                                price = fetched
                                did_fetch = True
                    if price is None:
                        price = parse_polymarket_price(prompt, q or "", str(outcome))
                    if (
                        price is None
                        and token_id
                        and TRY_FETCH_MISSING
                        and not USE_EOD_FIRST
                    ):
                        memo_key = (token_id, date_str)
                        fetched = price_memo.get(memo_key)
                        if fetched is None:
                            fetched_try += 1
                            fetched = _fetch_price_on_date(token_id, date_str)
                            price_memo[memo_key] = fetched
                            if fetched is not None:
                                did_fetch = True
                        price = fetched
                if price is not None:
                    if TRY_FETCH_MISSING and did_fetch and price is not None:
                        fetched_ok += 1
                    cache[(sym, date_str)] = price
                else:
                    missing[sym].append(date_str)
    if missing:
        print("[warn] Missing prices parsed from prompts (sample):")
        for idx, (sym, dates) in enumerate(missing.items()):
            if idx >= 5:
                print("  ...")
                break
            preview = ", ".join(sorted(set(dates))[:5])
            print(f"  - {sym}: {preview}")
    if TRY_FETCH_MISSING:
        print(
            f"[fetch] token-map questions: {len(q_token_map)} | fetch attempts: {fetched_try} | fetched ok: {fetched_ok}"
        )
    return cache


__all__ = [
    "compute_window_delta_metrics",
    "one_day_return_with_alloc_idx",
    "DayCalc",
    "build_price_cache",
]

# ===== Appended styling & combined plotting (target-look) =====


def apply_target_style():
    rcParams.update(
        {
            "figure.figsize": (9.0, 7.5),
            "figure.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.family": "sans-serif",
            "font.sans-serif": [
                "DejaVu Sans",
                "Helvetica",
                "Arial",
            ],
            "font.weight": "normal",
            "axes.labelweight": "normal",
            "axes.titleweight": "normal",
            "font.size": 10.5,
            "axes.titlesize": 28,
            "axes.labelsize": 24,
            "xtick.labelsize": 18,
            "ytick.labelsize": 18,
            "legend.fontsize": 18,
            "axes.labelpad": 0,
            "ytick.major.pad": 0,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "lines.linewidth": 1.4,
        }
    )


def _panel_with_shade(ax, rows: List[Dict[str, Any]], title: str):
    if not rows:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return

    # combined x-range from all models
    all_k = sorted({int(k) for r in rows for k in r.get("metrics", {}).keys()})
    if not all_k:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return

    # per-model: thin faint lines, no model legend
    y_values: List[float] = []
    for r in rows:
        ks = sorted(r.get("metrics", {}).keys())
        if not ks:
            continue
        ys = [r["metrics"][k] for k in ks]
        y_values.extend(
            [
                float(v)
                for v in ys
                if v is not None and not (isinstance(v, float) and math.isnan(v))
            ]
        )
        ax.plot(ks, ys, linewidth=0.8, alpha=0.25, zorder=1)

    # compute weighted mean across models

    mean_sum = _dd(float)
    mean_w = _dd(int)
    for r in rows:
        stats = r.get("stats", {})
        for k, d in stats.items():
            v = d.get("mean")
            n = int(d.get("samples", 0))
            if isinstance(v, (int, float)) and not np.isnan(v) and n > 0:
                k = int(k)
                mean_sum[k] += v * n
                mean_w[k] += n
    if not mean_sum:
        return
    mlags = sorted(mean_sum.keys())
    mseries = [(mean_sum[k] / mean_w[k]) if mean_w[k] > 0 else np.nan for k in mlags]
    y_values.extend(
        [
            float(v)
            for v in mseries
            if v is not None and not (isinstance(v, float) and math.isnan(v))
        ]
    )

    # mean band from cross-model 25-75% over means (not per-model bands)
    vals_by_k = {k: [] for k in mlags}
    for r in rows:
        stats = r.get("stats", {})
        for k in mlags:
            v = stats.get(k, {}).get("mean")
            if v is not None and not np.isnan(v):
                vals_by_k[k].append(v)
    lowers, uppers = [], []
    for k in mlags:
        vals = vals_by_k[k]
        if vals:
            lowers.append(np.nanpercentile(vals, 25))
            uppers.append(np.nanpercentile(vals, 75))
        else:
            lowers.append(np.nan)
            uppers.append(np.nan)
    y_values.extend(
        [
            float(v)
            for v in lowers + uppers
            if v is not None and not (isinstance(v, float) and math.isnan(v))
        ]
    )

    # draw mean band (gray) beneath mean line
    ax.fill_between(mlags, lowers, uppers, color="gray", alpha=0.15, zorder=2)

    # draw mean line with triangle markers and numeric labels
    (mean_line,) = ax.plot(mlags, mseries, color="black", linewidth=2.0, zorder=3)
    ax.plot(
        mlags,
        mseries,
        marker="^",
        markersize=5.0,
        markerfacecolor="white",
        markeredgecolor="black",
        markeredgewidth=0.8,
        linestyle="None",
        zorder=4,
    )
    leftmost = float(min(mlags)) if mlags else None
    rightmost = float(max(mlags)) if mlags else None

    def _format_pct_value(val: float, *, with_symbol: bool = True) -> str:
        pct = val * 100.0
        if abs(pct) < 1e-10:
            pct = 0.0
        sign = "\u2212" if pct < 0 else ""
        mag = abs(pct)
        text = f"{mag:.2f}".rstrip("0").rstrip(".")
        body = f"{sign}{text}"
        return f"{body}%" if with_symbol else body

    for x, y in zip(mlags, mseries):
        if y is None or (isinstance(y, float) and np.isnan(y)):
            continue
        offset_x = 5
        ha = "left"
        if leftmost is not None and float(x) <= leftmost:
            offset_x = 20
            ha = "right"
        if rightmost is not None and float(x) >= rightmost:
            offset_x = -6
            ha = "right"
        ax.annotate(
            _format_pct_value(y),
            (x, y),
            xytext=(offset_x, 6),
            textcoords="offset points",
            fontsize=14,
            color="#333333",
            zorder=5,
            ha=ha,
            va="bottom",
            clip_on=True,
        )

    # cosmetics
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(1.1)
    x_min = float(min(all_k))
    x_max = float(max(all_k))
    if x_min == x_max:
        pad_x = max(abs(x_min) * 0.05, 0.1)
        ax.set_xlim(x_min - pad_x, x_max + pad_x)
    else:
        span = x_max - x_min
        pad_left = max(span * 0.05, 0.2)
        pad_right = max(span * 0.05, 0.3)
        ax.set_xlim(x_min - pad_left, x_max + pad_right)
    ax.set_xlabel("Rebalance Interval (Days)")
    ax.set_ylabel("Mean k-Δ (%)")

    valid_vals = [v for v in y_values if math.isfinite(v)]
    if valid_vals:
        y_min = min(valid_vals)
        y_max = max(valid_vals)
        if y_min == y_max:
            pad = max(abs(y_min) * 0.05, 0.01)
        else:
            pad = max((y_max - y_min) * 0.08, 1e-3)
        ax.set_ylim(y_min - pad, y_max + pad)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda val, _: _format_pct_value(val, with_symbol=False))
    )


def main() -> None:
    try:
        models_path = _find_models_path()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    with models_path.open() as f:
        models = json.load(f)
    print(f"Loaded {len(models)} models from {models_path}")

    price_cache = build_price_cache(models)
    print(f"Collected {len(price_cache)} price entries")

    rf_daily = 0.0
    by_cat: Dict[str, List[Dict[str, Any]]] = {"stock": [], "polymarket": []}
    k_values = sorted(set(int(x) for x in K_SET_DEFAULT if int(x) >= 1))

    for m in models:
        cat = m.get("category")
        if cat not in by_cat:
            continue
        hist = m.get("allocationHistory", [])
        if len(hist) < 2:
            continue
        hist_sorted = sorted(hist, key=lambda x: x.get("timestamp") or "")
        stats = compute_window_delta_metrics(
            hist_sorted,
            price_cache,
            k_values,
            WINDOW_H,
            rf_daily=rf_daily,
            missing_policy=MISSING_POLICY_DEFAULT,
            tc_bps=TC_BPS,
        )
        metrics_mean = {int(k): (stats[int(k)]["mean"]) for k in k_values}
        by_cat[cat].append(
            {
                "name": m.get("name") or m.get("id") or "unknown",
                "metrics": metrics_mean,
                "stats": stats,
            }
        )

    # 2) Create category-specific figures
    apply_target_style()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for cat, title in (("stock", "Stock"), ("polymarket", "Polymarket")):
        fig, ax = plt.subplots(figsize=(9.0, 5.25))
        _panel_with_shade(ax, by_cat.get(cat, []), title)
        fig.tight_layout(rect=[0.05, 0.08, 0.98, 0.98])
        out_path = OUT_DIR / f"window_delta_{cat}_H{WINDOW_H}.pdf"
        fig.savefig(out_path, dpi=300)
        plt.close(fig)
        print(f"Saved: {out_path}")


if __name__ == "__main__":
    # Ensure local package imports (live_trade_bench) work when running as a script
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    main()
