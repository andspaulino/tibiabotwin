from src.bot.cavebot.cavebot_controller import CavebotController
from src.bot.cavebot.models import CavebotIntent, CavebotStatus
from src.domain.bot_state import BotMode, BotState
from src.domain.game_state import GameState
from src.utils.logger import logger


class CavebotModule:
    """Módulo com ciclo de vida e duas fases de decisão para navegação por minimapa."""

    def __init__(self, controller: CavebotController):
        self.controller = controller
        self.enabled = False

    def start(self) -> None:
        """Prepara o módulo, mantendo-o inativo até o toggle explícito."""
        self.enabled = False
        if self._is_available:
            logger.log("CAVEBOT", "Módulo Cavebot pronto e desativado; aguardando toggle manual.")
        else:
            logger.log("CAVEBOT", "Módulo Cavebot indisponível: nenhuma hunt foi carregada.")

    def toggle(self) -> bool:
        """Alterna a navegação sem executar ou autorizar ação no evento."""
        if not self._is_available:
            logger.log("CAVEBOT", "Não foi possível ativar: nenhuma hunt foi carregada.", level="WARNING")
            return False
        self.enabled = not self.enabled
        status = "ativado" if self.enabled else "desativado"
        logger.log("CAVEBOT", f"Módulo Cavebot {status} pelo toggle.")
        return self.enabled

    def stop(self) -> None:
        was_enabled = self.enabled
        self.enabled = False
        if was_enabled:
            logger.log("CAVEBOT", "Módulo Cavebot desativado no encerramento.")

    @property
    def _is_available(self) -> bool:
        return self.controller.route_runner is not None

    def inspect(self, game_state: GameState) -> CavebotIntent:
        """Inspeciona a rota antes da máquina de estados, sem executar ou autorizar ação."""
        if not self.enabled:
            return CavebotIntent(False, False, None, CavebotStatus.INACTIVE, "Módulo Cavebot desativado")
        return self.controller.evaluate(game_state)

    def propose(self, game_state: GameState, bot_state: BotState, inspected: CavebotIntent) -> CavebotIntent:
        """Produz ação somente após a decisão do modo global do ciclo atual."""
        del game_state
        if not self.enabled or not inspected.active:
            return inspected
        if inspected.status in {
            CavebotStatus.ARRIVED,
            CavebotStatus.COMPLETED,
            CavebotStatus.STUCK,
            CavebotStatus.INACTIVE,
        }:
            return inspected
        if bot_state.current_mode != BotMode.MOVING:
            return self.controller.suspend(bot_state.current_mode)
        return inspected

    def record_request(self) -> None:
        self.controller.record_request()

    def record_simulated_request(self) -> None:
        self.controller.record_simulated_request()
