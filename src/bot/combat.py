import time
from typing import Optional, Union, Dict, Any

from src.config.models import CombatConfig
from src.domain.game_state import GameState
from src.domain.roi import RelativeROI, AbsoluteROI
from src.utils.input import press_key
from src.utils.screen import has_monsters_in_battle, has_active_target, BATTLE_LIST_ROI
from src.utils.logger import logger


class AutoAttacker:
    """Módulo responsável por detectar alvos na Battle List e acionar o ataque automático."""

    def __init__(self, config: Optional[CombatConfig] = None):
        self.config = config or CombatConfig()
        self.last_attack_time = 0.0
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

    def update(
        self,
        state_or_img: Union[GameState, Any],
        in_pz: bool = False,
        roi: Union[RelativeROI, AbsoluteROI, Dict[str, Any]] = BATTLE_LIST_ROI
    ):
        """
        Lógica de combate leve e orientada a eventos (sem spam no log).
        Pode receber um GameState imutável ou uma imagem BGR direta.
        """
        if not self.enabled or not self.config.enabled:
            self.had_target_last_check = False
            self.had_monsters_last_check = False
            return

        if isinstance(state_or_img, GameState):
            state = state_or_img
            if not state.is_safe_to_act or state.player.in_protection_zone:
                self.had_target_last_check = False
                self.had_monsters_last_check = False
                return

            if state.target.has_active_target is None or state.target.has_monsters_in_battle is None:
                return

            has_target = state.target.has_active_target
            has_monsters = state.target.has_monsters_in_battle
        else:
            img_bgr = state_or_img
            if in_pz:
                self.had_target_last_check = False
                self.had_monsters_last_check = False
                return

            has_target = has_active_target(
                img_bgr,
                roi=roi,
                target_template_path=self.config.target_template_path,
                threshold=self.config.target_match_threshold
            )
            has_monsters = has_monsters_in_battle(
                img_bgr,
                roi=roi,
                min_pixels=self.config.min_battle_pixels
            )

        now = time.time()

        # 1. Alvo ativo selecionado (moldura de ataque vermelha)
        if has_target:
            if not self.had_target_last_check:
                logger.log("COMBAT", "Alvo travado", level="ACTION")
            self.had_target_last_check = True
            self.had_monsters_last_check = True
            return

        self.had_target_last_check = False

        # 2. Se há monstros na Battle List mas sem alvo travado
        attack_cd_sec = self.config.attack_cooldown_ms / 1000.0
        if has_monsters:
            if now - self.last_attack_time >= attack_cd_sec:
                # Loga apenas na primeira detecção de combate ou troca de alvo
                if not self.had_monsters_last_check:
                    logger.log("COMBAT", "Atacando inimigo", level="ACTION")
                press_key(self.config.attack_key)
                self.last_attack_time = now
            self.had_monsters_last_check = True
        else:
            if self.had_monsters_last_check:
                logger.log("COMBAT", "Batalha encerrada", level="INFO")
            self.had_monsters_last_check = False
