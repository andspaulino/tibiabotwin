from typing import List

from src.domain.game_state import GameState
from src.domain.actions import BotAction
from src.infrastructure.input.base import InputController
from src.utils.logger import logger


class ActionExecutor:
    """
    Executor central de ações autorizadas.
    É o ÚNICO componente responsável por disparar comandos de entrada físicos através do InputController.
    Suporta o modo de observação (--observe-only).
    """

    def execute(
        self,
        actions: List[BotAction],
        game_state: GameState,
        input_controller: InputController,
        observe_only: bool = False
    ) -> None:
        """
        Revalida os portões de segurança e executa cada ação autorizada.
        No modo observe_only, registra logs simulados sem enviar comandos de hardware.
        """
        if not actions or not game_state.is_safe_to_act:
            return

        for action in actions:
            if action.key:
                if observe_only:
                    logger.log("SIMULATION", f"[OBSERVE-ONLY] Acao simulada {action.action_type.value.upper()}: {action.reason}", level="ACTION")
                else:
                    input_controller.press_key(action.key)
                    logger.log("ACTION", f"Executado {action.action_type.value.upper()}: {action.reason}", level="ACTION")
