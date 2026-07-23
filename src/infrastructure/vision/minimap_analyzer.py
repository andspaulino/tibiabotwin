from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import cv2
import numpy as np

from src.domain.minimap import MarkerDetection, MarkerMatchDiagnostic, MinimapBounds, MinimapState
from src.domain.roi import InvalidROIError, RelativeROI, ROIResolver


@dataclass(frozen=True)
class _TemplateImage:
    image: np.ndarray
    mask: np.ndarray | None = None


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
        match_threshold: float | Mapping[str, float],
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
        if isinstance(match_threshold, Mapping):
            thresholds = dict(match_threshold)
            if set(thresholds) != set(marker_templates) or any(
                not 0.0 <= threshold <= 1.0 for threshold in thresholds.values()
            ):
                return MinimapState.unavailable("limites por marcador do minimapa inválidos")
        elif 0.0 <= match_threshold <= 1.0:
            thresholds = {template_id: match_threshold for template_id in marker_templates}
        else:
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
        match_diagnostics: list[MarkerMatchDiagnostic] = []
        for template_id, template_path in marker_templates.items():
            detections, best_confidence = self._find_all(
                template_id,
                minimap,
                template_path,
                thresholds[template_id],
            )
            markers.extend(detections)
            match_diagnostics.append(
                MarkerMatchDiagnostic(template_id, best_confidence, thresholds[template_id])
            )

        return MinimapState(
            available=True,
            bounds=MinimapBounds(x=roi.left, y=roi.top, width=roi.width, height=roi.height),
            center=(roi.width // 2, roi.height // 2),
            markers=tuple(markers),
            cross_confidence=cross_confidence,
            match_diagnostics=tuple(match_diagnostics),
        )

    def _find_all(
        self,
        template_id: str,
        image: np.ndarray,
        template_path: str,
        threshold: float,
    ) -> tuple[list[MarkerDetection], float | None]:
        template = self._load_template(template_path)
        if template is None or not template_id:
            return [], None
        if template.image.shape[0] > image.shape[0] or template.image.shape[1] > image.shape[1]:
            return [], None

        result = self._match_template(image, template)
        best_confidence = max(0.0, float(np.max(result)))
        candidates = np.argwhere(result >= threshold)
        ordered = sorted(candidates, key=lambda point: float(result[point[0], point[1]]), reverse=True)
        accepted_centers: list[tuple[int, int]] = []
        detections: list[MarkerDetection] = []
        template_height, template_width = template.image.shape[:2]

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
        return detections, best_confidence

    def _best_confidence(self, image: np.ndarray, template_path: str) -> float | None:
        template = self._load_template(template_path)
        if template is None or template.image.shape[0] > image.shape[0] or template.image.shape[1] > image.shape[1]:
            return None
        result = self._match_template(image, template)
        finite_values = result[np.isfinite(result)]
        return float(np.max(finite_values)) if finite_values.size else None

    def _is_duplicate(self, first: tuple[int, int], second: tuple[int, int]) -> bool:
        return float(np.hypot(first[0] - second[0], first[1] - second[1])) <= self.nms_distance_pixels

    @staticmethod
    def _match_template(image: np.ndarray, template: _TemplateImage) -> np.ndarray:
        result = cv2.matchTemplate(
            image,
            template.image,
            cv2.TM_CCOEFF_NORMED,
            mask=template.mask,
        )
        normalized = np.nan_to_num(result, nan=-1.0, posinf=-1.0, neginf=-1.0)
        return np.clip(normalized, -1.0, 1.0)

    @staticmethod
    def _load_template(template_path: str) -> _TemplateImage | None:
        path = Path(template_path)
        if not path.is_file():
            return None

        loaded = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if loaded is None:
            return None
        if loaded.ndim == 2:
            return _TemplateImage(cv2.cvtColor(loaded, cv2.COLOR_GRAY2BGR))
        if loaded.shape[2] == 4:
            alpha = loaded[:, :, 3]
            if not np.any(alpha):
                return None
            return _TemplateImage(loaded[:, :, :3], alpha)
        if loaded.shape[2] == 3:
            return _TemplateImage(loaded)
        return None
