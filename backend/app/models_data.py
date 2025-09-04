"""
Simple model data provider - directly uses live_trade_bench without complex wrappers
"""

import os
import sys
import threading
from typing import Any, Dict, List, Optional

# Add live_trade_bench to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from live_trade_bench import (
    create_stock_portfolio_system,
    create_polymarket_portfolio_system,
)

# Simple global instances
_stock_system = None
_polymarket_system = None

def _get_stock_system():
    """Get or create stock system"""
    global _stock_system
    if _stock_system is None:
        _stock_system = create_stock_portfolio_system()
        
        # Add 3 models
        models = [
            ("GPT-4o", "gpt-4o", 1000),
            ("Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022", 1000),
            ("GPT-4 Turbo", "gpt-4-turbo", 1000),
        ]
        
        for name, model_name, initial_cash in models:
            _stock_system.add_agent(name=name, initial_cash=initial_cash, model_name=model_name)
    
    return _stock_system

def _get_polymarket_system():
    """Get or create polymarket system"""
    global _polymarket_system
    if _polymarket_system is None:
        _polymarket_system = create_polymarket_portfolio_system()
        
        models = [
            ("GPT-4o", "gpt-4o", 500),
            ("Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022", 500),
            ("GPT-4 Turbo", "gpt-4-turbo", 500),
        ]
        
        for name, model_name, initial_cash in models:
            _polymarket_system.add_agent(name=name, initial_cash=initial_cash, model_name=model_name)
    
    return _polymarket_system

def get_models_data() -> List[Dict[str, Any]]:
    """Get all model data - the only function routers actually need!"""
    models = []
    
    # Stock models
    stock_system = _get_stock_system()
    for agent_name, agent in stock_system.agents.items():
        account = agent.account
        models.append({
            "id": f"{agent_name.lower().replace(' ', '-')}_stock",
            "name": agent_name,
            "category": "stock",
            "performance": getattr(account, 'return_pct', 0.0),
            "accuracy": 75.0,
            "trades": 10,
            "profit": getattr(account, 'unrealized_pnl', 0.0),
            "status": "active",
            "last_updated": "2024-01-01T00:00:00Z"
        })
    
    # Polymarket models
    poly_system = _get_polymarket_system()
    for agent_name, agent in poly_system.agents.items():
        account = agent.account
        models.append({
            "id": f"{agent_name.lower().replace(' ', '-')}_polymarket",
            "name": agent_name,
            "category": "polymarket",
            "performance": getattr(account, 'return_pct', 0.0),
            "accuracy": 70.0,
            "trades": 8,
            "profit": getattr(account, 'unrealized_pnl', 0.0),
            "status": "active",
            "last_updated": "2024-01-01T00:00:00Z"
        })
    
    return models

def get_portfolio(model_id: str) -> Optional[Dict[str, Any]]:
    """Get portfolio for a specific model"""
    
    # Parse model ID
    if "_stock" in model_id:
        system = _get_stock_system()
        agent_name = model_id.replace("_stock", "").replace("-", " ").title()
        category = "stock"
    elif "_polymarket" in model_id:
        system = _get_polymarket_system()
        agent_name = model_id.replace("_polymarket", "").replace("-", " ").title()
        category = "polymarket"
    else:
        return None
    
    # Find agent
    agent = system.agents.get(agent_name)
    if not agent:
        return None
    
    account = agent.account
    
    return {
        "model_id": model_id,
        "model_name": agent_name,
        "category": category,
        "cash": account.cash_balance,
        "total_value": account.get_total_value(),
        "holdings": getattr(account, 'positions', {}),
        "target_allocations": getattr(account, 'target_allocations', {}),
        "return_pct": getattr(account, 'return_pct', 0.0),
        "unrealized_pnl": getattr(account, 'unrealized_pnl', 0.0),
        "last_updated": "2024-01-01T00:00:00Z",
        "market_data_available": True
    }

def get_system_status() -> Dict[str, Any]:
    """Get simple system status"""
    stock_count = len(_get_stock_system().agents)
    poly_count = len(_get_polymarket_system().agents)
    
    return {
        "running": True,  # Always true since we're just data provider
        "stock_agents": stock_count,
        "polymarket_agents": poly_count,
        "total_agents": stock_count + poly_count
    }

def trigger_cycle():
    """Run one cycle manually"""
    try:
        # Run both systems briefly in parallel
        stock_thread = threading.Thread(
            target=lambda: _get_stock_system().run(duration_minutes=0.5, interval=15),
            daemon=True
        )
        poly_thread = threading.Thread(
            target=lambda: _get_polymarket_system().run(duration_minutes=0.5, interval=15),
            daemon=True
        )
        
        stock_thread.start()
        poly_thread.start()
        
        stock_thread.join(timeout=60)
        poly_thread.join(timeout=60)
        
        return {"status": "success", "message": "Trading cycle completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
