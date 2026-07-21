import time
from collections import deque

class Logger:
    """
    Gerenciador centralizado de logs do Tibia Bot.
    Padroniza mensagens e mantém buffer histórico para renderização em Overlays de tela futuros.
    """

    _instance = None

    def __new__(cls, max_history: int = 50):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.history = deque(maxlen=max_history)
            cls._instance.listeners = []
        return cls._instance

    def log(self, category: str, message: str, level: str = "INFO"):
        """
        Emite um evento de log centralizado.
        
        :param category: Categoria do evento ('HEALER', 'COMBAT', 'PZ', 'SYSTEM')
        :param message: Texto descritivo da ação
        :param level: Nível ('INFO', 'ACTION', 'WARNING', 'ERROR')
        """
        timestamp_str = time.strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp_str,
            "category": category.upper(),
            "message": message,
            "level": level.upper()
        }

        self.history.append(entry)

        # Formatação padronizada para o console
        cat_tag = f"[{entry['category']}]"
        print(f"{timestamp_str} {cat_tag:10s} {message}")

        # Notifica inscritos (ex: futuro Overlay de tela / HUD)
        for listener in self.listeners:
            try:
                listener(entry)
            except Exception:
                pass

    def add_listener(self, callback):
        """Registra uma função callback para receber novos eventos em tempo real."""
        if callback not in self.listeners:
            self.listeners.append(callback)

    def get_recent_logs(self, count: int = 10) -> list[dict]:
        """Retorna os últimos N registros para exibição em Overlays ou interfaces gráficas."""
        return list(self.history)[-count:]

# Instância global singleton do Logger
logger = Logger()
