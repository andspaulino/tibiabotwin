import time

from src.bot.cavebot.marker_selector import MarkerSelector
from src.bot.cavebot.models import CavebotIntent, CavebotStatus, RelativeRegion, RouteSettings, Waypoint, WaypointType
from src.bot.cavebot.movement_controller import MovementController
from src.config.models import CavebotConfig, MinimapConfig
from src.domain.game_state import GameState


class CavebotController:
    """Orquestra um waypoint de marcador sem acessar captura ou executar inputs."""

    def __init__(self, config: CavebotConfig, minimap_config: MinimapConfig):
        self.config = config
        self.minimap_config = minimap_config
        self.selector = MarkerSelector()
        self.movement = MovementController()
        self._last_request_at: float | None = None

    def evaluate(self, game_state: GameState) -> CavebotIntent:
        if not self.config.enabled:
            return CavebotIntent(False, False, None, CavebotStatus.INACTIVE, "Cavebot desativado na configuração")
        if not game_state.minimap.available:
            return CavebotIntent(True, False, None, CavebotStatus.SEARCHING_MARKER, "Minimapa indisponível")

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
        marker = self.selector.select(game_state.minimap, waypoint, settings.match_threshold)
        intent = self.movement.evaluate(game_state.minimap, waypoint, marker, settings)
        if intent.action is None:
            return intent

        now = time.monotonic()
        if self._last_request_at is not None and (now - self._last_request_at) * 1000.0 < settings.click_cooldown_ms:
            return CavebotIntent(True, True, None, CavebotStatus.NAVIGATING, "Aguardando cooldown de movimento")
        return intent

    def record_simulated_request(self) -> None:
        """Registra o intervalo apenas após o engine encaminhar uma simulação autorizada."""
        self._last_request_at = time.monotonic()
