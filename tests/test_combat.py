import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from tests.test_obs_capture import main as capture_obs_screen
from src.utils.screen import (
    has_monsters_in_battle,
    has_active_target,
    BATTLE_LIST_ROI
)

def main():
    print("==================================================")
    print("      Teste de Diagnóstico do Módulo de Combate   ")
    print("==================================================")
    
    # Captura tela ao vivo via OBS
    print("Acionando captura do OBS...")
    capture_obs_screen()

    image_path = "screenshot_obs_clean.png"
    if not os.path.exists(image_path):
        print(f"[X] Imagem '{image_path}' nao encontrada.")
        return

    img = cv2.imread(image_path)
    
    has_monsters = has_monsters_in_battle(img, BATTLE_LIST_ROI)
    has_target = has_active_target(img, BATTLE_LIST_ROI)

    print("\n--------------------------------------------------")
    print(f"ROI da Battle List : {BATTLE_LIST_ROI}")
    print(f"Monstros na Battle : {'SIM' if has_monsters else 'NAO'}")
    print(f"Alvo Ativo (Red Box): {'SIM' if has_target else 'NAO'}")
    print("==================================================")

if __name__ == "__main__":
    main()
