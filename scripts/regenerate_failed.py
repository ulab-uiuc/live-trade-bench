#!/usr/bin/env python3
"""
Regenerate allocation snapshots where LLM calls previously failed.

This script loads an input models data JSON file, replays any allocation history
entry with a failed `llm_output`, and writes a new JSON file with refreshed
results. It uses the existing agent implementations to perform the LLM calls.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from live_trade_bench.agents.polymarket_agent import LLMPolyMarketAgent
from live_trade_bench.agents.stock_agent import LLMStockAgent
from live_trade_bench.utils.agent_utils import normalize_allocations

Snapshot = Dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input_path",
        type=Path,
        nargs="?",
        default=Path("backend/models_data_1009.json"),
        help="Source JSON file to process.",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        nargs="?",
        default=Path("backend/models_data_1009_refreshed.json"),
        help="Destination JSON file for updated data.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing output; still performs regeneration checks.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=20.0,
        help="Seconds to sleep after each regenerated snapshot (default: 20).",
    )
    return parser.parse_args()


def build_agent(category: str, name: str, model_name: str):
    if category == "stock":
        return LLMStockAgent(name=name, model_name=model_name)
    if category == "polymarket":
        return LLMPolyMarketAgent(name=name, model_name=model_name)
    raise ValueError(f"Unsupported category: {category}")


def call_agent_llm(agent, prompt: str) -> Dict[str, Any]:
    messages = [{"role": "user", "content": prompt}]
    response = agent._call_llm(messages)
    if not response.get("success"):
        raise RuntimeError(f"LLM call failed: {response.get('error')}")
    parsed = agent._parse_allocation_response(response)
    if not parsed:
        raise RuntimeError("Parsed allocation response is empty")
    allocations = normalize_allocations(parsed)
    if not allocations:
        raise RuntimeError("No valid allocations returned from LLM")
    reasoning = parsed.get("reasoning")
    return {
        "allocations": allocations,
        "raw_response": response,
        "reasoning": reasoning,
    }


def build_allocations_array(
    allocations: Dict[str, float],
    metadata_source: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    metadata_map: Dict[str, Dict[str, Any]] = {}
    for entry in metadata_source:
        name = entry.get("name")
        if not name:
            continue
        metadata_map[name] = {
            k: v for k, v in entry.items() if k not in {"name", "allocation"}
        }

    enriched: List[Dict[str, Any]] = []
    for symbol, weight in sorted(
        allocations.items(), key=lambda kv: kv[1], reverse=True
    ):
        row = {"name": symbol, "allocation": weight}
        if symbol in metadata_map:
            row.update(metadata_map[symbol])
        enriched.append(row)
    return enriched


def update_profit_history(model_entry: Dict[str, Any]) -> None:
    profit_history = model_entry.get("profitHistory", [])
    if not profit_history:
        return
    by_timestamp = {item.get("timestamp"): item for item in profit_history}
    for snapshot in model_entry.get("allocationHistory", []):
        ts = snapshot.get("timestamp")
        if ts and ts in by_timestamp:
            ph_entry = by_timestamp[ts]
            ph_entry["profit"] = snapshot.get("profit")
            ph_entry["totalValue"] = snapshot.get("total_value")


def refresh_snapshot(
    model_entry: Dict[str, Any],
    snapshot: Snapshot,
    agent_cache: Dict[Tuple[str, str, str], Any],
    delay: float,
) -> bool:
    llm_output = snapshot.get("llm_output") or {}
    if llm_output.get("success") is not False:
        return False

    llm_input = snapshot.get("llm_input")
    if not llm_input:
        raise RuntimeError("Missing llm_input for failed snapshot")

    model_name = llm_input.get("model") or model_entry.get("id", "")
    cache_key = (model_entry.get("category"), model_entry.get("name"), model_name)
    if cache_key not in agent_cache:
        agent_cache[cache_key] = build_agent(cache_key[0], cache_key[1], cache_key[2])
    agent = agent_cache[cache_key]
    agent.model_name = model_name

    prompt = llm_input.get("prompt")
    if not prompt:
        raise RuntimeError("Missing prompt in llm_input")

    max_retries = 5
    backoff_base = max(delay, 20.0)
    for attempt in range(max_retries):
        try:
            result = call_agent_llm(agent, prompt)
            break
        except RuntimeError as exc:
            err_text = str(exc)
            is_rate_limited = "ratelimit" in err_text.lower() or "429" in err_text
            if not is_rate_limited or attempt == max_retries - 1:
                raise
            sleep_for = backoff_base * (attempt + 1)
            print(
                f"Rate limit hit for {model_entry.get('name')} ({model_entry.get('category')}),"
                f" backing off {sleep_for:.0f}s..."
            )
            time.sleep(sleep_for)
    allocations = result["allocations"]
    response = result["raw_response"]
    snapshot["allocations"] = allocations
    snapshot["allocations_array"] = build_allocations_array(
        allocations, snapshot.get("allocations_array", [])
    )
    snapshot["llm_output"] = {
        "success": True,
        "content": response.get("content"),
        "error": None,
        "timestamp": datetime.now().isoformat(),
    }
    if delay > 0:
        time.sleep(delay)
    return True


def ensure_portfolio_consistency(model_entry: Dict[str, Any]) -> None:
    allocation_history = model_entry.get("allocationHistory") or []
    if not allocation_history:
        return
    final_snapshot = allocation_history[-1]
    latest_allocations = final_snapshot.get("allocations") or {}

    portfolio = model_entry.get("portfolio") or {}
    portfolio.setdefault("target_allocations", latest_allocations)
    portfolio["target_allocations"] = latest_allocations

    current_alloc = portfolio.get("current_allocations")
    if isinstance(current_alloc, dict):
        portfolio["current_allocations"] = latest_allocations

    model_entry["asset_allocation"] = latest_allocations


def process_models(models: List[Dict[str, Any]], delay: float) -> Tuple[int, List[str]]:
    refreshed = 0
    errors: List[str] = []
    agent_cache: Dict[Tuple[str, str, str], Any] = {}

    for model_entry in models:
        model_name = model_entry.get("name", "unknown")
        category = model_entry.get("category", "unknown")

        for idx, snapshot in enumerate(model_entry.get("allocationHistory", [])):
            try:
                updated = refresh_snapshot(model_entry, snapshot, agent_cache, delay)
                if updated:
                    refreshed += 1
            except Exception as exc:
                error_msg = (
                    f"❌ Failed: {category}/{model_name} "
                    f"snapshot #{idx} - {type(exc).__name__}: {exc}"
                )
                print(error_msg)
                errors.append(error_msg)
                # Continue processing other snapshots

        update_profit_history(model_entry)
        ensure_portfolio_consistency(model_entry)
        model_entry["trades"] = len(model_entry.get("allocationHistory", []))

    return refreshed, errors


def main() -> None:
    args = parse_args()
    with args.input_path.open("r") as fh:
        models = json.load(fh)

    try:
        refreshed, errors = process_models(models, args.delay)

        print(f"\n{'='*60}")
        print(f"✅ Successfully regenerated {refreshed} snapshots")

        if errors:
            print(f"❌ Encountered {len(errors)} errors:")
            for err in errors:
                print(f"   {err}")

        # Save successful updates even if there were errors
        if not args.dry_run:
            with args.output_path.open("w") as fh:
                json.dump(models, fh, indent=4)
            print(f"\n💾 Updated data written to {args.output_path}")
            print(
                f"   (Saved {refreshed} successful updates despite {len(errors)} failures)"
            )
        else:
            print("\nDry run complete; no file written.")

        # Exit with error code if there were failures
        if errors:
            print(f"\n⚠️  Script completed with {len(errors)} errors")
            raise SystemExit(1)

    except Exception as exc:
        # Critical failure - still try to save what we have
        print(f"\n💥 Critical error occurred: {exc}")

        if not args.dry_run:
            emergency_path = args.output_path.with_suffix(".emergency.json")
            try:
                with emergency_path.open("w") as fh:
                    json.dump(models, fh, indent=4)
                print(f"🚨 Emergency save to {emergency_path}")
            except Exception as save_exc:
                print(f"❌ Emergency save failed: {save_exc}")

        raise


if __name__ == "__main__":
    main()
