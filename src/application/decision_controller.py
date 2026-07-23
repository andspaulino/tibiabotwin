import time
from typing import List, Optional

from src.config.models import AppConfig
from src.domain.game_state import GameState
from src.domain.bot_state import BotState, BotMode
from src.domain.actions import BotAction, ActionType
from src.application.cooldown_manager import CooldownManager
from src.utils.logger import logger


class DecisionController:
    """
    Resolvedor central de conflitos, prioridades e compatibilidade de ações do bot.
    Recebe intenções de ações propostas pelos módulos e filtra apenas as autorizadas e compatíveis com cooldowns.
    """

    def __init__(self, cooldown_manager: Optional[CooldownManager] = None):
        self.cooldown_manager = cooldown_manager or CooldownManager()

    def _get_cooldown_ms(self, action: BotAction, config: Optional[AppConfig]) -> float:
        if action.cooldown_ms > 0:
            return float(action.cooldown_ms)

        if not config:
            return 0.0

        if action.action_type == ActionType.EMERGENCY_HEAL:
            return float(config.healer.emergency_potion.cooldown_ms)
        elif action.action_type == ActionType.HEAL:
            return float(config.healer.spell.cooldown_ms)
        elif action.action_type == ActionType.USE_MANA:
            return float(config.healer.mana_potion.cooldown_ms)
        elif action.action_type == ActionType.ATTACK:
            return float(config.combat.attack_cooldown_ms)
        elif action.action_type in (ActionType.LOOT, ActionType.LOOT_NEARBY):
            return float(config.loot.cooldown_ms)
        return 0.0

    def resolve(
        self,
        proposed_actions: List[BotAction],
        game_state: GameState,
        bot_state: BotState,
        config: Optional[AppConfig] = None
    ) -> List[BotAction]:
        """
        Ordena, valida cooldowns e resolve conflitos entre ações propostas.
        Limita o resultado a no máximo uma ação por ciclo (a de maior prioridade válida).
        """
        if not proposed_actions:
            return []

        # 1. Trava de segurança: Se o estado for inseguro ou pausado, rejeita todas as ações
        if not game_state.is_safe_to_act or bot_state.current_mode in (BotMode.PAUSED, BotMode.UNSAFE, BotMode.STOPPED):
            return []

        # 2. Ordena por prioridade (menor número = maior prioridade)
        sorted_actions = sorted(proposed_actions, key=lambda act: act.priority)
        now = time.time()

        for action in sorted_actions:
            # 3. Regra de Protection Zone: Nenhuma ação ofensiva, de loot ou de movimentação em PZ
            if bot_state.current_mode == BotMode.IN_PROTECTION_ZONE:
                if action.action_type in (ActionType.ATTACK, ActionType.LOOT, ActionType.LOOT_NEARBY, ActionType.MOVE):
                    continue

            # 4. Verifica se a ação respeita o CooldownManager
            cd_ms = self._get_cooldown_ms(action, config)
            if not self.cooldown_manager.can_execute(action.action_type, cd_ms, now):
                continue
            if action.key and not self.cooldown_manager.can_execute(action.key, cd_ms, now):
                continue

            # Retorna imediatamente a primeira ação válida encontrada (a de maior prioridade)
            return [action]

        return []
