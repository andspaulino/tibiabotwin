import time
import os
from collections import deque

class Logger:
    """
    Gerenciador centralizado de logs do Tibia Bot.
    Padroniza mensagens, mantém buffer histórico e sincroniza arquivo para OBS/HUD.
    """

    _instance = None

    def __new__(cls, max_history: int = 50, hud_file: str = "logs_hud.txt"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.history = deque(maxlen=max_history)
            cls._instance.listeners = []
            cls._instance.hud_file = hud_file
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

        # Sincroniza os últimos logs no arquivo logs_hud.txt para OBS Studio / HUD
        self._sync_hud_file()

        # Notifica inscritos (ex: Overlay transparente de tela / HUD)
        for listener in self.listeners:
            try:
                listener(entry)
            except Exception:
                pass

    def _sync_hud_file(self, count: int = 7):
        """Escreve os últimos N logs formatados em um arquivo texto para o OBS Studio."""
        try:
            recent = self.get_recent_logs(count)
            lines = [f"{e['timestamp']} [{e['category']:7s}] {e['message']}" for e in recent]
            with open(self.hud_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
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
