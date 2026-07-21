class AutoAttacker:
    """Módulo responsável por detectar alvos na Battle List e atacar automaticamente."""

    def __init__(self):
        self.enabled = False

    def start(self):
        self.enabled = True
        print("[AutoAttacker] Módulo de combate ativado.")

    def stop(self):
        self.enabled = False
        print("[AutoAttacker] Módulo de combate desativado.")

    def update(self):
        """Lógica de combate a ser executada no loop principal."""
        if not self.enabled:
            return
        pass
