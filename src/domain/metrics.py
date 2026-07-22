from dataclasses import dataclass


@dataclass(frozen=True)
class CycleMetrics:
    """Métricas de desempenho e telemetria de um ciclo do bot."""
    capture_time_ms: float
    analyze_time_ms: float
    decision_time_ms: float
    total_cycle_time_ms: float
    consecutive_failures: int = 0
    valid_frame_rate: float = 1.0
