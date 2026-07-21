import ctypes
from ctypes import wintypes
import os
try:
    import mss
except ImportError:
    mss = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import cv2
except ImportError:
    cv2 = None

ClientToScreen = ctypes.windll.user32.ClientToScreen
GetClientRect = ctypes.windll.user32.GetClientRect

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class ScreenCapturer:
    """Gerenciador de captura de tela de alta velocidade via MSS."""

    def __init__(self):
        if mss is None:
            raise RuntimeError("Biblioteca 'mss' não encontrada. Instale executando: pip install -r requirements.txt")
        self.sct = mss.mss()

    def capture_monitor(self, monitor_index: int = 1) -> Image.Image:
        """Captura a tela inteira de um monitor."""
        monitor = self.sct.monitors[monitor_index]
        sct_img = self.sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    def capture_window_client_area(self, hwnd: int) -> Image.Image:
        """
        Captura a área do cliente de uma janela específica (exclui bordas e barras de título).
        Ideal para capturar a janela de Projetor do OBS Studio.
        """
        client_rect = wintypes.RECT()
        GetClientRect(hwnd, ctypes.byref(client_rect))
        
        width = client_rect.right - client_rect.left
        height = client_rect.bottom - client_rect.top

        pt = POINT(0, 0)
        ClientToScreen(hwnd, ctypes.byref(pt))
        left, top = pt.x, pt.y

        monitor = {"top": top, "left": left, "width": width, "height": height}
        sct_img = self.sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    def capture_region(self, top: int, left: int, width: int, height: int) -> Image.Image:
        """Captura uma região retangular específica da tela."""
        monitor = {"top": top, "left": left, "width": width, "height": height}
        sct_img = self.sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    def close(self):
        """Libera os recursos do gravador de tela."""
        self.sct.close()

def pil_to_cv2(pil_img) -> np.ndarray:
    """Converte uma imagem PIL para array NumPy no formato BGR do OpenCV."""
    if np is None or cv2 is None:
        raise RuntimeError("NumPy e OpenCV são necessários. Instale executando: pip install -r requirements.txt")
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def locate_template(img, template, threshold: float = 0.8):
    """
    Busca um template dentro de uma imagem usando cv2.matchTemplate.
    Retorna (max_val, max_loc) ou None se abaixo do limite.
    """
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) não está instalado. Instale executando: pip install -r requirements.txt")
    
    result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        return max_val, max_loc
    return None
