import os
import sys
from pathlib import Path

# Garante importações a partir do diretório raiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import cv2
import numpy as np

from src.domain.roi import RelativeROI, ROIResolver

# ROIs Padrão da Aplicação
HP_ROI = RelativeROI(0.187, 0.000, 0.281, 0.018)
MANA_ROI = RelativeROI(0.531, 0.000, 0.281, 0.018)
STATUS_BAR_ROI = RelativeROI(0.000, 0.020, 0.300, 0.050)
BATTLE_LIST_ROI = RelativeROI(0.850, 0.200, 0.140, 0.400)


def create_base_canvas(width=1920, height=1080) -> np.ndarray:
    """Cria uma tela base escura estilo Tibia."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (30, 30, 30)  # Fundo cinza escuro
    return img


def generate_hp_fixture(hp_percent: float, width=1920, height=1080) -> np.ndarray:
    img = create_base_canvas(width, height)
    abs_roi = ROIResolver.resolve(HP_ROI, width, height)

    # Desenha fundo da barra de vida
    cv2.rectangle(img, (abs_roi.left, abs_roi.top), (abs_roi.left + abs_roi.width, abs_roi.top + abs_roi.height), (10, 10, 10), -1)

    # Desenha preenchimento da vida (BGR: Verde para vida cheia/média, Vermelho para crítico)
    fill_w = int(abs_roi.width * max(0.0, min(1.0, hp_percent)))
    if fill_w > 0:
        color = (0, 220, 0) if hp_percent > 0.3 else (0, 0, 220)
        cv2.rectangle(img, (abs_roi.left, abs_roi.top), (abs_roi.left + fill_w, abs_roi.top + abs_roi.height), color, -1)

    return img


def generate_mana_fixture(mana_percent: float, width=1920, height=1080) -> np.ndarray:
    img = create_base_canvas(width, height)
    abs_roi = ROIResolver.resolve(MANA_ROI, width, height)

    # Desenha fundo da barra de mana
    cv2.rectangle(img, (abs_roi.left, abs_roi.top), (abs_roi.left + abs_roi.width, abs_roi.top + abs_roi.height), (10, 10, 10), -1)

    # Desenha preenchimento da mana (BGR: Azul)
    fill_w = int(abs_roi.width * max(0.0, min(1.0, mana_percent)))
    if fill_w > 0:
        cv2.rectangle(img, (abs_roi.left, abs_roi.top), (abs_roi.left + fill_w, abs_roi.top + abs_roi.height), (220, 100, 0), -1)

    return img


def generate_all_fixtures():
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    (fixtures_dir / "hp").mkdir(parents=True, exist_ok=True)
    (fixtures_dir / "mana").mkdir(parents=True, exist_ok=True)

    # HP
    cv2.imwrite(str(fixtures_dir / "hp" / "hp_100.png"), generate_hp_fixture(1.0))
    cv2.imwrite(str(fixtures_dir / "hp" / "hp_50.png"), generate_hp_fixture(0.5))
    cv2.imwrite(str(fixtures_dir / "hp" / "hp_20.png"), generate_hp_fixture(0.2))

    # Mana
    cv2.imwrite(str(fixtures_dir / "mana" / "mana_100.png"), generate_mana_fixture(1.0))
    cv2.imwrite(str(fixtures_dir / "mana" / "mana_30.png"), generate_mana_fixture(0.3))

    print(f"[OK] Fixtures sintéticas geradas com sucesso em '{fixtures_dir}'")


if __name__ == "__main__":
    generate_all_fixtures()
