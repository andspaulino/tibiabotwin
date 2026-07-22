import time
from typing import Dict, Union, Optional

from src.domain.actions import ActionType


class CooldownManager:
    """
    Gerenciador centralizado de cooldowns.
    Garante que os timestamps de execução sejam atualizados EXCLUSIVAMENTE
    após a ação ter sido autorizada e enviada ao hardware com sucesso.
    """

    def __init__(self):
        self.last_execution_times: Dict[Union[ActionType, str], float] = {}

    def can_execute(self, key_or_action: Union[ActionType, str], cooldown_ms: float, now: Optional[float] = None) -> bool:
        """
        Verifica se o tempo decorrido desde a última execução confirmada respeita o cooldown configurado.
        """
        if cooldown_ms <= 0:
            return True

        current_time = now if now is not None else time.time()
        last_time = self.last_execution_times.get(key_or_action, 0.0)
        cooldown_sec = cooldown_ms / 1000.0

        return (current_time - last_time) >= cooldown_sec

    def register_execution(self, key_or_action: Union[ActionType, str], now: Optional[float] = None) -> None:
        """
        Registra o momento em que a ação foi enviada fisicamente com sucesso.
        """
        current_time = now if now is not None else time.time()
        self.last_execution_times[key_or_action] = current_time
