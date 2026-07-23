import time

from src.bot.cavebot.marker_selector import MarkerSelector
from src.bot.cavebot.models import CavebotIntent, CavebotStatus, HuntRoute, MovementState, RelativeRegion, RouteSettings, Waypoint, WaypointType
from src.bot.cavebot.route_runner import RouteRunner
from src.bot.cavebot.movement_controller import MovementController
from src.bot.cavebot.stuck_detector import StuckDetector
from src.config.models import CavebotConfig, MinimapConfig
from src.domain.game_state import GameState


class CavebotController:
    """Orquestra um waypoint de marcador sem acessar captura ou executar inputs."""

    def __init__(
        self,
        config: CavebotConfig,
        minimap_config: MinimapConfig,
        route: HuntRoute | None = None,
    ):
        self.config = config
        self.minimap_config = minimap_config
        self.route_runner = RouteRunner(route) if route is not None else None
        self.selector = MarkerSelector()
        self.movement = MovementController()
        self.stuck_detector = StuckDetector()
        self.movement_state: MovementState | None = None
        self._last_request_at: float | None = None

    def evaluate(self, game_state: GameState) -> CavebotIntent:
        if self.route_runner is None and not self.config.enabled:
            return CavebotIntent(False, False, None, CavebotStatus.INACTIVE, "Cavebot desativado na configuração")
        if self.route_runner is not None and self.route_runner.completed:
            return CavebotIntent(True, False, None, CavebotStatus.COMPLETED, "Rota concluída")
        if not game_state.minimap.available:
            return CavebotIntent(True, False, None, CavebotStatus.SEARCHING_MARKER, "Minimapa indisponível")

        if self.route_runner is not None:
            waypoint = self.route_runner.current_waypoint
            assert waypoint is not None
            settings = self.route_runner.route.settings
        else:
            waypoint = Waypoint(
                id="observe-flag",
                type=WaypointType.MARKER_CLICK,
                marker=self.config.marker,
                expected_region=RelativeRegion(
                    self.config.expected_region.x,
                    self.config.expected_region.y,
                    self.config.expected_region.width,
                    self.config.expected_region.height,
                ),
                description="Waypoint de observação configurado",
            )
            settings = RouteSettings(
                match_threshold=self.minimap_config.match_threshold,
                arrival_radius_pixels=self.config.arrival_radius_pixels,
                progress_epsilon_pixels=self.config.progress_epsilon_pixels,
                stuck_timeout_ms=self.config.stuck_timeout_ms,
                click_cooldown_ms=self.config.click_cooldown_ms,
                max_retries=self.config.max_retries,
            )
        marker = self.selector.select(game_state.minimap, waypoint, settings.threshold_for(waypoint.marker))
        intent = self.movement.evaluate(game_state.minimap, waypoint, marker, settings)
        if intent.status == CavebotStatus.SEARCHING_MARKER:
            # Frames sem marcador não representam progresso nem travamento.
            return intent
        if intent.status == CavebotStatus.ARRIVED:
            self.movement_state = None
            if self.route_runner is not None:
                next_waypoint = self.route_runner.mark_arrived()
                suffix = "rota concluída" if next_waypoint is None else f"próximo waypoint: {next_waypoint.id}"
                return CavebotIntent(True, False, None, CavebotStatus.ARRIVED, f"{intent.reason}; {suffix}")
            return intent
        if intent.action is None or marker is None:
            return intent

        now = time.monotonic()
        current_state = self.movement_state or MovementState(
            waypoint_id=waypoint.id,
            best_distance=None,
            last_distance=None,
            last_progress_at=now,
        )
        distance = self.movement.distance_to_center(game_state.minimap, marker)
        stuck = self.stuck_detector.update(current_state, distance, settings, now)
        self.movement_state = stuck.state
        if stuck.status == CavebotStatus.STUCK:
            return CavebotIntent(True, False, None, CavebotStatus.STUCK, stuck.reason)
        if stuck.status == CavebotStatus.WAITING_RETRY:
            intent = CavebotIntent(True, True, intent.action, CavebotStatus.WAITING_RETRY, stuck.reason)

        if self._last_request_at is not None and (now - self._last_request_at) * 1000.0 < settings.click_cooldown_ms:
            return CavebotIntent(True, True, None, CavebotStatus.NAVIGATING, "Aguardando cooldown de movimento")
        return intent

    def record_simulated_request(self) -> None:
        """Registra o intervalo apenas após o engine encaminhar uma simulação autorizada."""
        self._last_request_at = time.monotonic()
