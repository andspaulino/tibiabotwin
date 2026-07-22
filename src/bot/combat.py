import time
from typing import Optional, Union, Dict, Any, List

from src.config.models import CombatConfig
from src.domain.game_state import GameState
from src.domain.roi import RelativeROI, AbsoluteROI
from src.domain.actions import BotAction, ActionType
from src.utils.screen import BATTLE_LIST_ROI
from src.utils.logger import logger


class AutoAttacker:
    """
    Módulo responsável por detectar alvos na Battle List e propor ações de ataque.
    É um módulo declarativo puro: não executa inputs diretamente e não altera cooldowns de hardware.
    """

    def __init__(self, config: Optional[CombatConfig] = None):
        self.config = config or CombatConfig()
        self.enabled = False
        self.had_target_last_check = False
        self.had_monsters_last_check = False

    def start(self):
        """Inicia o módulo de ataque se ativado na configuração."""
        if not self.config.enabled:
            logger.log("COMBAT", "Modulo de ataque desativado na configuracao.")
            self.enabled = False
            return

        self.enabled = True
        logger.log("COMBAT", "Modulo de ataque ativado.")

    def stop(self):
        """Para o módulo de ataque."""
        self.enabled = False
        logger.log("COMBAT", "Modulo de ataque desativado.")

    def get_proposed_actions(self, game_state: GameState) -> List[BotAction]:
        """
        Avalia o GameState e retorna uma lista de intenções de ações (BotAction).
        Não executa inputs diretamente nem altera timestamps de cooldown.
        """
        if not self.enabled or not self.config.enabled or not game_state.is_safe_to_act:
            self.had_target_last_check = False
            self.had_monsters_last_check = False
            return []

        if game_state.player.in_protection_zone:
            self.had_target_last_check = False
            self.had_monsters_last_check = False
            return []

        has_target = game_state.target.has_active_target
        has_monsters = game_state.target.has_monsters_in_battle

        if has_target is None or has_monsters is None:
            return []

        actions: List[BotAction] = []

        # 1. Alvo ativo selecionado (moldura de ataque vermelha)
        if has_target:
            if not self.had_target_last_check:
                logger.log("COMBAT", "Alvo travado", level="ACTION")
            self.had_target_last_check = True
            self.had_monsters_last_check = True
            return []

        self.had_target_last_check = False

        # 2. Se há monstros na Battle List mas sem alvo travado
        if has_monsters:
            if not self.had_monsters_last_check:
                logger.log("COMBAT", "Atacando inimigo", level="ACTION")
            actions.append(
                BotAction(
                    action_type=ActionType.ATTACK,
                    priority=4,
                    key=self.config.attack_key,
                    reason="Selecao de alvo na Battle List"
                )
            )
            self.had_monsters_last_check = True
        else:
            if self.had_monsters_last_check:
                logger.log("COMBAT", "Batalha encerrada", level="INFO")
            self.had_monsters_last_check = False

        return actions

    def update(
        self,
        state_or_img: Union[GameState, Any],
        in_pz: bool = False,
        roi: Union[RelativeROI, AbsoluteROI, Dict[str, Any]] = BATTLE_LIST_ROI
    ) -> List[BotAction]:
        """Método legado para compatibilidade direta. Retorna intenções sem disparar inputs."""
        if isinstance(state_or_img, GameState):
            return self.get_proposed_actions(state_or_img)
        return []
