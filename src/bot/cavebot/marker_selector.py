from src.bot.cavebot.models import Waypoint
from src.domain.minimap import MarkerDetection, MinimapState


class MarkerSelector:
    """Seleciona um marcador sem capturar tela ou assumir um candidato ambíguo."""

    def select(
        self,
        minimap: MinimapState,
        waypoint: Waypoint,
        default_threshold: float,
    ) -> MarkerDetection | None:
        if not minimap.available or minimap.bounds is None or waypoint.marker is None:
            return None
        if waypoint.expected_region is None:
            return None

        threshold = waypoint.match_threshold if waypoint.match_threshold is not None else default_threshold
        candidates = [
            marker
            for marker in minimap.markers
            if marker.template_id == waypoint.marker
            and marker.confidence >= threshold
            and self._in_expected_region(marker, minimap, waypoint)
        ]
        if not candidates:
            return None

        candidates.sort(key=lambda marker: marker.confidence, reverse=True)
        if len(candidates) > 1 and candidates[0].confidence == candidates[1].confidence:
            return None
        return candidates[0]

    @staticmethod
    def _in_expected_region(marker: MarkerDetection, minimap: MinimapState, waypoint: Waypoint) -> bool:
        assert minimap.bounds is not None
        assert waypoint.expected_region is not None
        region = waypoint.expected_region
        normalized_x = marker.center[0] / minimap.bounds.width
        normalized_y = marker.center[1] / minimap.bounds.height
        return (
            region.x <= normalized_x <= region.x + region.width
            and region.y <= normalized_y <= region.y + region.height
        )
