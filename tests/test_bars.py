import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from src.utils.screen import (
    get_hp_percentage,
    get_mp_percentage,
    get_status_bar_activity,
    HP_BAR_ROI,
    MP_BAR_ROI,
    STATUS_BAR_ROI
)

def main():
    image_path = "screenshot_obs_clean.png"
    if not os.path.exists(image_path):
        print(f"[X] Arquivo '{image_path}' nao encontrado na raiz.")
        return

    print("==================================================")
    print("  Teste de Identificacao de HP, Mana e Status     ")
    print("==================================================")
    
    img = cv2.imread(image_path)
    if img is None:
        print("[X] Nao foi possivel ler a imagem.")
        return

    hp_pct = get_hp_percentage(img)
    mp_pct = get_mp_percentage(img)
    status_info = get_status_bar_activity(img)

    print(f"Barra de Vida (HP)  : {hp_pct * 100:.2f}% (ROI: {HP_BAR_ROI})")
    print(f"Barra de Mana (MP)  : {mp_pct * 100:.2f}% (ROI: {MP_BAR_ROI})")
    print(f"Barra de Status     : Icones Ativos = {status_info['active']} ({status_info['active_pixels']} px) (ROI: {STATUS_BAR_ROI})")
    print("==================================================")

if __name__ == "__main__":
    main()
