from dataclasses import dataclass


@dataclass(frozen=True)
class MarkerDetection:
    """Template encontrado no minimapa; ``center`` é local à ROI do minimapa."""

    template_id: str
    center: tuple[int, int]
    confidence: float

    def __post_init__(self) -> None:
        if not self.template_id:
            raise ValueError("template_id do marcador não pode ser vazio")
        if self.center[0] < 0 or self.center[1] < 0:
            raise ValueError("o centro do marcador não pode ter coordenadas negativas")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("a confiança do marcador deve estar entre 0.0 e 1.0")


@dataclass(frozen=True)
class MinimapBounds:
    """Limites da ROI em pixels absolutos relativos ao frame do Projetor."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.x < 0 or self.y < 0:
            raise ValueError("as coordenadas do minimapa não podem ser negativas")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("as dimensões do minimapa devem ser maiores que zero")


@dataclass(frozen=True)
class MinimapState:
    """Snapshot imutável da percepção do minimapa no frame atual.

    ``center`` e os centros em ``markers`` usam coordenadas locais à ROI. Para
    obter uma coordenada absoluta no frame, some ``bounds.x`` e ``bounds.y``.
    """

    available: bool
    bounds: MinimapBounds | None
    center: tuple[int, int] | None
    markers: tuple[MarkerDetection, ...] = ()
    cross_confidence: float | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.available:
            if self.bounds is None or self.center is None:
                raise ValueError("um minimapa disponível requer limites e centro")
            if self.reason is not None:
                raise ValueError("um minimapa disponível não pode ter motivo de indisponibilidade")
        elif self.markers:
            raise ValueError("um minimapa indisponível não pode conter marcadores")
        if self.cross_confidence is not None and not 0.0 <= self.cross_confidence <= 1.0:
            raise ValueError("a confiança do cross deve estar entre 0.0 e 1.0")

    @classmethod
    def unavailable(cls, reason: str) -> "MinimapState":
        return cls(available=False, bounds=None, center=None, reason=reason)
