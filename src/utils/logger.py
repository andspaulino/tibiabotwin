import time
import os
from collections import deque
from pathlib import Path
from uuid import uuid4
import logging
from logging.handlers import RotatingFileHandler


class Logger:
    """
    Gerenciador centralizado de logs do Tibia Bot.
    Padroniza mensagens, mantém buffer histórico, rotação de arquivos e sincronização para OBS/HUD.
    """

    _instance = None

    def __new__(cls, max_history: int = 50, hud_file: str = "logs_hud.txt"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.history = deque(maxlen=max_history)
            cls._instance.listeners = []
            cls._instance.hud_file = hud_file
            cls._instance.session_id = uuid4().hex[:8]
            cls._instance.last_log_entry = None
            
            # Configura diretório de logs e RotatingFileHandler
            log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "app.log"

            file_formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [SESSION:%(session_id)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=5 * 1024 * 1024,  # 5 MB por arquivo
                backupCount=3,
                encoding="utf-8"
            )
            file_handler.setFormatter(file_formatter)

            cls._instance.file_logger = logging.getLogger("TibiaBotFileLogger")
            cls._instance.file_logger.setLevel(logging.DEBUG)
            cls._instance.file_logger.addHandler(file_handler)

        return cls._instance

    def log(self, category: str, message: str, level: str = "INFO"):
        """
        Emite um evento de log centralizado.
        """
        category_upper = category.upper()
        level_upper = level.upper()

        # Evita repetição da exata mesma mensagem no mesmo segundo
        log_key = (category_upper, message)
        if self.last_log_entry == log_key and level_upper == "INFO":
            return
        self.last_log_entry = log_key

        timestamp_str = time.strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp_str,
            "category": category_upper,
            "message": message,
            "level": level_upper
        }

        self.history.append(entry)

        # Registra no arquivo de log rotacionado
        file_msg = f"[{category_upper:8s}] {message}"
        self.file_logger.info(file_msg, extra={"session_id": self.session_id})

        # Formatação padronizada para o console
        cat_tag = f"[{category_upper}]"
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
