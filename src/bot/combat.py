import time
from src.utils.input import press_key
from src.utils.humanizer import gaussian_delay
from src.utils.screen import has_monsters_in_battle, has_active_target
from src.utils.logger import logger

class AutoAttacker:
    """Módulo responsável por detectar alvos na Battle List e acionar o ataque automático."""

    def __init__(self, attack_key: str = 'space', attack_cooldown: float = 1.0):
        self.attack_key = attack_key
        self.attack_cooldown = attack_cooldown
        self.last_attack_time = 0
        self.enabled = False
        self.had_target_last_check = False
        self.had_monsters_last_check = False

    def start(self):
        """Inicia o módulo de ataque."""
        self.enabled = True
        logger.log("COMBAT", f"Modulo de combate ativado (Hotkey de ataque: '{self.attack_key.upper()}').")

    def stop(self):
        """Para o módulo de ataque."""
        self.enabled = False
        logger.log("COMBAT", "Modulo de combate desativado.")

    def update(self, img_bgr, in_pz: bool = False):
        """
        Lógica de combate executada continuamente no loop principal.
        Emite logs estritamente orientados a eventos/ações (sem spam).
        """
        if not self.enabled or in_pz:
            self.had_target_last_check = False
            self.had_monsters_last_check = False
            return

        now = time.time()
        
        has_target = has_active_target(img_bgr)
        has_monsters = has_monsters_in_battle(img_bgr)

        # 1. Se existe um alvo ativo selecionado (moldura de ataque vermelha)
        if has_target:
            if not self.had_target_last_check:
                logger.log("COMBAT", "Alvo travado e sob ataque.", level="ACTION")
            self.had_target_last_check = True
            self.had_monsters_last_check = True
            return

        self.had_target_last_check = False

        # 2. Se não houver alvo ativo, verifica se há monstros presentes na Battle List
        if has_monsters:
            if now - self.last_attack_time >= self.attack_cooldown:
                logger.log("COMBAT", f"Inimigo detectado na Battle List. Atacando (HK '{self.attack_key.upper()}')...", level="ACTION")
                press_key(self.attack_key)
                self.last_attack_time = now
            self.had_monsters_last_check = True
        else:
            if self.had_monsters_last_check:
                logger.log("COMBAT", "Batalha encerrada / Nenhum inimigo na Battle List.", level="INFO")
            self.had_monsters_last_check = False
