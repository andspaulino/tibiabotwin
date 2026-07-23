from dataclasses import dataclass

from src.infrastructure.window.base import WindowClientArea


class CoordinateMappingError(ValueError):
    """Indica que uma coordenada não pode ser convertida com segurança."""


@dataclass(frozen=True)
class ScreenPoint:
    x: int
    y: int


class FrameToWindowMapper:
    """Converte um ponto do frame para a área cliente equivalente na tela."""

    def __init__(self, aspect_ratio_tolerance: float = 0.02):
        if aspect_ratio_tolerance < 0:
            raise ValueError("aspect_ratio_tolerance não pode ser negativa")
        self.aspect_ratio_tolerance = aspect_ratio_tolerance

    def map_point(
        self,
        frame_x: int,
        frame_y: int,
        frame_width: int,
        frame_height: int,
        target: WindowClientArea,
    ) -> ScreenPoint:
        if frame_width <= 1 or frame_height <= 1:
            raise CoordinateMappingError("o frame deve possuir dimensões maiores que 1 pixel")
        if not 0 <= frame_x < frame_width or not 0 <= frame_y < frame_height:
            raise CoordinateMappingError("o ponto está fora dos limites do frame")

        frame_aspect = frame_width / frame_height
        target_aspect = target.width / target.height
        relative_difference = abs(frame_aspect - target_aspect) / frame_aspect
        if relative_difference > self.aspect_ratio_tolerance:
            raise CoordinateMappingError(
                "aspectos incompatíveis entre o frame do Projetor "
                f"({frame_width}x{frame_height}) e a área cliente do Tibia "
                f"({target.width}x{target.height})"
            )

        normalized_x = frame_x / (frame_width - 1)
        normalized_y = frame_y / (frame_height - 1)
        screen_x = target.left + round(normalized_x * (target.width - 1))
        screen_y = target.top + round(normalized_y * (target.height - 1))
        return ScreenPoint(screen_x, screen_y)
