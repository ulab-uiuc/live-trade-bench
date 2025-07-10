from datetime import datetime, timedelta


from fastapi import APIRouter, HTTPException, Query

from app.data import get_trades_data, get_real_trades_data
from app.schemas import Trade, TradingSummary

router = APIRouter(prefix='/api/trades', tags=['trades'])


@router.get('/', response_model=list[Trade])
async def get_trades(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    symbol: str | None = Query(default=None),
    model: str | None = Query(default=None),
):
    """Get trading history with optional filtering and pagination."""
    try:
        trades = get_trades_data()

        # Apply filters
        if symbol:
            trades = [t for t in trades if t.symbol.upper() == symbol.upper()]

        if model:
            trades = [t for t in trades if model.lower() in t.model.lower()]

        # Sort by timestamp (newest first)
        trades.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        total_trades = len(trades)
        trades = trades[offset : offset + limit]

        return trades
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error fetching trades: {str(e)}')


@router.get('/summary', response_model=TradingSummary)
async def get_trading_summary():
    """Get trading performance summary."""
    try:
        trades = get_trades_data()

        if not trades:
            return TradingSummary(
                total_profit=0.0,
                total_trades=0,
                profitable_trades=0,
                win_rate=0.0,
                average_profit=0.0,
                today_profit=0.0,
            )

        total_profit = sum(trade.profit for trade in trades)
        total_trades = len(trades)
        profitable_trades = len([t for t in trades if t.profit > 0])
        win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
        average_profit = total_profit / total_trades if total_trades > 0 else 0

        # Calculate today's profit (trades from last 24 hours)
        now = datetime.now()
        today_start = now - timedelta(days=1)
        today_trades = [t for t in trades if t.timestamp >= today_start]
        today_profit = sum(trade.profit for trade in today_trades)

        return TradingSummary(
            total_profit=round(total_profit, 2),
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            win_rate=round(win_rate, 2),
            average_profit=round(average_profit, 2),
            today_profit=round(today_profit, 2),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error calculating summary: {str(e)}'
        )


@router.get('/stats')
async def get_trading_stats():
    """Get detailed trading statistics."""
    try:
        trades = get_trades_data()

        if not trades:
            return {
                'total_trades': 0,
                'total_profit': 0.0,
                'win_rate': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'profit_factor': 0.0,
            }

        profits = [t.profit for t in trades if t.profit > 0]
        losses = [t.profit for t in trades if t.profit < 0]

        total_profit = sum(trade.profit for trade in trades)
        total_wins = len(profits)
        total_losses = len(losses)
        win_rate = (total_wins / len(trades)) * 100 if trades else 0

        largest_win = max(profits) if profits else 0
        largest_loss = min(losses) if losses else 0
        average_win = sum(profits) / len(profits) if profits else 0
        average_loss = sum(losses) / len(losses) if losses else 0

        # Profit factor = total wins / abs(total losses)
        total_loss_amount = abs(sum(losses)) if losses else 1
        profit_factor = sum(profits) / total_loss_amount if profits else 0

        return {
            'total_trades': len(trades),
            'total_profit': round(total_profit, 2),
            'win_rate': round(win_rate, 2),
            'largest_win': round(largest_win, 2),
            'largest_loss': round(largest_loss, 2),
            'average_win': round(average_win, 2),
            'average_loss': round(average_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'total_wins': total_wins,
            'total_losses': total_losses,
            'symbols_traded': list(set(t.symbol for t in trades)),
            'models_used': list(set(t.model for t in trades)),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error calculating stats: {str(e)}'
        )


@router.get('/by-symbol/{symbol}')
async def get_trades_by_symbol(symbol: str):
    """Get all trades for a specific symbol."""
    try:
        trades = get_trades_data()
        symbol_trades = [t for t in trades if t.symbol.upper() == symbol.upper()]

        if not symbol_trades:
            raise HTTPException(
                status_code=404, detail=f'No trades found for symbol {symbol}'
            )

        # Calculate symbol-specific metrics
        total_profit = sum(t.profit for t in symbol_trades)
        total_trades = len(symbol_trades)
        profitable_trades = len([t for t in symbol_trades if t.profit > 0])
        win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

        return {
            'symbol': symbol.upper(),
            'trades': symbol_trades,
            'summary': {
                'total_trades': total_trades,
                'total_profit': round(total_profit, 2),
                'profitable_trades': profitable_trades,
                'win_rate': round(win_rate, 2),
                'average_profit': round(total_profit / total_trades, 2)
                if total_trades > 0
                else 0,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching symbol trades: {str(e)}'
        )


@router.get('/by-model/{model_name}')
async def get_trades_by_model(model_name: str):
    """Get all trades for a specific model."""
    try:
        trades = get_trades_data()
        model_trades = [t for t in trades if model_name.lower() in t.model.lower()]

        if not model_trades:
            raise HTTPException(
                status_code=404, detail=f'No trades found for model {model_name}'
            )

        # Calculate model-specific metrics
        total_profit = sum(t.profit for t in model_trades)
        total_trades = len(model_trades)
        profitable_trades = len([t for t in model_trades if t.profit > 0])
        win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

        return {
            'model': model_name,
            'trades': model_trades,
            'summary': {
                'total_trades': total_trades,
                'total_profit': round(total_profit, 2),
                'profitable_trades': profitable_trades,
                'win_rate': round(win_rate, 2),
                'average_profit': round(total_profit / total_trades, 2)
                if total_trades > 0
                else 0,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching model trades: {str(e)}'
        )


@router.get('/real', response_model=list[Trade])
async def get_real_trades(
    ticker: str = Query(default="NVDA", description="Stock ticker symbol"),
    days: int = Query(default=7, ge=1, le=30, description="Number of days of trading data")
):
    """Get real trading data by fetching stock prices."""
    try:
        real_trades = get_real_trades_data(ticker=ticker, days=days)
        return real_trades
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error fetching real trades: {str(e)}'
        )
