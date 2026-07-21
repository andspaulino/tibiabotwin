import time
from src.utils.input import press_key
from src.utils.logger import logger

class AutoHealer:
    """Módulo responsável pelo monitoramento e execução da cura automática de HP e Mana."""

    def __init__(
        self,
        spell_hp_threshold: float = 0.90,     # Magia de Cura (HK 1) se HP <= 90%
        potion_hp_threshold: float = 0.30,    # Poção de Vida (HK 3) se HP <= 30%
        mp_threshold: float = 0.50,           # Poção de Mana (HK 2) se MP <= 50%
        spell_cooldown: float = 1.0,          # Cooldown de magia (segundos)
        potion_cooldown: float = 1.0          # Cooldown de poção (segundos)
    ):
        self.spell_hp_threshold = spell_hp_threshold
        self.potion_hp_threshold = potion_hp_threshold
        self.mp_threshold = mp_threshold
        self.spell_cooldown = spell_cooldown
        self.potion_cooldown = potion_cooldown
        
        self.last_spell_time = 0
        self.last_potion_time = 0
        self.enabled = False

    def start(self):
        """Inicia o módulo de cura."""
        self.enabled = True
        logger.log("HEALER", "Modulo de cura ativado (HK 1: Magia HP <= 90%, HK 3: Pocao HP <= 30%, HK 2: Mana MP <= 50%).")

    def stop(self):
        """Para o módulo de cura."""
        self.enabled = False
        logger.log("HEALER", "Modulo de cura desativado.")

    def check_and_heal(self, current_hp_pct: float, current_mp_pct: float, in_pz: bool = False):
        """
        Verifica as porcentagens atuais de HP e MP e aciona as hotkeys correspondentes.
        """
        if not self.enabled or in_pz:
            return

        # Ignora frames não inicializados ou capturas pretas
        if current_hp_pct <= 0.0 and current_mp_pct <= 0.0:
            return

        now = time.time()

        # 1. EMERGÊNCIA: Poção de Vida (Hotkey 3) se HP <= 30%
        if current_hp_pct <= self.potion_hp_threshold:
            if now - self.last_potion_time >= self.potion_cooldown:
                logger.log("HEALER", f"[!] Vida CRITICA em {current_hp_pct * 100:.1f}% (<= {self.potion_hp_threshold * 100:.0f}%). Usando Pocao de Vida (HK 3)!", level="WARNING")
                press_key('3')
                self.last_potion_time = now
                return

        # 2. CURA PRIMÁRIA: Magia de Cura (Hotkey 1) se HP <= 90%
        if current_hp_pct <= self.spell_hp_threshold:
            if now - self.last_spell_time >= self.spell_cooldown:
                logger.log("HEALER", f"[+] Vida em {current_hp_pct * 100:.1f}% (<= {self.spell_hp_threshold * 100:.0f}%). Usando Magia de Cura (HK 1).", level="ACTION")
                press_key('1')
                self.last_spell_time = now

        # 3. MANA: Poção de Mana (Hotkey 2) se MP <= 50%
        if current_mp_pct <= self.mp_threshold:
            if now - self.last_potion_time >= self.potion_cooldown:
                logger.log("HEALER", f"[*] Mana em {current_mp_pct * 100:.1f}% (<= {self.mp_threshold * 100:.0f}%). Usando Pocao de Mana (HK 2).", level="ACTION")
                press_key('2')
                self.last_potion_time = now
