from typing import List, Optional
import time

from src.domain.game_state import GameState
from src.domain.actions import BotAction
from src.infrastructure.input.base import InputController
from src.application.cooldown_manager import CooldownManager
from src.utils.logger import logger


class ActionExecutor:
    """
    Executor central de ações autorizadas.
    É o ÚNICO componente responsável por disparar comandos de entrada físicos através do InputController.
    Atualiza os timestamps do CooldownManager APÓS a execução confirmada com sucesso.
    """

    def __init__(self, cooldown_manager: Optional[CooldownManager] = None):
        self.cooldown_manager = cooldown_manager or CooldownManager()

    def execute(
        self,
        actions: List[BotAction],
        game_state: GameState,
        input_controller: InputController,
        observe_only: bool = False,
        cooldown_manager: Optional[CooldownManager] = None
    ) -> None:
        """
        Revalida os portões de segurança e executa cada ação autorizada.
        Registra os cooldowns após o envio físico bem sucedido.
        """
        if not actions or not game_state.is_safe_to_act:
            return

        cd_mgr = cooldown_manager or self.cooldown_manager
        now = time.time()

        for action in actions:
            if action.key:
                if observe_only:
                    logger.log("SIMULATION", f"[OBSERVE-ONLY] Acao simulada {action.action_type.value.upper()}: {action.reason}", level="ACTION")
                else:
                    input_controller.press_key(action.key)
                    logger.log("ACTION", f"Executado {action.action_type.value.upper()}: {action.reason}", level="ACTION")

                # Registra o cooldown EXCLUSIVAMENTE após o envio bem sucedido
                cd_mgr.register_execution(action.action_type, now)
                cd_mgr.register_execution(action.key, now)
