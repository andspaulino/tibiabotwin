from src.bot.cavebot.models import HuntRoute, Waypoint


class RouteRunner:
    """Controla o waypoint atual e só progride após chegada confirmada visualmente."""

    def __init__(self, route: HuntRoute):
        self.route = route
        self.current_index = 0
        self.completed = False

    @property
    def current_waypoint(self) -> Waypoint | None:
        if self.completed:
            return None
        return self.route.waypoints[self.current_index]

    def mark_arrived(self) -> Waypoint | None:
        """Avança uma posição somente quando o controlador confirma a chegada."""
        if self.completed:
            return None
        next_index = self.current_index + 1
        if next_index < len(self.route.waypoints):
            self.current_index = next_index
            return self.current_waypoint
        if self.route.loop:
            self.current_index = 0
            return self.current_waypoint
        self.completed = True
        return None

    def reset_movement(self) -> None:
        """Mantém o waypoint atual e deixa a reaquisição visual para o controlador."""
        return None
