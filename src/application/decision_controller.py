import time
from typing import List, Optional

from src.application.cooldown_manager import CooldownManager
from src.config.models import AppConfig
from src.domain.actions import ActionType, BotAction
from src.domain.bot_state import BotMode, BotState
from src.domain.game_state import GameState


class DecisionController:
    """Resolve segurança, compatibilidade, prioridade e cooldown das intenções."""

    def __init__(self, cooldown_manager: Optional[CooldownManager] = None):
        self.cooldown_manager = cooldown_manager or CooldownManager()

    def _get_cooldown_ms(self, action: BotAction, config: Optional[AppConfig]) -> float:
        if action.cooldown_ms > 0:
            return float(action.cooldown_ms)
        if config is None:
            return 0.0
        if action.action_type == ActionType.EMERGENCY_HEAL:
            return float(config.healer.emergency_potion.cooldown_ms)
        if action.action_type == ActionType.HEAL:
            return float(config.healer.spell.cooldown_ms)
        if action.action_type == ActionType.USE_MANA:
            return float(config.healer.mana_potion.cooldown_ms)
        if action.action_type == ActionType.ATTACK:
            return float(config.combat.attack_cooldown_ms)
        if action.action_type in (ActionType.LOOT, ActionType.LOOT_NEARBY):
            return float(config.loot.cooldown_ms)
        return 0.0

    def resolve(
        self,
        proposed_actions: List[BotAction],
        game_state: GameState,
        bot_state: BotState,
        config: Optional[AppConfig] = None,
    ) -> List[BotAction]:
        """Retorna no máximo a ação válida de maior prioridade sem consumir cooldown."""
        if not proposed_actions:
            return []
        if not game_state.is_safe_to_act or bot_state.current_mode in {
            BotMode.PAUSED,
            BotMode.UNSAFE,
            BotMode.STOPPED,
        }:
            return []

        now = time.time()
        for action in sorted(proposed_actions, key=lambda act: act.priority, reverse=True):
            if bot_state.current_mode == BotMode.IN_PROTECTION_ZONE and action.action_type in {
                ActionType.ATTACK,
                ActionType.LOOT,
                ActionType.LOOT_NEARBY,
                ActionType.MOVE,
            }:
                continue

            cooldown_ms = self._get_cooldown_ms(action, config)
            cooldown_key = action.cooldown_key or action.action_type.value
            if not self.cooldown_manager.can_execute(cooldown_key, cooldown_ms, now):
                continue
            return [action]
        return []
