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
    """
    if pydirectinput is None:
        print(f"[Simulacao Input] Tecla '{key.upper()}' acionada (instale pydirectinput para envio real).")
        time.sleep(delay)
        return
    
    pydirectinput.keyDown(key)
    time.sleep(random.uniform(0.02, 0.05))
    pydirectinput.keyUp(key)
    time.sleep(delay + random.uniform(0.005, 0.02))

def click_at(x: int, y: int, button: str = 'left', delay: float = 0.1):
    """
    Move o cursor e clica em uma posição específica da tela.
    """
    if pydirectinput is None:
        print(f"[Simulacao Input] Clique em ({x}, {y}) com botao {button}.")
        time.sleep(delay)
        return
    
    pydirectinput.moveTo(x, y)
    time.sleep(random.uniform(0.03, 0.07))
    pydirectinput.click(button=button)
    time.sleep(delay + random.uniform(0.01, 0.03))
