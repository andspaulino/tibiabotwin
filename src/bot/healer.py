import time
from typing import Optional, Union, List

from src.config.models import HealerConfig
from src.domain.game_state import GameState
from src.domain.actions import BotAction, ActionType
from src.infrastructure.input import InputController
from src.infrastructure.factory import create_input_controller
from src.utils.logger import logger


class AutoHealer:
    """Módulo responsável pelo monitoramento e proposição de ações de cura de HP e Mana."""

    def __init__(
        self,
        config: Optional[HealerConfig] = None,
        input_controller: Optional[InputController] = None
    ):
        self.config = config or HealerConfig()
        self.input_controller = input_controller or create_input_controller()
        
        self.last_spell_time = 0.0
        self.last_mana_potion_time = 0.0
        self.last_emergency_potion_time = 0.0
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
        Não executa inputs diretamente.
        """
        if not self.enabled or not self.config.enabled or not game_state.is_safe_to_act:
            return []

        if game_state.player.in_protection_zone:
            return []

        hp_pct = game_state.player.hp_percent
        mp_pct = game_state.player.mana_percent

        if hp_pct is None or mp_pct is None or (hp_pct <= 0.0 and mp_pct <= 0.0):
            return []

        now = time.time()
        actions: List[BotAction] = []
        hp_pct_100 = hp_pct * 100.0
        mp_pct_100 = mp_pct * 100.0

        # 1. EMERGÊNCIA: Poção de Vida
        emerg_cfg = self.config.emergency_potion
        if emerg_cfg.enabled and hp_pct_100 <= emerg_cfg.hp_below:
            cd_sec = emerg_cfg.cooldown_ms / 1000.0
            if now - self.last_emergency_potion_time >= cd_sec:
                actions.append(
                    BotAction(
                        action_type=ActionType.EMERGENCY_HEAL,
                        priority=1,
                        key=emerg_cfg.key,
                        reason=f"Pocao de Vida ({hp_pct_100:.0f}%)"
                    )
                )
                self.last_emergency_potion_time = now
                return actions

        # 2. CURA PRIMÁRIA: Magia de Cura
        spell_cfg = self.config.spell
        if spell_cfg.enabled and hp_pct_100 <= spell_cfg.hp_below:
            cd_sec = spell_cfg.cooldown_ms / 1000.0
            if now - self.last_spell_time >= cd_sec:
                actions.append(
                    BotAction(
                        action_type=ActionType.HEAL,
                        priority=2,
                        key=spell_cfg.key,
                        reason=f"Magia de Cura ({hp_pct_100:.0f}%)"
                    )
                )
                self.last_spell_time = now

        # 3. MANA: Poção de Mana
        mana_cfg = self.config.mana_potion
        if mana_cfg.enabled and mp_pct_100 <= mana_cfg.threshold_below:
            cd_sec = mana_cfg.cooldown_ms / 1000.0
            if now - self.last_mana_potion_time >= cd_sec:
                actions.append(
                    BotAction(
                        action_type=ActionType.USE_MANA,
                        priority=3,
                        key=mana_cfg.key,
                        reason=f"Pocao de Mana ({mp_pct_100:.0f}%)"
                    )
                )
                self.last_mana_potion_time = now

        return actions

    def check_and_heal(
        self,
        state_or_hp: Union[GameState, float],
        current_mp_pct: Optional[float] = None,
        in_pz: bool = False
    ):
        """Método legado para compatibilidade direta."""
        if isinstance(state_or_hp, GameState):
            actions = self.get_proposed_actions(state_or_hp)
            for act in actions:
                if act.key:
                    self.input_controller.press_key(act.key)
