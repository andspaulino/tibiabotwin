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

# ROIs mapeadas da interface (Projetor OBS)
HP_BAR_ROI = {'top': 0, 'left': 359, 'width': 539, 'height': 20}
MP_BAR_ROI = {'top': 1, 'left': 1024, 'width': 537, 'height': 19}
STATUS_BAR_ROI = {'top': 1, 'left': 915, 'width': 110, 'height': 18}
BATTLE_LIST_ROI = {'top': 160, 'left': 1740, 'width': 160, 'height': 350}

def crop_roi(img, roi: dict):
    """Corta uma Região de Interesse (ROI) da imagem OpenCV BGR."""
    top, left, width, height = roi['top'], roi['left'], roi['width'], roi['height']
    return img[top:top+height, left:left+width]

def get_hp_percentage(img, roi: dict = HP_BAR_ROI) -> float:
    """
    Calcula a porcentagem atual de Vida (HP) na ROI da barra (retorna valor de 0.0 a 1.0).
    Filtra pixels verdes/vermelhos da barra de vida vs fundo cinza/texto.
    """
    if np is None:
        return 0.0
    roi_img = crop_roi(img, roi)
    if roi_img.size == 0:
        return 0.0
    
    mid_y = roi_img.shape[0] // 2
    row = roi_img[mid_y, :]  # BGR
    
    # Pixel ativo de HP: canal Verde ou Vermelho dominante sobre o Azul
    is_hp = ((row[:, 1] > row[:, 0] + 15) & (row[:, 1] > 50)) | ((row[:, 2] > row[:, 0] + 15) & (row[:, 2] > 50))
    filled_pixels = np.sum(is_hp)
    total_pixels = row.shape[0]
    
    return float(filled_pixels / total_pixels) if total_pixels > 0 else 0.0

def get_mp_percentage(img, roi: dict = MP_BAR_ROI) -> float:
    """
    Calcula a porcentagem atual de Mana (MP) na ROI da barra (retorna valor de 0.0 a 1.0).
    Filtra pixels azuis da barra de mana vs texto/fundo.
    """
    if np is None:
        return 0.0
    roi_img = crop_roi(img, roi)
    if roi_img.size == 0:
        return 0.0
    
    mid_y = roi_img.shape[0] // 2
    row = roi_img[mid_y, :]  # BGR
    
    # Pixel ativo de MP: canal Azul dominante sobre o Verde e Vermelho
    is_mp = (row[:, 0] > row[:, 1] + 15) & (row[:, 0] > row[:, 2] + 15) & (row[:, 0] > 50)
    filled_pixels = np.sum(is_mp)
    total_pixels = row.shape[0]
    
    return float(filled_pixels / total_pixels) if total_pixels > 0 else 0.0

def get_status_bar_image(img, roi: dict = STATUS_BAR_ROI):
    """
    Retorna o recorte NumPy BGR da Barra de Status (ícones de envenenamento, paralisação, PZ, etc.).
    """
    return crop_roi(img, roi)

def get_status_bar_activity(img, roi: dict = STATUS_BAR_ROI) -> dict:
    """
    Analisa a Barra de Status e retorna informações sobre a presença de ícones ativos.
    """
    if np is None:
        return {"active": False, "active_pixels": 0}
    
    status_img = crop_roi(img, roi)
    if status_img.size == 0:
        return {"active": False, "active_pixels": 0}
    
    # Identifica pixels com iluminação/cor acima do fundo neutro
    active_pixels = int(np.sum(np.sum(status_img, axis=2) > 60))
    has_icons = active_pixels > 10
    
    return {
        "active": has_icons,
        "active_pixels": active_pixels,
        "roi": roi
    }

def is_in_pz(img, pz_template_path: str = "templates/pz.png", threshold: float = 0.82) -> bool:
    """
    Verifica se o personagem está em Protection Zone (PZ) utilizando Template Matching e validação de cor azul/branca.
    """
    if cv2 is None or np is None or not os.path.exists(pz_template_path):
        return False
    
    pz_template = cv2.imread(pz_template_path)
    if pz_template is None:
        return False
    
    status_img = get_status_bar_image(img)
    if status_img.size == 0:
        return False

    # 1. Busca por correspondência visual de template
    res = cv2.matchTemplate(status_img, pz_template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val < threshold:
        return False

    # 2. Confirmação pela presença de pixels com azul característico da pombinha de PZ (BGR)
    has_blue_dove = np.any((status_img[:, :, 0] > status_img[:, :, 1] + 20) & 
                           (status_img[:, :, 0] > status_img[:, :, 2] + 20) & 
                           (status_img[:, :, 0] > 100))

    return bool(has_blue_dove)

def has_monsters_in_battle(img, roi: dict = BATTLE_LIST_ROI) -> bool:
    """
    Verifica se há alvos/criaturas presentes na região da Battle List.
    Avalia a contagem de pixels ativos (barras de vida de criaturas / nomes) em relação ao fundo escuro.
    """
    if np is None:
        return False
    battle_img = crop_roi(img, roi)
    if battle_img.size == 0:
        return False

    # Na Battle List, entradas de monstros possuem nomes com pixels claros e barrinhas de vida
    active_pixels = int(np.sum(np.sum(battle_img, axis=2) > 80))
    return bool(active_pixels > 50)

def has_active_target(img, roi: dict = BATTLE_LIST_ROI) -> bool:
    """
    Verifica se há um alvo ativo atualmente selecionado (moldura de ataque vermelha viva na Battle List).
    Na interface do Tibia, o alvo selecionado possui uma moldura vermelha intensa em volta de sua linha.
    """
    if np is None:
        return False
    battle_img = crop_roi(img, roi)
    if battle_img.size == 0:
        return False

    # Procura por pixels com Vermelho puro dominante (R > 180, G < 60, B < 60)
    red_mask = (battle_img[:, :, 2] > 180) & (battle_img[:, :, 1] < 60) & (battle_img[:, :, 0] < 60)
    red_target_pixels = int(np.sum(red_mask))
    
    # Se houver moldura vermelha (pelo menos 15 pixels formando a borda)
    return bool(red_target_pixels >= 15)
