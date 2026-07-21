import cv2

img = cv2.imread("templates/target_red.png")
if img is not None:
    h, w, c = img.shape
    print(f"Dimensões originais de target_red.png: {w}x{h}")
    
    # Procura por pixels vermelhos de moldura
    # Vermelho puro: B baixo, G baixo, R alto
    red_mask = (img[:, :, 2] > 180) & (img[:, :, 1] < 50) & (img[:, :, 0] < 50)
    
    # Encontra a bounding box da moldura vermelha
    import numpy as np
    y_indices, x_indices = np.where(red_mask)
    if len(x_indices) > 0:
        min_x, max_x = np.min(x_indices), np.max(x_indices)
        min_y, max_y = np.min(y_indices), np.max(y_indices)
        print(f"Moldura vermelha detectada: Left={min_x}, Top={min_y}, Right={max_x}, Bottom={max_y}")
        
        # Corta exatamente a caixa da moldura vermelha
        cropped_red = img[min_y:max_y+1, min_x:max_x+1]
        cv2.imwrite("templates/target_red.png", cropped_red)
        print(f"Nova imagem salva em templates/target_red.png com dimensões {cropped_red.shape[1]}x{cropped_red.shape[0]}")
    else:
        print("Nenhum pixel vermelho intenso foi encontrado.")
else:
    print("Imagem templates/target_red.png não encontrada.")
