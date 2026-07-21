import time
import random

try:
    import pydirectinput
    pydirectinput.FAILSAFE = False
except ImportError:
    pydirectinput = None

from src.utils.humanizer import (
    get_key_hold_duration,
    gaussian_delay,
    generate_bezier_points
)

def press_key(key: str, delay: float = 0.05):
    """
    Simula o pressionamento de uma tecla usando DirectX scan codes com tempo de retenção e pausa humanizados.
    
    :param key: Nome da tecla (ex: '1', '2', '3', 'f1', 'space')
    :param delay: Pausa base pós-pressionar
    """
    hold_time = get_key_hold_duration()
    post_delay = gaussian_delay(mean=delay, std_dev=delay * 0.2, min_val=0.01, max_val=delay * 2.0)

    if pydirectinput is None:
        print(f"[Simulacao Input] Tecla '{key.upper()}' acionada ({hold_time * 1000:.0f}ms pressionada).")
        time.sleep(hold_time + post_delay)
        return

    pydirectinput.keyDown(key)
    time.sleep(hold_time)
    pydirectinput.keyUp(key)
    time.sleep(post_delay)

def move_mouse_human(target_x: int, target_y: int):
    """
    Move o cursor até as coordenadas de destino seguindo uma curva de Bézier humanizada.
    """
    if pydirectinput is None:
        print(f"[Simulacao Input] Mover mouse para ({target_x}, {target_y}).")
        return

    curr_x, curr_y = pydirectinput.position()
    trajectory = generate_bezier_points(curr_x, curr_y, target_x, target_y, num_points=12)

    for px, py in trajectory:
        pydirectinput.moveTo(px, py)
        time.sleep(random.uniform(0.003, 0.008))

def click_at(x: int, y: int, button: str = 'left', delay: float = 0.1):
    """
    Move o cursor em trajetória curva e clica na posição informada.
    """
    move_mouse_human(x, y)
    
    pre_click_delay = gaussian_delay(mean=0.04, std_dev=0.01, min_val=0.015, max_val=0.08)
    time.sleep(pre_click_delay)

    if pydirectinput is None:
        print(f"[Simulacao Input] Clique {button.upper()} em ({x}, {y}).")
        time.sleep(delay)
        return

    pydirectinput.click(button=button)
    post_delay = gaussian_delay(mean=delay, std_dev=delay * 0.2, min_val=0.02, max_val=delay * 2.0)
    time.sleep(post_delay)
