import time
from typing import List, Optional

from src.config.models import LootConfig
from src.domain.actions import ActionPriority, ActionType, BotAction, KeyPayload
from src.domain.game_state import GameState
from src.utils.logger import logger


class AutoLootController:
    """
    Propõe ações de Quick Loot Nearby Corpses.

    O módulo não envia inputs diretamente. Ele apenas cria BotAction.
    """

    def __init__(self, config: Optional[LootConfig] = None):
        self.config = config or LootConfig()
        self.enabled = False

        self.target_missing_since: Optional[float] = None
        self.loot_pending = False
        self.loot_requested_for_current_target = False

    def start(self) -> None:
        if not self.config.enabled:
            self.enabled = False
            logger.log(
                "LOOT",
                "Modulo de Auto-Loot desativado na configuracao.",
            )
            return

        self.enabled = True
        self._reset_combat_state()

        logger.log(
            "LOOT",
            "Modulo de Auto-Loot ativado.",
        )

    def stop(self) -> None:
        self.enabled = False
        self._reset_combat_state()

        logger.log(
            "LOOT",
            "Modulo de Auto-Loot desativado.",
        )

    def get_proposed_actions(
        self,
        current_state: GameState,
        previous_state: Optional[GameState] = None,
    ) -> List[BotAction]:
        if not self.enabled or not self.config.enabled:
            self._cancel_pending()
            return []

        if not current_state.is_safe_to_act:
            self._cancel_pending()
            return []

        if current_state.player.in_protection_zone is True:
            self._cancel_pending()
            return []

        if self._requires_emergency_heal(current_state):
            self._cancel_pending()
            return []

        has_active_target = (
            current_state.target.has_active_target
        )

        # Um novo alvo ficou ativo. Inicia um novo ciclo de combate.
        if has_active_target is True:
            self._reset_combat_state()
            return []

        if previous_state is None:
            return []

        target_was_active = (
            previous_state.target.has_active_target is True
        )

        target_is_inactive = (
            current_state.target.has_active_target is False
        )

        # A transição só serve para iniciar o estado pendente.
        if (
            target_was_active
            and target_is_inactive
            and not self.loot_requested_for_current_target
        ):
            self.loot_pending = True
            self.target_missing_since = time.monotonic()

            logger.log(
                "LOOT",
                "Alvo deixou de estar ativo. Loot pendente.",
                level="INFO",
            )

            return []

        # A partir daqui, não dependemos mais da transição.
        if not self.loot_pending:
            return []

        # Se a detecção ficou indeterminada, não executar.
        if current_state.target.has_active_target is None:
            self._cancel_pending()
            return []

        if (
            self.config.require_empty_battle_list
            and current_state.target.has_monsters_in_battle
            is not False
        ):
            return []

        if self.target_missing_since is None:
            self._cancel_pending()
            return []

        elapsed_ms = (
            time.monotonic() - self.target_missing_since
        ) * 1000.0

        if elapsed_ms < self.config.delay_ms:
            return []

        self.loot_pending = False
        self.target_missing_since = None
        self.loot_requested_for_current_target = True

        logger.log(
            "LOOT",
            (
                "Solicitando Quick Loot "
                f"({self.config.nearby_corpses_key})"
            ),
            level="ACTION",
        )

        return [
            BotAction(
                action_type=ActionType.LOOT_NEARBY,
                priority=ActionPriority.LOOT,
                payload=KeyPayload(self.config.nearby_corpses_key),
                reason=(
                    "Alvo anteriormente ativo deixou de existir; "
                    "executando Quick Loot Nearby Corpses."
                ),
                cooldown_ms=self.config.cooldown_ms,
                cooldown_key="loot:nearby",
            )
        ]

    def _requires_emergency_heal(
        self,
        game_state: GameState,
    ) -> bool:
        hp_percent = game_state.player.hp_percent

        if hp_percent is None:
            return False

        hp_percent_100 = hp_percent * 100.0

        return (
            hp_percent_100
            <= self.config.emergency_hp_threshold
        )

    def _cancel_pending(self) -> None:
        self.loot_pending = False
        self.target_missing_since = None

    def _reset_combat_state(self) -> None:
        self.loot_pending = False
        self.target_missing_since = None
        self.loot_requested_for_current_target = False
