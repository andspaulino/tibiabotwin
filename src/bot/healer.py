import time
from typing import Optional, Union, List

from src.config.models import HealerConfig
from src.domain.game_state import GameState
from src.domain.actions import BotAction, ActionType
from src.utils.logger import logger


class AutoHealer:
    """
    Módulo responsável pela avaliação e proposição de intenções de cura de HP e Mana.
    É um módulo declarativo puro: não executa inputs diretamente e não atualiza cooldowns de hardware.
    """

    def __init__(self, config: Optional[HealerConfig] = None):
        self.config = config or HealerConfig()
        self.enabled = False

    def start(self):
        """Inicia o módulo de cura se ativado na configuração."""
        if not self.config.enabled:
            logger.log("HEALER", "Modulo de cura desativado na configuracao.")
            self.enabled = False
            return
        
        self.enabled = True
        logger.log("HEALER", "Modulo de cura ativado.")

    def stop(self):
        """Para o módulo de cura."""
        self.enabled = False
        logger.log("HEALER", "Modulo de cura desativado.")

    def get_proposed_actions(self, game_state: GameState) -> List[BotAction]:
        """
        Avalia o GameState e retorna uma lista de intenções de ações (BotAction).
        Não executa inputs diretamente nem altera timestamps de cooldown.
        """
        if not self.enabled or not self.config.enabled or not game_state.is_safe_to_act:
            return []

        if game_state.player.in_protection_zone:
            return []

        hp_pct = game_state.player.hp_percent
        mp_pct = game_state.player.mana_percent

        if hp_pct is None or mp_pct is None or (hp_pct <= 0.0 and mp_pct <= 0.0):
            return []

        actions: List[BotAction] = []
        hp_pct_100 = hp_pct * 100.0
        mp_pct_100 = mp_pct * 100.0

        # 1. EMERGÊNCIA: Poção de Vida
        emerg_cfg = self.config.emergency_potion
        if emerg_cfg.enabled and hp_pct_100 <= emerg_cfg.hp_below:
            actions.append(
                BotAction(
                    action_type=ActionType.EMERGENCY_HEAL,
                    priority=1,
                    key=emerg_cfg.key,
                    reason=f"Pocao de Vida ({hp_pct_100:.0f}%)",
                    cooldown_ms=emerg_cfg.cooldown_ms
                )
            )
            return actions

        # 2. CURA PRIMÁRIA: Magia de Cura
        spell_cfg = self.config.spell
        if spell_cfg.enabled and hp_pct_100 <= spell_cfg.hp_below:
            actions.append(
                BotAction(
                    action_type=ActionType.HEAL,
                    priority=2,
                    key=spell_cfg.key,
                    reason=f"Magia de Cura ({hp_pct_100:.0f}%)",
                    cooldown_ms=spell_cfg.cooldown_ms
                )
            )

        # 3. MANA: Poção de Mana
        mana_cfg = self.config.mana_potion
        if mana_cfg.enabled and mp_pct_100 <= mana_cfg.threshold_below:
            actions.append(
                BotAction(
                    action_type=ActionType.USE_MANA,
                    priority=3,
                    key=mana_cfg.key,
                    reason=f"Pocao de Mana ({mp_pct_100:.0f}%)",
                    cooldown_ms=mana_cfg.cooldown_ms
                )
            )

        return actions


