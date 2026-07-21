import time
import random
import math

def gaussian_delay(mean: float, std_dev: float, min_val: float, max_val: float) -> float:
    """
    Gera um tempo de delay baseado em Distribuição Gaussiana (Curva Normal).
    Simula o tempo de reação humano, onde a maioria dos eventos se concentra ao redor da média.
    
    :param mean: Tempo médio em segundos (ex: 0.150s)
    :param std_dev: Desvio padrão (ex: 0.030s)
    :param min_val: Tempo mínimo absoluto em segundos
    :param max_val: Tempo máximo absoluto em segundos
    """
    val = random.gauss(mean, std_dev)
    clamped_val = max(min_val, min(max_val, val))
    return clamped_val

def sleep_gaussian(mean: float = 0.15, std_dev: float = 0.03, min_val: float = 0.08, max_val: float = 0.35):
    """Executa time.sleep com variação gaussiana humanizada."""
    delay = gaussian_delay(mean, std_dev, min_val, max_val)
    time.sleep(delay)
    return delay

def get_key_hold_duration() -> float:
    """
    Retorna o tempo pelo qual a tecla fica pressionada (key down até key up).
    Simula o tempo de pressão física de um dedo humano na tecla (30ms a 75ms).
    """
    return gaussian_delay(mean=0.045, std_dev=0.008, min_val=0.025, max_val=0.085)

class MicroPauseGenerator:
    """
    Gerenciador de micro-pausas e hesitações humanas.
    A cada N ações, introduz ocasionalmente uma breve pausa orgânica.
    """

    def __init__(self, min_actions: int = 25, max_actions: int = 60):
        self.min_actions = min_actions
        self.max_actions = max_actions
        self.action_counter = 0
        self.target_count = random.randint(self.min_actions, self.max_actions)

    def tick(self) -> bool:
        """
        Incrementa o contador de ações e verifica se uma micro-pausa deve ocorrer.
        Retorna True se uma micro-pausa foi acionada.
        """
        self.action_counter += 1
        if self.action_counter >= self.target_count:
            pause_time = gaussian_delay(mean=0.45, std_dev=0.15, min_val=0.20, max_val=0.85)
            print(f"\n[Humanizer] Micro-pausa humana ({pause_time * 1000:.0f}ms)...")
            time.sleep(pause_time)
            
            # Reseta o contador com novo limite aleatório
            self.action_counter = 0
            self.target_count = random.randint(self.min_actions, self.max_actions)
            return True
        return False

def generate_bezier_points(start_x: int, start_y: int, end_x: int, end_y: int, num_points: int = 15) -> list[tuple[int, int]]:
    """
    Gera uma trajetória de pontos no formato de curva de Bézier quadrática com leves imperfeições.
    Simula a movimentação curva natural da mão humana controlando o mouse.
    """
    # Ponto de controle intermediário deslocado (para criar a curva)
    mid_x = (start_x + end_x) / 2 + random.randint(-50, 50)
    mid_y = (start_y + end_y) / 2 + random.randint(-50, 50)

    points = []
    for i in range(num_points + 1):
        t = i / float(num_points)
        # Fórmula da Curva de Bézier Quadrática
        x = (1 - t)**2 * start_x + 2 * (1 - t) * t * mid_x + t**2 * end_x
        y = (1 - t)**2 * start_y + 2 * (1 - t) * t * mid_y + t**2 * end_y
        
        # Adiciona leve trepidação/jitter humanizado nos pontos intermediários
        if 0 < i < num_points:
            x += random.uniform(-1.5, 1.5)
            y += random.uniform(-1.5, 1.5)

        points.append((int(round(x)), int(round(y))))
    return points
