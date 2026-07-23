import time
from typing import Optional, List

from src.config.models import LootConfig
from src.domain.game_state import GameState
from src.domain.actions import BotAction, ActionType
from src.utils.logger import logger


class AutoLootController:
    """
    Módulo responsável por propor ações de Auto-Loot via Quick Loot Nearby Corpses.
    É um módulo declarativo puro: não executa inputs diretamente e não altera cooldowns de hardware.
    """

    def __init__(self, config: Optional[LootConfig] = None):
        self.config = config or LootConfig()
        self.enabled = False
        self.target_missing_since: Optional[float] = None
        self.loot_requested_for_current_target: bool = False

    def start(self):
        """Inicia o módulo de loot se ativado na configuração."""
        if not self.config.enabled:
            logger.log("LOOT", "Modulo de Auto-Loot desativado na configuracao.")
            self.enabled = False
            return

        self.enabled = True
        self.target_missing_since = None
        self.loot_requested_for_current_target = False
        logger.log("LOOT", "Modulo de Auto-Loot ativado.")

    def stop(self):
        """Para o módulo de loot."""
        self.enabled = False
        self.target_missing_since = None
        self.loot_requested_for_current_target = False
        logger.log("LOOT", "Modulo de Auto-Loot desativado.")

    def get_proposed_actions(
        self,
        current_state: GameState,
        previous_state: Optional[GameState] = None
    ) -> List[BotAction]:
        """
        Avalia o GameState atual e anterior e retorna intenções de loot (BotAction).
        Não executa inputs diretamente nem altera timestamps de cooldown.
        """
        if not self.enabled or not self.config.enabled or not current_state.is_safe_to_act:
            self._cancel_pending()
            return []

        # Cancelar se em Protection Zone
        if current_state.player.in_protection_zone:
            self._cancel_pending()
            return []

        # Cancelar se cura de emergência for necessária
        if current_state.player.hp_percent is not None:
            hp_pct_100 = current_state.player.hp_percent * 100.0
            if hp_pct_100 <= self.config.emergency_hp_threshold:
                self._cancel_pending()
                return []

        # Se há um alvo ativo no ciclo atual, reseta o estado de loot do alvo anterior
        if current_state.target.has_active_target:
            self.loot_requested_for_current_target = False
            self.target_missing_since = None
            return []

        if previous_state is None:
            return []

        # Verificar se ocorreu a transição: havia alvo ativo no ciclo anterior, e agora não há
        target_was_active = previous_state.target.has_active_target is True
        target_is_inactive = current_state.target.has_active_target is False

        if not target_was_active or not target_is_inactive:
            return []

        # Se o loot já foi solicitado para este alvo derrotado
        if self.loot_requested_for_current_target:
            return []

        # Se exige Battle List vazia e ainda há monstros na Battle List
        if self.config.require_empty_battle_list and current_state.target.has_monsters_in_battle is not False:
            return []

        now = time.monotonic()
        if self.target_missing_since is None:
            self.target_missing_since = now
            return []

        elapsed_ms = (now - self.target_missing_since) * 1000.0
        if elapsed_ms < self.config.delay_ms:
            return []

        self.loot_requested_for_current_target = True
        self.target_missing_since = None

        logger.log("LOOT", f"Solicitando Quick Loot ({self.config.nearby_corpses_key})", level="ACTION")

        return [
            BotAction(
                action_type=ActionType.LOOT_NEARBY,
                priority=self.config.priority,
                key=self.config.nearby_corpses_key,
                reason="Alvo ativamente travado deixou de existir (Quick Loot)",
                cooldown_ms=self.config.cooldown_ms,
            )
        ]

    def _cancel_pending(self):
        self.target_missing_since = None
