from dataclasses import dataclass
from enum import Enum

from src.domain.actions import BotAction


class WaypointType(Enum):
    MARKER_CLICK = "marker_click"
    STAND = "stand"
    ACTION = "action"
    LABEL = "label"
    GOTO = "goto"


@dataclass(frozen=True)
class RelativeRegion:
    """Região relativa à ROI do minimapa usada para desambiguar marcadores."""

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.x <= 1.0 or not 0.0 <= self.y <= 1.0:
            raise ValueError("a região esperada deve iniciar entre 0.0 e 1.0")
        if not 0.0 < self.width <= 1.0 or not 0.0 < self.height <= 1.0:
            raise ValueError("a região esperada deve ter dimensões entre 0.0 e 1.0")
        if self.x + self.width > 1.0 or self.y + self.height > 1.0:
            raise ValueError("a região esperada não pode ultrapassar a ROI do minimapa")


@dataclass(frozen=True)
class RouteSettings:
    match_threshold: float
    arrival_radius_pixels: float
    progress_epsilon_pixels: float
    stuck_timeout_ms: int
    click_cooldown_ms: int
    max_retries: int
    marker_thresholds: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.match_threshold <= 1.0:
            raise ValueError("match_threshold deve estar entre 0.0 e 1.0")
        if self.arrival_radius_pixels <= 0:
            raise ValueError("arrival_radius_pixels deve ser maior que zero")
        if self.progress_epsilon_pixels < 0:
            raise ValueError("progress_epsilon_pixels não pode ser negativo")
        if self.stuck_timeout_ms <= 0 or self.click_cooldown_ms < 0 or self.max_retries < 0:
            raise ValueError("tempos e retentativas da rota são inválidos")
        marker_ids = [marker_id for marker_id, _ in self.marker_thresholds]
        if len(set(marker_ids)) != len(marker_ids):
            raise ValueError("marker_thresholds não pode conter IDs duplicados")
        for marker_id, threshold in self.marker_thresholds:
            if not marker_id or not 0.0 <= threshold <= 1.0:
                raise ValueError("marker_thresholds contém valor inválido")

    def threshold_for(self, marker_id: str | None) -> float:
        return dict(self.marker_thresholds).get(marker_id or "", self.match_threshold)


@dataclass(frozen=True)
class HuntRoute:
    hunt_name: str
    version: int
    loop: bool
    settings: RouteSettings
    waypoints: tuple["Waypoint", ...]

    def __post_init__(self) -> None:
        if not self.hunt_name.strip():
            raise ValueError("o nome da rota não pode ser vazio")
        if self.version != 1:
            raise ValueError("a versão da rota não é suportada")
        if not self.waypoints:
            raise ValueError("a rota deve possuir ao menos um waypoint")


@dataclass(frozen=True)
class Waypoint:
    id: str
    type: WaypointType
    marker: str | None
    expected_region: RelativeRegion | None
    match_threshold: float | None = None
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("o id do waypoint não pode ser vazio")
        if self.type == WaypointType.MARKER_CLICK:
            if not self.marker:
                raise ValueError("MARKER_CLICK exige um marcador")
            if self.expected_region is None:
                raise ValueError("MARKER_CLICK exige uma região esperada")
        if self.match_threshold is not None and not 0.0 <= self.match_threshold <= 1.0:
            raise ValueError("o threshold do waypoint deve estar entre 0.0 e 1.0")


class CavebotStatus(Enum):
    INACTIVE = "inactive"
    SEARCHING_MARKER = "searching_marker"
    NAVIGATING = "navigating"
    ARRIVED = "arrived"
    WAITING_RETRY = "waiting_retry"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    STUCK = "stuck"
    ERROR = "error"


@dataclass(frozen=True)
class MovementState:
    waypoint_id: str
    best_distance: float | None
    last_distance: float | None
    last_progress_at: float
    retry_count: int = 0
    click_sent_at: float | None = None


@dataclass(frozen=True)
class CavebotIntent:
    active: bool
    movement_requested: bool
    action: BotAction | None
    status: CavebotStatus
    reason: str


@dataclass(frozen=True)
class StuckEvaluation:
    state: MovementState
    status: CavebotStatus
    reason: str
