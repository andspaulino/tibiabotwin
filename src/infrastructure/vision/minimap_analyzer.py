from pathlib import Path
from typing import Mapping

import cv2
import numpy as np

from src.domain.minimap import MarkerDetection, MinimapBounds, MinimapState
from src.domain.roi import InvalidROIError, RelativeROI, ROIResolver


class MinimapAnalyzer:
    """Percebe marcadores no frame compartilhado sem conhecer a rota ou gerar ações."""

    def __init__(self, nms_distance_pixels: float = 4.0):
        if nms_distance_pixels < 0:
            raise ValueError("nms_distance_pixels não pode ser negativo")
        self.nms_distance_pixels = nms_distance_pixels

    def analyze(
        self,
        frame: np.ndarray | None,
        minimap_roi: RelativeROI,
        marker_templates: Mapping[str, str],
        match_threshold: float,
        *,
        validate_cross: bool = False,
        cross_template_path: str | None = None,
        cross_match_threshold: float = 0.88,
    ) -> MinimapState:
        """Retorna o estado do minimapa para um único frame já capturado.

        Os templates são deliberadamente recebidos como dados: a classe não lê a
        configuração da aplicação nem aplica regras de waypoint.
        """
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0 or frame.ndim < 2:
            return MinimapState.unavailable("frame do minimapa inválido")
        if not 0.0 <= match_threshold <= 1.0:
            return MinimapState.unavailable("limite de correspondência do minimapa inválido")
        if not 0.0 <= cross_match_threshold <= 1.0:
            return MinimapState.unavailable("limite de correspondência do cross inválido")

        height, width = frame.shape[:2]
        try:
            roi = ROIResolver.resolve(minimap_roi, width, height)
        except InvalidROIError as error:
            return MinimapState.unavailable(f"ROI do minimapa inválida: {error}")

        minimap = frame[roi.top:roi.top + roi.height, roi.left:roi.left + roi.width]
        if minimap.size == 0:
            return MinimapState.unavailable("ROI do minimapa está vazia")

        cross_confidence: float | None = None
        if validate_cross:
            if not cross_template_path:
                return MinimapState.unavailable("validação do cross ativada sem template")
            cross_confidence = self._best_confidence(minimap, cross_template_path)
            if cross_confidence is None:
                return MinimapState.unavailable("template cross indisponível ou incompatível com a ROI")
            if cross_confidence < cross_match_threshold:
                return MinimapState.unavailable("layout do minimapa não validado pelo cross")

        markers: list[MarkerDetection] = []
        for template_id, template_path in marker_templates.items():
            markers.extend(self._find_all(template_id, minimap, template_path, match_threshold))

        return MinimapState(
            available=True,
            bounds=MinimapBounds(x=roi.left, y=roi.top, width=roi.width, height=roi.height),
            center=(roi.width // 2, roi.height // 2),
            markers=tuple(markers),
            cross_confidence=cross_confidence,
        )

    def _find_all(
        self,
        template_id: str,
        image: np.ndarray,
        template_path: str,
        threshold: float,
    ) -> list[MarkerDetection]:
        template = self._load_template(template_path)
        if template is None or not template_id:
            return []
        if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
            return []

        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        candidates = np.argwhere(result >= threshold)
        ordered = sorted(candidates, key=lambda point: float(result[point[0], point[1]]), reverse=True)
        accepted_centers: list[tuple[int, int]] = []
        detections: list[MarkerDetection] = []
        template_height, template_width = template.shape[:2]

        for top, left in ordered:
            center = (int(left + template_width // 2), int(top + template_height // 2))
            if any(self._is_duplicate(center, accepted) for accepted in accepted_centers):
                continue
            accepted_centers.append(center)
            detections.append(
                MarkerDetection(
                    template_id=template_id,
                    center=center,
                    confidence=float(result[top, left]),
                )
            )
        return detections

    def _best_confidence(self, image: np.ndarray, template_path: str) -> float | None:
        template = self._load_template(template_path)
        if template is None or template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
            return None
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        return float(cv2.minMaxLoc(result)[1])

    def _is_duplicate(self, first: tuple[int, int], second: tuple[int, int]) -> bool:
        return float(np.hypot(first[0] - second[0], first[1] - second[1])) <= self.nms_distance_pixels

    @staticmethod
    def _load_template(template_path: str) -> np.ndarray | None:
        path = Path(template_path)
        if not path.is_file():
            return None
        return cv2.imread(str(path), cv2.IMREAD_COLOR)
