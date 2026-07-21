import os
import sys

# Garante importações a partir da raiz do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from tests.test_obs_capture import main as capture_obs_screen
from src.utils.screen import is_in_pz

def main():
    print("==================================================")
    print("      Teste Dinamico de Deteccao de PZ            ")
    print("==================================================")
    
    # 1. Utiliza o script existente (test_obs_capture.py) para tirar a captura limpa do OBS
    print("Acionando o script de captura do OBS (tests/test_obs_capture.py)...\n")
    capture_obs_screen()

    # 2. Carrega a imagem salva pelo script de captura
    image_path = "screenshot_obs_clean.png"
    if not os.path.exists(image_path):
        print(f"\n[X] Nao foi possivel encontrar '{image_path}'. A captura falhou.")
        return

    img = cv2.imread(image_path)
    
    # 3. Executa a checagem de PZ usando o módulo do projeto
    in_pz = is_in_pz(img)

    print("\n==================================================")
    print("           Resultado da Verificacao de PZ          ")
    print("==================================================")
    if in_pz:
        print("[OK] Icone de PZ DETECTADO na barra de status!")
        print("  - Estado: O personagem ESTA em Protection Zone (PZ)!")
    else:
        print("[X] Icone de PZ NAO localizado.")
        print("  - Estado: O personagem NAO esta em Protection Zone (PZ).")
    print("==================================================")

if __name__ == "__main__":
    main()
