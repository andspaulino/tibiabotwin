import time
import random

try:
    import pydirectinput
    pydirectinput.FAILSAFE = False
except ImportError:
    pydirectinput = None

def press_key(key: str, delay: float = 0.05):
    """
    Simula o pressionamento de uma tecla usando DirectX scan codes.
    
    :param key: Nome da tecla (ex: 'f1', 'f2', 'space', 'a')
    :param delay: Tempo de espera após pressionar a tecla
    """
    if pydirectinput is None:
        raise RuntimeError("pydirectinput não está instalado.")
    
    pydirectinput.keyDown(key)
    time.sleep(random.uniform(0.02, 0.05))
    pydirectinput.keyUp(key)
    
    # Pausa com leve variação humanizada
    time.sleep(delay + random.uniform(0.005, 0.02))

def click_at(x: int, y: int, button: str = 'left', delay: float = 0.1):
    """
    Move o cursor e clica em uma posição específica da tela.
    """
    if pydirectinput is None:
        raise RuntimeError("pydirectinput não está instalado.")
    
    pydirectinput.moveTo(x, y)
    time.sleep(random.uniform(0.03, 0.07))
    pydirectinput.click(button=button)
    time.sleep(delay + random.uniform(0.01, 0.03))
