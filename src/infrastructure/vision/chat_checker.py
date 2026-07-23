import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Union

from src.domain.roi import RelativeROI, AbsoluteROI, ROIResolver
from src.utils.logger import logger


_template_cache = {}


def load_template(template_path: str) -> Optional[np.ndarray]:
    """Carrega e armazena em cache o template de imagem BGR."""
    if not template_path:
        return None

    if template_path in _template_cache:
        return _template_cache[template_path]

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    path = Path(template_path)
    if not path.is_absolute():
        path = project_root / path

    if not path.exists() or not path.is_file():
        return None

    template = cv2.imread(str(path))
    if template is not None:
        _template_cache[template_path] = template
    return template


def is_chat_on(
    img_bgr: np.ndarray,
    roi: Optional[Union[RelativeROI, AbsoluteROI]] = None,
    template_path: str = "templates/chat_on.png",
    threshold: float = 0.90
) -> bool:
    """
    Verifica se o chat do Tibia está no estado ON através de Template Matching estritamente com chat_on.png.
    Retorna True se e somente se o score_on >= threshold (ex: 0.90).
    Se não encontrar o template chat_on.png com score alto, retorna False (presume Chat OFF com total segurança).
    """
    if img_bgr is None or img_bgr.size == 0:
        return False

    template = load_template(template_path)
    if template is None:
        logger.log("CHAT", f"Template '{template_path}' nao encontrado; presumindo Chat OFF por seguranca.", level="WARNING")
        return False

    h_frame, w_frame = img_bgr.shape[:2]

    if roi is not None:
        abs_roi = ROIResolver.resolve(roi, w_frame, h_frame)
        crop = img_bgr[abs_roi.top:abs_roi.top + abs_roi.height, abs_roi.left:abs_roi.left + abs_roi.width]
    else:
        crop = img_bgr

    if crop.shape[0] < template.shape[0] or crop.shape[1] < template.shape[1]:
        return False

    res = cv2.matchTemplate(crop, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    is_match = float(max_val) >= threshold
    logger.log("CHAT", f"Score Chat ON: {max_val:.3f} (Threshold: {threshold}) -> {'ON' if is_match else 'OFF'}")
    return is_match


def get_chat_button_center(w_frame: int, h_frame: int, roi: Union[RelativeROI, AbsoluteROI]) -> Tuple[int, int]:
    """Calcula as coordenadas pixels (X, Y) do centro da ROI do botão do chat relativas ao frame capturado."""
    abs_roi = ROIResolver.resolve(roi, w_frame, h_frame)
    center_x = abs_roi.left + (abs_roi.width // 2)
    center_y = abs_roi.top + (abs_roi.height // 2)
    return center_x, center_y
