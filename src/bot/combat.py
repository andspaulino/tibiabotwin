import time
from typing import Optional

from src.config.models import CombatConfig
from src.utils.input import press_key
from src.utils.screen import has_monsters_in_battle, has_active_target
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

    def update(self, img_bgr, in_pz: bool = False):
        """
        Lógica de combate leve e orientada a eventos (sem spam no log).
        """
        if not self.enabled or not self.config.enabled or in_pz:
            self.had_target_last_check = False
            self.had_monsters_last_check = False
            return

        now = time.time()
        has_target = has_active_target(
            img_bgr,
            target_template_path=self.config.target_template_path,
            threshold=self.config.target_match_threshold
        )
        has_monsters = has_monsters_in_battle(
            img_bgr,
            min_pixels=self.config.min_battle_pixels
        )

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
