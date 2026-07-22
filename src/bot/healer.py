import time
from typing import Optional

from src.config.models import HealerConfig
from src.utils.input import press_key
from src.utils.logger import logger


class AutoHealer:
    """Módulo responsável pelo monitoramento e execução da cura automática de HP e Mana."""

    def __init__(self, config: Optional[HealerConfig] = None):
        self.config = config or HealerConfig()
        
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

    def check_and_heal(self, current_hp_pct: float, current_mp_pct: float, in_pz: bool = False):
        """
        Verifica as porcentagens atuais de HP e MP e aciona as hotkeys configuradas.
        - current_hp_pct e current_mp_pct estão na faixa de 0.0 a 1.0.
        - As configurações hp_below / mana_below estão na faixa de 0.0 a 100.0.
        """
        if not self.enabled or not self.config.enabled or in_pz:
            return

        # Ignora frames não inicializados ou capturas pretas
        if current_hp_pct <= 0.0 and current_mp_pct <= 0.0:
            return

        now = time.time()
        hp_pct_100 = current_hp_pct * 100.0
        mp_pct_100 = current_mp_pct * 100.0

        # 1. EMERGÊNCIA: Poção de Vida
        emerg_cfg = self.config.emergency_potion
        if emerg_cfg.enabled and hp_pct_100 <= emerg_cfg.hp_below:
            cd_sec = emerg_cfg.cooldown_ms / 1000.0
            if now - self.last_emergency_potion_time >= cd_sec:
                logger.log("HEALER", f"Pocao de Vida ({hp_pct_100:.0f}%)", level="WARNING")
                press_key(emerg_cfg.key)
                self.last_emergency_potion_time = now
                return

        # 2. CURA PRIMÁRIA: Magia de Cura
        spell_cfg = self.config.spell
        if spell_cfg.enabled and hp_pct_100 <= spell_cfg.hp_below:
            cd_sec = spell_cfg.cooldown_ms / 1000.0
            if now - self.last_spell_time >= cd_sec:
                press_key(spell_cfg.key)
                self.last_spell_time = now

        # 3. MANA: Poção de Mana
        mana_cfg = self.config.mana_potion
        if mana_cfg.enabled and mp_pct_100 <= mana_cfg.threshold_below:
            cd_sec = mana_cfg.cooldown_ms / 1000.0
            if now - self.last_mana_potion_time >= cd_sec:
                press_key(mana_cfg.key)
                self.last_mana_potion_time = now
