from math import hypot

from src.bot.cavebot.models import CavebotIntent, CavebotStatus, RouteSettings, Waypoint
from src.domain.actions import ActionPriority, ActionType, BotAction, MouseClickPayload
from src.domain.minimap import MarkerDetection, MinimapState


class MovementController:
    """Transforma um marcador já selecionado em intenção de movimento, sem executar input."""

    def evaluate(
        self,
        minimap: MinimapState,
        waypoint: Waypoint,
        marker: MarkerDetection | None,
        settings: RouteSettings,
    ) -> CavebotIntent:
        if not minimap.available or minimap.bounds is None or minimap.center is None:
            return CavebotIntent(False, False, None, CavebotStatus.ERROR, "Minimapa indisponível para movimento")
        if waypoint.type.value != "marker_click" or marker is None:
            return CavebotIntent(True, True, None, CavebotStatus.SEARCHING_MARKER, "Marcador do waypoint não encontrado com segurança")

        distance = self.distance_to_center(minimap, marker)
        if distance <= settings.arrival_radius_pixels:
            return CavebotIntent(
                True,
                False,
                None,
                CavebotStatus.ARRIVED,
                f"Waypoint {waypoint.id} chegou: distância {distance:.1f}px dentro do raio",
            )

        action = BotAction(
            action_type=ActionType.MOVE,
            priority=ActionPriority.MOVEMENT,
            payload=MouseClickPayload(
                x=minimap.bounds.x + marker.center[0],
                y=minimap.bounds.y + marker.center[1],
            ),
            reason=(
                f"Waypoint {waypoint.id}: marcador {marker.template_id} selecionado "
                f"com confiança {marker.confidence:.2f}; distância {distance:.1f}px"
            ),
            cooldown_ms=settings.click_cooldown_ms,
            cooldown_key="cavebot:movement",
        )
        return CavebotIntent(True, True, action, CavebotStatus.NAVIGATING, action.reason)

    @staticmethod
    def distance_to_center(minimap: MinimapState, marker: MarkerDetection) -> float:
        if minimap.center is None:
            raise ValueError("não é possível calcular distância sem centro do minimapa")
        return hypot(marker.center[0] - minimap.center[0], marker.center[1] - minimap.center[1])
