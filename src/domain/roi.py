from dataclasses import dataclass
from typing import Dict, Union, Any


class InvalidROIError(ValueError):
    """Exceção lançada quando uma ROI possui dimensões ou coordenadas inválidas."""
    pass


@dataclass(frozen=True)
class RelativeROI:
    """Representa uma Região de Interesse proporcional (valores entre 0.0 e 1.0)."""
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self):
        if not (0.0 <= self.x <= 1.0):
            raise InvalidROIError(f"Coordenada x deve estar entre 0.0 e 1.0, recebido: {self.x}")
        if not (0.0 <= self.y <= 1.0):
            raise InvalidROIError(f"Coordenada y deve estar entre 0.0 e 1.0, recebido: {self.y}")
        if not (0.0 < self.width <= 1.0):
            raise InvalidROIError(f"Largura width deve estar entre 0.0 e 1.0, recebida: {self.width}")
        if not (0.0 < self.height <= 1.0):
            raise InvalidROIError(f"Altura height deve estar entre 0.0 e 1.0, recebida: {self.height}")
        if self.x + self.width > 1.001:
            raise InvalidROIError(f"ROI ultrapassa limite horizontal (x + width = {self.x + self.width:.3f} > 1.0)")
        if self.y + self.height > 1.001:
            raise InvalidROIError(f"ROI ultrapassa limite vertical (y + height = {self.y + self.height:.3f} > 1.0)")


@dataclass(frozen=True)
class AbsoluteROI:
    """Representa uma Região de Interesse em pixels absolutos."""
    top: int
    left: int
    width: int
    height: int

    def __post_init__(self):
        if self.top < 0 or self.left < 0:
            raise InvalidROIError(f"Coordenadas top e left não podem ser negativas: top={self.top}, left={self.left}")
        if self.width <= 0 or self.height <= 0:
            raise InvalidROIError(f"Largura e altura devem ser > 0: width={self.width}, height={self.height}")

    def to_dict(self) -> Dict[str, int]:
        """Retorna representação em dicionário legada ('top', 'left', 'width', 'height')."""
        return {
            "top": self.top,
            "left": self.left,
            "width": self.width,
            "height": self.height,
        }


class ROIResolver:
    """Classe responsável por converter e validar ROIs relativas/absolutas com base no tamanho do frame."""

    @staticmethod
    def resolve(
        roi: Union[RelativeROI, AbsoluteROI, Dict[str, Any]],
        frame_width: int,
        frame_height: int
    ) -> AbsoluteROI:
        """
        Converte uma ROI relativa ou legada em uma AbsoluteROI ajustada às dimensões do frame.
        """
        if frame_width <= 0 or frame_height <= 0:
            raise InvalidROIError(f"Dimensões inválidas do frame: {frame_width}x{frame_height}")

        if isinstance(roi, RelativeROI):
            left = int(round(roi.x * frame_width))
            top = int(round(roi.y * frame_height))
            width = int(round(roi.width * frame_width))
            height = int(round(roi.height * frame_height))

            # Clamping para evitar estouro por arredondamento
            left = max(0, min(frame_width - 1, left))
            top = max(0, min(frame_height - 1, top))
            width = max(1, min(frame_width - left, width))
            height = max(1, min(frame_height - top, height))

            return AbsoluteROI(top=top, left=left, width=width, height=height)

        elif isinstance(roi, AbsoluteROI):
            # Clamping para garantir que cabe dentro do frame
            left = max(0, min(frame_width - 1, roi.left))
            top = max(0, min(frame_height - 1, roi.top))
            width = max(1, min(frame_width - left, roi.width))
            height = max(1, min(frame_height - top, roi.height))

            return AbsoluteROI(top=top, left=left, width=width, height=height)

        elif isinstance(roi, dict):
            # Dicionário relativo {'x': ..., 'y': ..., 'width': ..., 'height': ...}
            if "x" in roi and "y" in roi:
                rel_roi = RelativeROI(
                    x=float(roi["x"]),
                    y=float(roi["y"]),
                    width=float(roi["width"]),
                    height=float(roi["height"])
                )
                return ROIResolver.resolve(rel_roi, frame_width, frame_height)
            # Dicionário absoluto legado {'top': ..., 'left': ..., 'width': ..., 'height': ...}
            elif "top" in roi and "left" in roi:
                abs_roi = AbsoluteROI(
                    top=int(roi["top"]),
                    left=int(roi["left"]),
                    width=int(roi["width"]),
                    height=int(roi["height"])
                )
                return ROIResolver.resolve(abs_roi, frame_width, frame_height)
            else:
                raise InvalidROIError(f"Formato de dicionário de ROI desconhecido: {roi}")
        else:
            raise InvalidROIError(f"Tipo de ROI não suportado: {type(roi)}")
