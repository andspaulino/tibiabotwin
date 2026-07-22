import ctypes
from ctypes import wintypes

# Constantes do Win32 API
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x00000002

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020
SWP_FLAGS = SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED

# Funções Win32 API
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

def is_window_minimized(hwnd: int) -> bool:
    """Verifica se a janela está minimizada no Windows."""
    return bool(IsIconic(hwnd))

def is_window_active(hwnd: int) -> bool:
    """Verifica se a janela informada está no primeiro plano (foco ativo) do Windows."""
    return GetForegroundWindow() == hwnd

RDW_INVALIDATE = 0x0001
RDW_ERASE = 0x0004
RDW_UPDATENOW = 0x0100
RDW_ALLCHILDREN = 0x0080
RDW_FLAGS = RDW_INVALIDATE | RDW_ERASE | RDW_UPDATENOW | RDW_ALLCHILDREN

def get_window_title(hwnd: int) -> str:
    """Retorna o título de uma janela pelo seu HWND."""
    length = GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    GetWindowTextW(hwnd, buff, length + 1)
    return buff.value

def find_windows_by_title(title_query: str, allow_partial: bool = True) -> list[tuple[int, str]]:
    """Busca todas as janelas visíveis cujo título contenha ou coincida com a string fornecida."""
    matching_windows = []
    
    def enum_handler(hwnd, lparam):
        if IsWindowVisible(hwnd):
            title = get_window_title(hwnd)
            if allow_partial:
                if title_query.lower() in title.lower():
                    matching_windows.append((hwnd, title))
            else:
                if title_query.lower() == title.lower():
                    matching_windows.append((hwnd, title))
        return True

    EnumWindows(EnumWindowsProc(enum_handler), 0)
    return matching_windows


def set_window_opacity(hwnd: int, opacity: int) -> bool:
    """
    Altera a opacidade de uma janela.
    
    :param hwnd: Handle da janela.
    :param opacity: Valor de 0 a 255.
    """
    if opacity >= 255:
        return reset_window_opacity(hwnd)

    opacity = max(0, min(255, opacity))
    ex_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
    
    if not (ex_style & WS_EX_LAYERED):
        SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
    
    result = SetLayeredWindowAttributes(hwnd, 0, opacity, LWA_ALPHA)
    SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FLAGS)
    RedrawWindow(hwnd, None, None, RDW_FLAGS)
    return bool(result)

def reset_window_opacity(hwnd: int) -> bool:
    """Restaura completamente a opacidade (255) e remove o estilo de transparência da janela."""
    # 1. Ajusta o alpha de volta para 255
    SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
    
    # 2. Remove o estilo WS_EX_LAYERED da janela
    ex_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
    if ex_style & WS_EX_LAYERED:
        SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style & ~WS_EX_LAYERED)
    
    # 3. Força a redraw imediata do frame no DWM do Windows
    SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FLAGS)
    RedrawWindow(hwnd, None, None, RDW_FLAGS)
    return True
