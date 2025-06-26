from typing import List, Dict

class MetricsLogger:
    """
    Aggregates return percentages and provides summary statistics.
    """
    def __init__(self):
        self.returns: List[float] = []

    def record(self, return_pct: float) -> None:
        """Add a realized return percentage from one trade."""
        self.returns.append(return_pct)

    def summary(self) -> Dict[str, float]:
        """
        Compute summary metrics:
          - trades: total number of trades
          - avg_return: mean return
          - win_rate: proportion of positive returns
          - max_return: highest return
          - min_return: lowest return
        """
        if not self.returns:
            return {"trades": 0, "avg_return": 0.0, "win_rate": 0.0,
                    "max_return": 0.0, "min_return": 0.0}

        trades = len(self.returns)
        avg_return = sum(self.returns) / trades
        win_rate = sum(1 for r in self.returns if r > 0) / trades
        max_return = max(self.returns)
        min_return = min(self.returns)

        return {
            "trades": trades,
            "avg_return": avg_return,
            "win_rate": win_rate,
            "max_return": max_return,
            "min_return": min_return,
        }
