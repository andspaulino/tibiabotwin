import os
import cv2

image_path = "screenshot_obs_clean.png"
if os.path.exists(image_path):
    img = cv2.imread(image_path)
    h, w, c = img.shape
    print(f"Dimensões da captura: {w}x{h}")
    
    # Recorta a região direita da tela (onde fica a Battle List típica)
    right_panel = img[100:600, w-300:w]
    cv2.imwrite("scratch_battle_panel.png", right_panel)
    print("Salvo scratch_battle_panel.png para inspeção.")
else:
    print("screenshot_obs_clean.png não encontrada.")
