import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.humanizer import (
    gaussian_delay,
    get_key_hold_duration,
    MicroPauseGenerator,
    generate_bezier_points
)

def main():
    print("==================================================")
    print("        Teste do Módulo de Humanização            ")
    print("==================================================")

    print("\n1. Amostragem de Delays Gaussianos (Média: 150ms):")
    delays = [gaussian_delay(mean=0.150, std_dev=0.030, min_val=0.080, max_val=0.350) for _ in range(5)]
    for idx, d in enumerate(delays, 1):
        print(f"  - Amostra {idx}: {d * 1000:6.2f} ms")

    print("\n2. Duração de Pressionamento de Teclas (Key Hold):")
    holds = [get_key_hold_duration() for _ in range(5)]
    for idx, h in enumerate(holds, 1):
        print(f"  - Pressionamento {idx}: {h * 1000:6.2f} ms")

    print("\n3. Trajetória de Curva de Bézier (Mouse de (0,0) para (500,300)):")
    points = generate_bezier_points(0, 0, 500, 300, num_points=6)
    for idx, pt in enumerate(points):
        print(f"  - Passo {idx}: X={pt[0]:4d}, Y={pt[1]:4d}")

    print("\n4. Teste de Micro-Pausa (Simulando 30 ações rápidas):")
    pauser = MicroPauseGenerator(min_actions=5, max_actions=10)
    for i in range(1, 15):
        triggered = pauser.tick()
        if not triggered:
            print(f"  - Ação {i}: normal", end="\r")
            time.sleep(0.02)
        else:
            print(f"\n  -> Micro-pausa engatada na ação {i}!")

    print("\n==================================================")
    print("[OK] Teste de humanização concluído com sucesso!")
    print("==================================================")

if __name__ == "__main__":
    main()
