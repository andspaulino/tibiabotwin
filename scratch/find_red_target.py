import cv2
import numpy as np

img = cv2.imread("screenshot_obs_clean.png")

# Procura por pixels de vermelho intenso de moldura de alvo (R alto, G baixo, B baixo)
red_mask = (img[:, :, 2] > 160) & (img[:, :, 1] < 50) & (img[:, :, 0] < 50)
y_indices, x_indices = np.where(red_mask)

print(f"Total de pixels vermelhos de moldura/alvo encontrados: {len(x_indices)}")
if len(x_indices) > 0:
    min_x, max_x = np.min(x_indices), np.max(x_indices)
    min_y, max_y = np.min(y_indices), np.max(y_indices)
    print(f"BBox do Alvo Vermelho: Left={min_x}, Top={min_y}, Width={max_x-min_x}, Height={max_y-min_y}")
