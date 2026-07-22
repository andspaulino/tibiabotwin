import os
import sys
import threading
import time
import tkinter as tk
from typing import Optional, Union

from src.utils.logger import logger
from src.domain.game_state import GameState
from src.domain.bot_state import BotMode, BotState

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x0000020
    WS_EX_TOPMOST = 0x00000008


class OnScreenOverlay:
    """
    Overlay Transparente de Tela (HUD) para o Tibia Bot.
    Exibe logs em tempo real por cima do jogo/OBS sem bloquear cliques do mouse (Click-Through).
    """

    def __init__(self, width: int = 360, height: int = 250, pos_x: int = 0, pos_y: int = 780):
        self.width = width
        self.height = height
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.root = None
        self.thread = None
        self.running = False
        self.last_game_state: Optional[GameState] = None
        self.last_bot_state: Optional[BotState] = None
        self.observe_only = False
        self.status_label = None

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

        self.status_label = tk.Label(
            frame,
            text="[STATUS]: Inicializando...",
            font=("Consolas", 8, "bold"),
            fg="#8b949e",
            bg="#161b22",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=2, pady=1)

        self.log_container = tk.Frame(frame, bg="#0d1117")
        self.log_container.pack(fill="both", expand=True, padx=6, pady=4)

        self._update_logs_ui()

        # Inscreve a função de atualização nos eventos do Logger
        logger.add_listener(self._on_log_event)

        self.running = True
        self.root.mainloop()

    def update(
        self,
        game_state: Optional[GameState] = None,
        bot_state: Optional[BotState] = None,
        observe_only: bool = False
    ):
        """Atualiza a interface do Overlay com os snapshots mais recentes de GameState e BotState."""
        if game_state is not None:
            self.last_game_state = game_state
        if bot_state is not None:
            self.last_bot_state = bot_state
        self.observe_only = observe_only

        if self.root and self.running:
            try:
                self.root.after(0, self._render_status_ui)
            except Exception:
                pass

    def _render_status_ui(self):
        if not self.root or not self.status_label or not self.last_game_state:
            return

        gs = self.last_game_state
        bs = self.last_bot_state

        hp_str = f"{gs.player.hp_percent * 100:.0f}%" if gs.player.hp_percent is not None else "??"
        mp_str = f"{gs.player.mana_percent * 100:.0f}%" if gs.player.mana_percent is not None else "??"
        pz_str = "SIM" if gs.player.in_protection_zone else ("NAO" if gs.player.in_protection_zone is False else "??")
        
        mode_str = bs.current_mode.value.upper() if bs else ("SEGURO" if gs.is_safe_to_act else "UNSAFE")
        if self.observe_only:
            mode_str += " [OBSERVE ONLY]"

        txt = f"HP:{hp_str} | MP:{mp_str} | PZ:{pz_str} | MODE:{mode_str}"
        
        if bs:
            fg = "#3fb950" if bs.current_mode in (BotMode.IDLE, BotMode.COMBAT) else ("#58a6ff" if bs.current_mode == BotMode.IN_PROTECTION_ZONE else "#f85149")
        else:
            fg = "#3fb950" if gs.is_safe_to_act else "#f85149"

        self.status_label.config(text=txt, fg=fg)

    def _on_log_event(self, entry: dict):
        if self.root and self.running:
            try:
                self.root.after(0, self._update_logs_ui)
            except Exception:
                pass

    def _update_logs_ui(self):
        if not self.root or not hasattr(self, "log_container"):
            return

        for widget in self.log_container.winfo_children():
            widget.destroy()

        recent = logger.get_recent_logs(7)

        for log in recent:
            level = log.get("level", "INFO")

            color_map = {
                "ACTION": "#3fb950",
                "WARNING": "#d29922",
                "ERROR": "#f85149",
                "INFO": "#8b949e"
            }
            fg_color = color_map.get(level, "#8b949e")

            line_str = f"{log['timestamp']} [{log['category']:7s}] {log['message']}"

            lbl = tk.Label(
                self.log_container,
                text=line_str,
                font=("Consolas", 8),
                fg=fg_color,
                bg="#0d1117",
                anchor="w",
                justify="left"
            )
            lbl.pack(fill="x", pady=0)

    def start(self):
        """Inicia a janela do Overlay transparente em uma thread separada."""
        if self.running:
            return
        self.thread = threading.Thread(target=self._create_window, daemon=True)
        self.thread.start()

    def stop(self):
        """Encerra graciosamente a janela do Overlay."""
        self.running = False
        if self.root:
            try:
                self.root.after(0, self.root.destroy)
            except Exception:
                pass
