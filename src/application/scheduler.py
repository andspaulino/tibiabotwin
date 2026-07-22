import time


class LoopScheduler:
    """
    Controlador de tempo e frequência de loop do bot.
    Garante a execução no intervalo configurado (FPS target) e calcula métricas por ciclo.
    """

    def __init__(self, target_interval_ms: float = 100.0):
        self.target_interval_ms = target_interval_ms
        self.total_cycles: int = 0
        self.last_cycle_time_ms: float = 0.0

    def tick(self, cycle_start_perf: float) -> float:
        """
        Calcula o tempo decorrido no ciclo e realiza o sleep apropriado para manter o ritmo.
        Retorna o tempo total do ciclo em milissegundos.
        """
        elapsed_sec = time.perf_counter() - cycle_start_perf
        self.last_cycle_time_ms = elapsed_sec * 1000.0
        self.total_cycles += 1

        target_sleep_sec = max(0.0, (self.target_interval_ms / 1000.0) - elapsed_sec)
        if target_sleep_sec > 0:
            time.sleep(target_sleep_sec)

        return self.last_cycle_time_ms

    @property
    def average_fps(self) -> float:
        """Retorna o FPS estimado do loop com base no último tempo de ciclo."""
        if self.last_cycle_time_ms <= 0:
            return 0.0
        return 1000.0 / max(1.0, self.last_cycle_time_ms)
