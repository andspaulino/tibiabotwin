import os
import sys
import threading
import time
import tkinter as tk
from src.utils.logger import logger

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_TOPMOST = 0x00000008

class OnScreenOverlay:
    """
    Overlay Transparente de Tela (HUD) para o Tibia Bot.
    Exibe logs em tempo real por cima do jogo/OBS sem bloquear cliques do mouse (Click-Through).
    """

    def __init__(self, width: int = 350, height: int = 230, pos_x: int = 0, pos_y: int = 800):
        self.width = width
        self.height = height
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.root = None
        self.thread = None
        self.running = False
        self.labels = []

    def _create_window(self):
        self.root = tk.Tk()
        self.root.title("Tibia Bot HUD Overlay")
        self.root.geometry(f"{self.width}x{self.height}+{self.pos_x}+{self.pos_y}")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # Cor transparente de fundo
        bg_color = "#010101"
        self.root.config(bg=bg_color)
        self.root.wm_attributes("-transparentcolor", bg_color)

        # Configura Win32 Click-Through no Windows (os cliques do mouse passam direto para o jogo)
        if sys.platform == "win32":
            try:
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            except Exception as e:
                print(f"[HUD Overlay] Erro ao aplicar estilo Click-Through: {e}")

        # Frame container com fundo escuro semi-transparente
        frame = tk.Frame(self.root, bg="#0d1117", bd=1, relief="solid")
        frame.pack(fill="both", expand=True)

        title_label = tk.Label(
            frame,
            text=" 🎮 TIBIA BOT - HUD OVERLAY ",
            font=("Consolas", 10, "bold"),
            fg="#58a6ff",
            bg="#161b22",
            anchor="w"
        )
        title_label.pack(fill="x", padx=2, pady=2)

        self.log_container = tk.Frame(frame, bg="#0d1117")
        self.log_container.pack(fill="both", expand=True, padx=6, pady=4)

        self._update_logs_ui()

        # Inscreve a função de atualização nos eventos do Logger
        logger.add_listener(self._on_log_event)

        self.running = True
        self.root.mainloop()

    def _on_log_event(self, entry: dict):
        if self.root and self.running:
            try:
                self.root.after(0, self._update_logs_ui)
            except Exception:
                pass

    def _update_logs_ui(self):
        if not self.root:
            return

        # Limpa rótulos anteriores
        for widget in self.log_container.winfo_children():
            widget.destroy()

        recent_logs = logger.get_recent_logs(count=7)

        color_map = {
            "HEALER": "#3fb950",   # Verde
            "COMBAT": "#f85149",   # Vermelho
            "PZ": "#58a6ff",       # Azul
            "SYSTEM": "#d29922"    # Amarelo/Dourado
        }

        for log in recent_logs:
            cat = log["category"]
            fg_color = color_map.get(cat, "#c9d1d9")
            text_line = f"[{cat:7s}] {log['message']}"

            lbl = tk.Label(
                self.log_container,
                text=text_line,
                font=("Consolas", 9, "bold"),
                fg=fg_color,
                bg="#0d1117",
                anchor="w",
                justify="left"
            )
            lbl.pack(fill="x", pady=1)

    def start(self):
        """Inicia a janela de Overlay Transparente em uma thread separada."""
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._create_window, daemon=True)
        self.thread.start()
        time.sleep(0.5)

    def stop(self):
        """Fecha a janela do Overlay."""
        self.running = False
        if self.root:
            try:
                self.root.after(0, self.root.destroy)
            except Exception:
                pass
