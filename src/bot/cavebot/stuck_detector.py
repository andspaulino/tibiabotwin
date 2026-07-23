from src.bot.cavebot.models import CavebotStatus, MovementState, RouteSettings, StuckEvaluation


class StuckDetector:
    """Acompanha progresso por distância; nunca conclui ou avança um waypoint."""

    def update(
        self,
        state: MovementState,
        distance: float,
        settings: RouteSettings,
        now: float,
    ) -> StuckEvaluation:
        best_distance = state.best_distance
        if best_distance is None:
            updated = MovementState(state.waypoint_id, distance, distance, now, state.retry_count, state.click_sent_at)
            return StuckEvaluation(updated, CavebotStatus.NAVIGATING, "Primeira distância observada")

        if best_distance - distance >= settings.progress_epsilon_pixels:
            updated = MovementState(state.waypoint_id, distance, distance, now, state.retry_count, state.click_sent_at)
            return StuckEvaluation(updated, CavebotStatus.NAVIGATING, "Progresso confirmado")

        updated = MovementState(
            state.waypoint_id,
            best_distance,
            distance,
            state.last_progress_at,
            state.retry_count,
            state.click_sent_at,
        )
        elapsed_ms = (now - state.last_progress_at) * 1000.0
        if elapsed_ms < settings.stuck_timeout_ms:
            return StuckEvaluation(updated, CavebotStatus.NAVIGATING, "Aguardando progresso")
        if state.retry_count >= settings.max_retries:
            return StuckEvaluation(updated, CavebotStatus.STUCK, "Sem progresso e máximo de retentativas atingido")

        retry_state = MovementState(
            state.waypoint_id,
            best_distance,
            distance,
            now,
            state.retry_count + 1,
            state.click_sent_at,
        )
        return StuckEvaluation(retry_state, CavebotStatus.WAITING_RETRY, "Sem progresso; retentativa solicitada")
