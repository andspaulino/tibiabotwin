import time
from typing import List, Dict

from src.domain.game_state import GameState
from src.domain.bot_state import BotState, BotMode
from src.domain.actions import BotAction, ActionType
from src.utils.logger import logger


class DecisionController:
    """
    Resolvedor central de conflitos e prioridades de ações do bot.
    Recebe intenções de ações propostas pelos módulos e filtra apenas as autorizadas e compatíveis.
    """

    def __init__(self):
        self.last_action_times: Dict[ActionType, float] = {}

    def resolve(
        self,
        proposed_actions: List[BotAction],
        game_state: GameState,
        bot_state: BotState
    ) -> List[BotAction]:
        """
        Ordena, valida e resolve conflitos entre ações propostas.
        """
        if not proposed_actions:
            return []

        # 1. Trava de segurança: Se o estado for inseguro ou pausado, rejeita todas as ações
        if not game_state.is_safe_to_act or bot_state.current_mode in (BotMode.PAUSED, BotMode.UNSAFE, BotMode.STOPPED):
            return []

        # 2. Ordena por prioridade (menor número = maior prioridade)
        sorted_actions = sorted(proposed_actions, key=lambda act: act.priority)
        resolved: List[BotAction] = []
        now = time.time()

        for action in sorted_actions:
            # 3. Regra de Protection Zone: Nenhuma ação ofensiva ou de movimentação em PZ
            if bot_state.current_mode == BotMode.IN_PROTECTION_ZONE:
                if action.action_type in (ActionType.ATTACK, ActionType.LOOT, ActionType.MOVE):
                    continue

            # 4. Ação de emergência (EMERGENCY_HEAL) se selecionada, cancela ações secundárias de menor prioridade
            if action.action_type == ActionType.EMERGENCY_HEAL:
                resolved = [action]
                break

            resolved.append(action)

        return resolved
