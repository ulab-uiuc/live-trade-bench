"""
Backtesting visualization module for generating meaningful charts and plots.
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from ..core.metrics import MetricsLogger


class BacktestVisualizer:
    """
    Visualization class for generating backtesting charts and plots.
    """

    def __init__(self, metrics_logger: MetricsLogger, output_dir: str = './charts'):
        self.metrics_logger = metrics_logger
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set style for better looking plots
        plt.style.use('seaborn-v0_8')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10

    def generate_all_charts(self, ticker: str, save: bool = True) -> dict[str, str | None]:
        """
        Generate all backtesting charts.

        Args:
            ticker: Stock ticker symbol
            save: Whether to save charts to files

        Returns:
            Dictionary of chart file paths
        """
        chart_paths = {}

        # Generate individual charts
        chart_paths['equity_curve'] = self.plot_equity_curve(ticker, save)
        chart_paths['drawdown'] = self.plot_drawdown(ticker, save)
        chart_paths['trade_distribution'] = self.plot_trade_distribution(ticker, save)
        chart_paths['monthly_returns'] = self.plot_monthly_returns(ticker, save)
        chart_paths['cumulative_returns'] = self.plot_cumulative_returns(ticker, save)
        chart_paths['trade_timeline'] = self.plot_trade_timeline(ticker, save)

        # Generate summary dashboard
        chart_paths['dashboard'] = self.create_dashboard(ticker, save)

        return chart_paths

    def plot_equity_curve(self, ticker: str, save: bool = True) -> str | None:
        """Plot equity curve over time."""
        equity_curve = self.metrics_logger.get_equity_curve()

        if len(equity_curve) < 2:
            return None

        plt.figure(figsize=(12, 6))
        plt.plot(equity_curve, linewidth=2, color='blue', alpha=0.8)
        plt.axhline(
            y=1.0, color='red', linestyle='--', alpha=0.5, label='Initial Capital'
        )

        plt.title(f'{ticker} Equity Curve', fontsize=14, fontweight='bold')
        plt.xlabel('Trade Number', fontsize=12)
        plt.ylabel('Equity', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Add final equity annotation
        final_equity = equity_curve[-1]
        plt.annotate(
            f'Final: {final_equity:.4f}',
            xy=(len(equity_curve) - 1, final_equity),
            xytext=(len(equity_curve) * 0.7, final_equity * 1.1),
            arrowprops={'arrowstyle': '->', 'color': 'red'},
            fontsize=10,
            fontweight='bold',
        )

        plt.tight_layout()

        if save:
            filepath = self.output_dir / f'{ticker}_equity_curve.png'
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None

    def plot_drawdown(self, ticker: str, save: bool = True) -> str | None:
        """Plot drawdown chart."""
        equity_curve = self.metrics_logger.get_equity_curve()

        if len(equity_curve) < 2:
            return None

        # Calculate drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak * 100

        plt.figure(figsize=(12, 6))
        plt.fill_between(
            range(len(drawdown)), drawdown, 0, alpha=0.3, color='red', label='Drawdown'
        )
        plt.plot(drawdown, color='red', linewidth=1, alpha=0.7)

        plt.title(f'{ticker} Drawdown Analysis', fontsize=14, fontweight='bold')
        plt.xlabel('Trade Number', fontsize=12)
        plt.ylabel('Drawdown (%)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Add max drawdown annotation
        max_dd_idx = np.argmin(drawdown)
        max_dd = drawdown[max_dd_idx]
        plt.annotate(
            f'Max DD: {max_dd:.2f}%',
            xy=(float(max_dd_idx), float(max_dd)),
            xytext=(float(max_dd_idx) * 1.2, float(max_dd) * 0.5),
            arrowprops={'arrowstyle': '->', 'color': 'red'},
            fontsize=10,
            fontweight='bold',
        )

        plt.tight_layout()

        if save:
            filepath = self.output_dir / f'{ticker}_drawdown.png'
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None

    def plot_trade_distribution(self, ticker: str, save: bool = True) -> str | None:
        """Plot trade return distribution."""
        trades = self.metrics_logger.trades
        if not trades:
            return None

        returns = [trade.return_pct * 100 for trade in trades]

        plt.figure(figsize=(12, 6))

        # Create subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Histogram
        ax1.hist(returns, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Break-even')
        ax1.axvline(
            x=np.mean(returns),
            color='green',
            linestyle='-',
            alpha=0.7,
            label=f'Mean: {np.mean(returns):.2f}%',
        )
        ax1.set_title('Trade Return Distribution', fontweight='bold')
        ax1.set_xlabel('Return (%)')
        ax1.set_ylabel('Frequency')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Box plot
        ax2.boxplot(
            returns,
            patch_artist=True,
            boxprops={'facecolor': 'lightblue', 'alpha': 0.7},
        )
        ax2.set_title('Trade Return Statistics', fontweight='bold')
        ax2.set_ylabel('Return (%)')
        ax2.grid(True, alpha=0.3)

        plt.suptitle(f'{ticker} Trade Analysis', fontsize=14, fontweight='bold')
        plt.tight_layout()

        if save:
            filepath = self.output_dir / f'{ticker}_trade_distribution.png'
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None

    def plot_monthly_returns(self, ticker: str, save: bool = True) -> str | None:
        """Plot monthly returns heatmap."""
        trades = self.metrics_logger.trades
        if not trades:
            return None

        # Group trades by month
        monthly_returns: dict[str, list[float]] = {}
        for trade in trades:
            month_key = trade.entry_time.strftime('%Y-%m')
            if month_key not in monthly_returns:
                monthly_returns[month_key] = []
            monthly_returns[month_key].append(trade.return_pct)

        # Calculate monthly total returns
        monthly_totals = {}
        for month, returns in monthly_returns.items():
            monthly_totals[month] = np.sum(returns) * 100  # Convert to percentage

        if not monthly_totals:
            return None

        months = list(monthly_totals.keys())
        returns = list(monthly_totals.values())

        plt.figure(figsize=(12, 6))
        colors = ['red' if r < 0 else 'green' for r in returns]
        bars = plt.bar(range(len(months)), returns, color=colors, alpha=0.7)

        # Add value labels on bars
        for bar, ret in zip(bars, returns, strict=False):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,
                f'{ret:.1f}%',
                ha='center',
                va='bottom',
                fontweight='bold',
            )

        plt.title(f'{ticker} Monthly Returns', fontsize=14, fontweight='bold')
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Return (%)', fontsize=12)
        plt.xticks(range(len(months)), months, rotation=45)
        plt.grid(True, alpha=0.3)
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        plt.tight_layout()

        if save:
            filepath = self.output_dir / f'{ticker}_monthly_returns.png'
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None

    def plot_cumulative_returns(self, ticker: str, save: bool = True) -> str | None:
        """Plot cumulative returns over time."""
        trades = self.metrics_logger.trades
        if not trades:
            return None

        # Calculate cumulative returns
        cumulative_returns = []
        total_return: float = 0.0
        for trade in trades:
            total_return += trade.return_pct
            cumulative_returns.append(total_return * 100)  # Convert to percentage

        plt.figure(figsize=(12, 6))
        plt.plot(cumulative_returns, linewidth=2, color='blue', alpha=0.8)
        plt.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='Break-even')

        plt.title(f'{ticker} Cumulative Returns', fontsize=14, fontweight='bold')
        plt.xlabel('Trade Number', fontsize=12)
        plt.ylabel('Cumulative Return (%)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Add final return annotation
        final_return = cumulative_returns[-1]
        plt.annotate(
            f'Total: {final_return:.2f}%',
            xy=(len(cumulative_returns) - 1, final_return),
            xytext=(len(cumulative_returns) * 0.7, final_return * 1.1),
            arrowprops={'arrowstyle': '->', 'color': 'blue'},
            fontsize=10,
            fontweight='bold',
        )

        plt.tight_layout()

        if save:
            filepath = self.output_dir / f'{ticker}_cumulative_returns.png'
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None

    def plot_trade_timeline(self, ticker: str, save: bool = True) -> str | None:
        """Plot trade timeline showing entry and exit points."""
        trades = self.metrics_logger.trades
        if not trades:
            return None

        # Prepare data for timeline
        entry_times = [trade.entry_time for trade in trades]
        exit_times = [trade.exit_time for trade in trades]
        returns = [trade.return_pct * 100 for trade in trades]

        plt.figure(figsize=(15, 8))

        # Plot entry and exit points
        colors = ['green' if r > 0 else 'red' for r in returns]
        sizes = [abs(r) * 50 + 20 for r in returns]  # Size based on return magnitude

        plt.scatter(
            entry_times,
            [1] * len(entry_times),
            c=colors,
            s=sizes,
            alpha=0.7,
            label='Entry Points',
        )
        plt.scatter(
            exit_times,
            [0] * len(exit_times),
            c=colors,
            s=sizes,
            alpha=0.7,
            label='Exit Points',
        )

        # Connect entry to exit points
        for entry, exit_time, color in zip(
            entry_times, exit_times, colors, strict=False
        ):
            plt.plot([entry, exit_time], [1, 0], color=color, alpha=0.3, linewidth=1)

        plt.title(f'{ticker} Trade Timeline', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Trade Phase', fontsize=12)
        plt.yticks([0, 1], ['Exit', 'Entry'])
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Format x-axis dates
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45)

        plt.tight_layout()

        if save:
            filepath = self.output_dir / f'{ticker}_trade_timeline.png'
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None

    def create_dashboard(self, ticker: str, save: bool = True) -> str | None:
        """Create a comprehensive dashboard with multiple charts."""
        summary = self.metrics_logger.summary()
        trades = self.metrics_logger.trades

        if not trades:
            return None

        # Create dashboard with subplots
        plt.figure(figsize=(20, 12))

        # 1. Equity curve (top left)
        ax1 = plt.subplot(2, 3, 1)
        equity_curve = self.metrics_logger.get_equity_curve()
        ax1.plot(equity_curve, linewidth=2, color='blue')
        ax1.set_title('Equity Curve', fontweight='bold')
        ax1.set_xlabel('Trade Number')
        ax1.set_ylabel('Equity')
        ax1.grid(True, alpha=0.3)

        # 2. Drawdown (top middle)
        ax2 = plt.subplot(2, 3, 2)
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak * 100
        ax2.fill_between(range(len(drawdown)), drawdown, 0, alpha=0.3, color='red')
        ax2.plot(drawdown, color='red', linewidth=1)
        ax2.set_title('Drawdown', fontweight='bold')
        ax2.set_xlabel('Trade Number')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)

        # 3. Trade distribution (top right)
        ax3 = plt.subplot(2, 3, 3)
        returns = [trade.return_pct * 100 for trade in trades]
        ax3.hist(returns, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.axvline(x=0, color='red', linestyle='--', alpha=0.7)
        ax3.set_title('Trade Distribution', fontweight='bold')
        ax3.set_xlabel('Return (%)')
        ax3.set_ylabel('Frequency')
        ax3.grid(True, alpha=0.3)

        # 4. Key metrics (bottom left)
        ax4 = plt.subplot(2, 3, 4)
        ax4.axis('off')
        metrics_text = f"""
        Key Metrics:

        Total Trades: {summary['total_trades']}
        Win Rate: {summary['win_rate']:.1%}
        Total Return: {summary['total_return']:.2%}
        Sharpe Ratio: {summary['sharpe_ratio']:.3f}
        Max Drawdown: {summary['max_drawdown']:.2%}
        Profit Factor: {summary['profit_factor']:.2f}
        Avg Trade Duration: {summary['avg_trade_duration']:.1f} days
        """
        ax4.text(
            0.1,
            0.9,
            metrics_text,
            transform=ax4.transAxes,
            fontsize=12,
            verticalalignment='top',
            bbox={'boxstyle': 'round', 'facecolor': 'lightblue', 'alpha': 0.8},
        )

        # 5. Monthly returns (bottom middle)
        ax5 = plt.subplot(2, 3, 5)
        monthly_returns: dict[str, list[float]] = {}
        for trade in trades:
            month_key = trade.entry_time.strftime('%Y-%m')
            if month_key not in monthly_returns:
                monthly_returns[month_key] = []
            monthly_returns[month_key].append(trade.return_pct)

        monthly_totals = {
            month: np.sum(returns) * 100 for month, returns in monthly_returns.items()
        }
        if monthly_totals:
            months = list(monthly_totals.keys())
            returns = list(monthly_totals.values())
            colors = ['red' if r < 0 else 'green' for r in returns]
            ax5.bar(range(len(months)), returns, color=colors, alpha=0.7)
            ax5.set_title('Monthly Returns', fontweight='bold')
            ax5.set_xlabel('Month')
            ax5.set_ylabel('Return (%)')
            ax5.set_xticks(range(len(months)))
            ax5.set_xticklabels(months, rotation=45)
            ax5.grid(True, alpha=0.3)

        # 6. Performance vs benchmark (bottom right)
        ax6 = plt.subplot(2, 3, 6)
        cumulative_returns = []
        total_return: float = 0.0
        for trade in trades:
            total_return += trade.return_pct
            cumulative_returns.append(total_return * 100)

        ax6.plot(cumulative_returns, linewidth=2, color='blue', label='Strategy')
        ax6.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='Benchmark')
        ax6.set_title('Cumulative Returns', fontweight='bold')
        ax6.set_xlabel('Trade Number')
        ax6.set_ylabel('Return (%)')
        ax6.legend()
        ax6.grid(True, alpha=0.3)

        plt.suptitle(f'{ticker} Backtesting Dashboard', fontsize=16, fontweight='bold')
        plt.tight_layout()

        if save:
            filepath = self.output_dir / f'{ticker}_dashboard.png'
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            return None
