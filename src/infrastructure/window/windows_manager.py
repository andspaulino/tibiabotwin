import sys
from typing import Optional, Tuple, List
from src.config.models import WindowConfig
from src.infrastructure.window.base import WindowManager

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    LWA_ALPHA = 0x00000002

    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020
    SWP_FLAGS = SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED

    RDW_INVALIDATE = 0x0001
    RDW_ERASE = 0x0004
    RDW_UPDATENOW = 0x0100
    RDW_ALLCHILDREN = 0x0080
    RDW_FLAGS = RDW_INVALIDATE | RDW_ERASE | RDW_UPDATENOW | RDW_ALLCHILDREN

    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    GetWindowTextW = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    IsIconic = ctypes.windll.user32.IsIconic
    GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
    GetWindowLongW = ctypes.windll.user32.GetWindowLongW
    SetWindowLongW = ctypes.windll.user32.SetWindowLongW
    SetLayeredWindowAttributes = ctypes.windll.user32.SetLayeredWindowAttributes
    SetWindowPos = ctypes.windll.user32.SetWindowPos
    RedrawWindow = ctypes.windll.user32.RedrawWindow


class WindowsWindowManager(WindowManager):
    """Implementação Win32 do gerenciador de janelas para Windows."""

    def _get_window_title(self, hwnd: int) -> str:
        if sys.platform != "win32":
            return ""
        length = GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        GetWindowTextW(hwnd, buff, length + 1)
        return buff.value

    def _find_windows_by_title(self, title_query: str, allow_partial: bool = True) -> List[Tuple[int, str]]:
        if sys.platform != "win32":
            return []
        matching = []

        def enum_handler(hwnd, lparam):
            if IsWindowVisible(hwnd):
                title = self._get_window_title(hwnd)
                if allow_partial:
                    if title_query.lower() in title.lower():
                        matching.append((hwnd, title))
                else:
                    if title_query.lower() == title.lower():
                        matching.append((hwnd, title))
            return True

        EnumWindows(EnumWindowsProc(enum_handler), 0)
        return matching

    def find_tibia(self, window_cfg: WindowConfig) -> Optional[Tuple[int, str]]:
        windows = self._find_windows_by_title(window_cfg.tibia_title, allow_partial=window_cfg.allow_partial_match)
        tibia_specific = [w for w in windows if w[1].startswith("Tibia - ")]
        if tibia_specific:
            return tibia_specific[0]
        return windows[0] if windows else None

    def find_projector(self, window_cfg: WindowConfig) -> Optional[Tuple[int, str]]:
        windows = self._find_windows_by_title(window_cfg.obs_title, allow_partial=window_cfg.allow_partial_match)
        if not windows:
            windows = self._find_windows_by_title("obs") or self._find_windows_by_title("projetor") or self._find_windows_by_title("projector")
        return windows[0] if windows else None

    def is_focused(self, hwnd: int) -> bool:
        if sys.platform != "win32" or hwnd <= 0:
            return False
        return bool(GetForegroundWindow() == hwnd)

    def is_minimized(self, hwnd: int) -> bool:
        if sys.platform != "win32" or hwnd <= 0:
            return True
        return bool(IsIconic(hwnd))

    def set_opacity(self, hwnd: int, opacity: int) -> bool:
        if sys.platform != "win32" or hwnd <= 0:
            return False
        if opacity >= 255:
            return self.reset_opacity(hwnd)

        opacity = max(0, min(255, opacity))
        ex_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
        if not (ex_style & WS_EX_LAYERED):
            SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)

        result = SetLayeredWindowAttributes(hwnd, 0, opacity, LWA_ALPHA)
        SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FLAGS)
        RedrawWindow(hwnd, None, None, RDW_FLAGS)
        return bool(result)

    def reset_opacity(self, hwnd: int) -> bool:
        if sys.platform != "win32" or hwnd <= 0:
            return False
        SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
        ex_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
        if ex_style & WS_EX_LAYERED:
            SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style & ~WS_EX_LAYERED)
        SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FLAGS)
        RedrawWindow(hwnd, None, None, RDW_FLAGS)
        return True
