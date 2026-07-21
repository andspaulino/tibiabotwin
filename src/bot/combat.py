import time
from src.utils.input import press_key
from src.utils.humanizer import gaussian_delay
from src.utils.screen import has_monsters_in_battle, has_active_target

class AutoAttacker:
    """Módulo responsável por detectar alvos na Battle List e acionar o ataque automático."""

    def __init__(self, attack_key: str = 'space', attack_cooldown: float = 1.0):
        self.attack_key = attack_key
        self.attack_cooldown = attack_cooldown
        self.last_attack_time = 0
        self.enabled = False

    def start(self):
        """Inicia o módulo de ataque."""
        self.enabled = True
        print(f"[AutoAttacker] Módulo de combate ativado (Hotkey de ataque: '{self.attack_key.upper()}').")

    def stop(self):
        """Para o módulo de ataque."""
        self.enabled = False
        print("[AutoAttacker] Módulo de combate desativado.")

    def update(self, img_bgr, in_pz: bool = False):
        """
        Lógica de combate executada continuousamente no loop principal.
        
        :param img_bgr: Frame da imagem capturada em BGR.
        :param in_pz: Booleano indicando se o personagem está em Protection Zone.
        """
        if not self.enabled or in_pz:
            return

        now = time.time()
        
        # 1. Verifica se já existe um alvo ativo selecionado (moldura de ataque vermelha)
        if has_active_target(img_bgr):
            # Alvo ativo sendo atacado -> mantém combate
            return

        # 2. Se não houver alvo ativo, verifica se há monstros presentes na Battle List
        if has_monsters_in_battle(img_bgr):
            # Respeita o cooldown entre envios de comandos de ataque
            if now - self.last_attack_time >= self.attack_cooldown:
                print(f"\n[AutoAttacker] ⚔️ Novo alvo detectado! Pressionando '{self.attack_key.upper()}' para atacar...")
                press_key(self.attack_key)
                self.last_attack_time = now
