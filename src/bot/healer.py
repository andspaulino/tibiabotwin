import time
from src.utils.input import press_key

class AutoHealer:
    """Módulo responsável pelo monitoramento e execução da cura automática de HP e Mana."""

    def __init__(self, hp_threshold: float = 0.8, mp_threshold: float = 0.5):
        self.hp_threshold = hp_threshold
        self.mp_threshold = mp_threshold
        self.enabled = False

    def start(self):
        """Inicia o módulo de cura."""
        self.enabled = True
        print("[AutoHealer] Módulo ativado.")

    def stop(self):
        """Para o módulo de cura."""
        self.enabled = False
        print("[AutoHealer] Módulo desativado.")

    def check_and_heal(self, current_hp_pct: float, current_mp_pct: float):
        """
        Verifica as porcentagens atuais de HP e MP e aciona as hotkeys correspondentes.
        """
        if not self.enabled:
            return

        # Ignora frames não inicializados ou capturas pretas
        if current_hp_pct <= 0.0 and current_mp_pct <= 0.0:
            return

        if current_hp_pct < self.hp_threshold:
            print(f"[AutoHealer] HP baixo ({current_hp_pct * 100:.1f}%). Curando...")
            press_key('f1') # Exemplo de tecla para magia de cura
        elif current_mp_pct < self.mp_threshold:
            print(f"[AutoHealer] MP baixo ({current_mp_pct * 100:.1f}%). Usando poção...")
            press_key('f2') # Exemplo de tecla para poção de mana
