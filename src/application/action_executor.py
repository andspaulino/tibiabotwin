import time
from typing import Callable, List, Optional

from src.application.cooldown_manager import CooldownManager
from src.domain.actions import BotAction, KeyPayload, MouseClickPayload
from src.domain.game_state import GameState
from src.infrastructure.input.base import InputController
from src.utils.logger import logger


class ActionExecutor:
    """Único componente autorizado a transformar ações aprovadas em inputs físicos."""

    def __init__(
        self,
        input_controller: Optional[InputController] = None,
        cooldown_manager: Optional[CooldownManager] = None,
    ):
        self.input_controller = input_controller
        self.cooldown_manager = cooldown_manager or CooldownManager()

    def execute(
        self,
        actions: List[BotAction],
        game_state: GameState,
        observe_only: bool = False,
        cooldown_manager: Optional[CooldownManager] = None,
        final_validator: Callable[[BotAction], bool] | None = None,
    ) -> List[BotAction]:
        """Executa payloads aprovados e registra cooldown somente após sucesso físico."""
        if not actions or not game_state.is_safe_to_act:
            return []

        executed_actions: List[BotAction] = []
        cd_mgr = cooldown_manager or self.cooldown_manager
        for action in actions:
            if observe_only:
                logger.log(
                    "SIMULATION",
                    f"[OBSERVE-ONLY] Acao simulada {action.action_type.value.upper()}: {action.reason}",
                    level="ACTION",
                )
                continue
            if final_validator is not None and not final_validator(action):
                logger.log("ACTION", f"Descartada na validação final: {action.reason}", level="WARNING")
                continue
            if self.input_controller is None:
                logger.log("ACTION", f"Descartada sem controlador de input: {action.reason}", level="WARNING")
                continue

            try:
                if isinstance(action.payload, KeyPayload):
                    self.input_controller.press_key(action.payload.key)
                elif isinstance(action.payload, MouseClickPayload):
                    self.input_controller.click(
                        action.payload.x,
                        action.payload.y,
                        action.payload.button,
                        action.payload.return_position,
                    )
                else:
                    logger.log("ACTION", f"Payload não suportado: {action.reason}", level="WARNING")
                    continue
            except Exception as error:
                self.input_controller.release_all()
                logger.log("ACTION", f"Falha ao executar {action.action_type.value}: {error}", level="ERROR")
                continue

            cooldown_key = action.cooldown_key or action.action_type.value
            cd_mgr.register_execution(cooldown_key, time.time())
            executed_actions.append(action)
            logger.log("ACTION", f"Executado {action.action_type.value.upper()}: {action.reason}", level="ACTION")

        return executed_actions
