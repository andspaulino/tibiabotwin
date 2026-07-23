import time


class LoopScheduler:
    """
    Controlador de tempo e frequência de loop do bot.
    Garante a execução no intervalo configurado (FPS target) e calcula métricas por ciclo.
    """

    def __init__(self, target_interval_ms: float = 100.0):
        self.target_interval_ms = target_interval_ms
        self.total_cycles: int = 0
        self.last_processing_time_ms: float = 0.0
        self.last_cycle_time_ms: float = 0.0

    def tick(self, cycle_start_perf: float) -> float:
        """
        Calcula o tempo decorrido no ciclo, realiza o sleep apropriado para manter o ritmo,
        e registra os tempos de processamento e ciclo total.
        Retorna o tempo total do ciclo (incluindo sleep) em milissegundos.
        """
        processing_elapsed = time.perf_counter() - cycle_start_perf
        self.last_processing_time_ms = processing_elapsed * 1000.0

        target_sleep_sec = max(0.0, (self.target_interval_ms / 1000.0) - processing_elapsed)
        if target_sleep_sec > 0:
            time.sleep(target_sleep_sec)

        full_cycle_elapsed = time.perf_counter() - cycle_start_perf
        self.last_cycle_time_ms = full_cycle_elapsed * 1000.0
        self.total_cycles += 1

        return self.last_cycle_time_ms

    @property
    def average_fps(self) -> float:
        """Retorna o FPS real do loop com base no tempo total do último ciclo completo (incluindo sleep)."""
        if self.last_cycle_time_ms <= 0:
            return 0.0
        return 1000.0 / self.last_cycle_time_ms
