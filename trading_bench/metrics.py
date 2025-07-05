import math
from typing import Any

from .signal import TradeRecord


class MetricsLogger:
    """
    Quantitative backtesting metrics calculator with comprehensive trading strategy evaluation indicators
    """

    def __init__(self):
        self.trades: list[TradeRecord] = []
        self.equity_curve: list[float] = [
            1.0
        ]  # Start from 1.0, representing 100% initial capital
        self.current_equity = 1.0

    def record(self, trade: TradeRecord) -> None:
        """Record a complete trade"""
        self.trades.append(trade)
        # Update equity curve
        self.current_equity *= 1 + trade.return_pct
        self.equity_curve.append(self.current_equity)

    def summary(self) -> dict[str, Any]:
        """
        Calculate complete backtesting metrics summary
        """
        if not self.trades:
            return self._empty_summary()

        return {
            # Basic statistical indicators
            **self._basic_stats(),
            # Risk metrics
            **self._risk_metrics(),
            # Return metrics
            **self._return_metrics(),
            # Trading statistics
            **self._trade_stats(),
            # Time metrics
            **self._time_metrics(),
            # Advanced metrics
            **self._advanced_metrics(),
        }

    def _empty_summary(self) -> dict[str, Any]:
        """Default return values for empty trade records"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_return': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'max_return': 0.0,
            'min_return': 0.0,
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'calmar_ratio': 0.0,
            'avg_trade_duration': 0.0,
            'volatility': 0.0,
            'var_95': 0.0,
            'var_99': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'avg_equity_curve': 0.0,
            'final_equity': 1.0,
        }

    def _basic_stats(self) -> dict[str, Any]:
        """Basic statistical indicators"""
        returns = [trade.return_pct for trade in self.trades]
        winning_trades = [r for r in returns if r > 0]
        losing_trades = [r for r in returns if r < 0]

        total_trades = len(self.trades)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)

        return {
            'total_trades': total_trades,
            'winning_trades': winning_count,
            'losing_trades': losing_count,
            'win_rate': winning_count / total_trades if total_trades > 0 else 0.0,
            'avg_return': sum(returns) / total_trades if total_trades > 0 else 0.0,
            'max_return': max(returns) if returns else 0.0,
            'min_return': min(returns) if returns else 0.0,
            'best_trade': max(returns) if returns else 0.0,
            'worst_trade': min(returns) if returns else 0.0,
        }

    def _risk_metrics(self) -> dict[str, Any]:
        """Risk metrics"""
        returns = [trade.return_pct for trade in self.trades]
        if not returns:
            return {
                'volatility': 0.0,
                'var_95': 0.0,
                'var_99': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0,
            }

        # Calculate return series
        avg_return = sum(returns) / len(returns)

        # Volatility
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance)

        # VaR (Value at Risk)
        sorted_returns = sorted(returns)
        var_95_idx = int(len(sorted_returns) * 0.05)
        var_99_idx = int(len(sorted_returns) * 0.01)
        var_95 = (
            sorted_returns[var_95_idx]
            if var_95_idx < len(sorted_returns)
            else min(returns)
        )
        var_99 = (
            sorted_returns[var_99_idx]
            if var_99_idx < len(sorted_returns)
            else min(returns)
        )

        # Maximum drawdown
        max_drawdown = self._calculate_max_drawdown()

        # Sharpe ratio (assuming risk-free rate of 0)
        sharpe_ratio = avg_return / volatility if volatility > 0 else 0.0

        # Sortino ratio (only considering downside risk)
        downside_returns = [r for r in returns if r < avg_return]
        downside_variance = (
            sum((r - avg_return) ** 2 for r in downside_returns) / len(returns)
            if returns
            else 0
        )
        downside_volatility = math.sqrt(downside_variance)
        sortino_ratio = (
            avg_return / downside_volatility if downside_volatility > 0 else 0.0
        )

        # Calmar ratio
        calmar_ratio = avg_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

        return {
            'volatility': volatility,
            'var_95': var_95,
            'var_99': var_99,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
        }

    def _return_metrics(self) -> dict[str, Any]:
        """Return metrics"""
        returns = [trade.return_pct for trade in self.trades]
        winning_trades = [r for r in returns if r > 0]
        losing_trades = [r for r in returns if r < 0]

        total_return = self.current_equity - 1.0  # Total return rate

        avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0.0

        # Profit factor
        profit_factor = (
            abs(sum(winning_trades) / sum(losing_trades))
            if losing_trades and sum(losing_trades) != 0
            else 0.0
        )

        return {
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'final_equity': self.current_equity,
        }

    def _trade_stats(self) -> dict[str, Any]:
        """Trading statistics"""
        if not self.trades:
            return {
                'consecutive_wins': 0,
                'consecutive_losses': 0,
                'avg_trade_duration': 0.0,
            }

        # Consecutive wins/losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in self.trades:
            if trade.return_pct > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            elif trade.return_pct < 0:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)

        # Average trade duration
        avg_duration = sum(trade.trade_duration for trade in self.trades) / len(
            self.trades
        )

        return {
            'consecutive_wins': max_consecutive_wins,
            'consecutive_losses': max_consecutive_losses,
            'avg_trade_duration': avg_duration,
        }

    def _time_metrics(self) -> dict[str, Any]:
        """Time-related metrics"""
        if not self.trades:
            return {'total_days': 0, 'avg_trades_per_day': 0.0}

        # Calculate total trading days
        start_time = min(trade.entry_time for trade in self.trades)
        end_time = max(trade.exit_time for trade in self.trades)
        total_days = (end_time - start_time).days

        avg_trades_per_day = len(self.trades) / total_days if total_days > 0 else 0.0

        return {'total_days': total_days, 'avg_trades_per_day': avg_trades_per_day}

    def _advanced_metrics(self) -> dict[str, Any]:
        """Advanced metrics"""
        if not self.trades:
            return {'avg_equity_curve': 0.0, 'equity_curve_volatility': 0.0}

        # Equity curve statistics
        avg_equity = sum(self.equity_curve) / len(self.equity_curve)

        # Equity curve volatility
        equity_returns = []
        for i in range(1, len(self.equity_curve)):
            equity_returns.append(self.equity_curve[i] / self.equity_curve[i - 1] - 1)

        equity_volatility = (
            math.sqrt(sum(r**2 for r in equity_returns) / len(equity_returns))
            if equity_returns
            else 0.0
        )

        return {
            'avg_equity_curve': avg_equity,
            'equity_curve_volatility': equity_volatility,
        }

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if len(self.equity_curve) < 2:
            return 0.0

        max_drawdown = 0.0
        peak = self.equity_curve[0]

        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def get_trade_details(self) -> list[dict[str, Any]]:
        """Get detailed trade records"""
        return [
            {
                'entry_time': trade.entry_time.isoformat(),
                'entry_price': trade.entry_price,
                'exit_time': trade.exit_time.isoformat(),
                'exit_price': trade.exit_price,
                'return_pct': trade.return_pct,
                'trade_duration': trade.trade_duration,
                'high_during_trade': trade.high_during_trade,
                'low_during_trade': trade.low_during_trade,
            }
            for trade in self.trades
        ]

    def get_equity_curve(self) -> list[float]:
        """Get equity curve data"""
        return self.equity_curve
