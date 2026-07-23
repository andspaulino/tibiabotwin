import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from src.bot.cavebot.cavebot_controller import CavebotController
from src.bot.cavebot.models import CavebotIntent, CavebotStatus
from src.bot.cavebot.module import CavebotModule
from src.domain.bot_state import BotMode, BotState
from src.domain.capture_status import FrameStatus
from src.domain.game_state import CaptureState, GameState, PlayerState, TargetState, WindowState
from src.domain.minimap import MinimapState


class TestCavebotModule(unittest.TestCase):
    def setUp(self) -> None:
        now = datetime.now(timezone.utc)
        self.game_state = GameState(
            timestamp=now,
            capture=CaptureState(FrameStatus.VALID, now, 0.1),
            window=WindowState(True, False, True),
            player=PlayerState(0.9, 0.9, False),
            target=TargetState(False, False),
            minimap=MinimapState.unavailable("fixture indisponível"),
        )
        self.controller = Mock(spec=CavebotController)
        self.controller.route_runner = object()
        self.module = CavebotModule(self.controller)

    @staticmethod
    def _bot_state(mode: BotMode) -> BotState:
        return BotState(current_mode=mode, previous_mode=BotMode.IDLE)

    def test_disabled_module_returns_inactive_without_inspecting_controller(self) -> None:
        intent = self.module.inspect(self.game_state)

        self.assertEqual(intent.status, CavebotStatus.INACTIVE)
        self.assertFalse(intent.active)
        self.controller.evaluate.assert_not_called()

    def test_active_module_delegates_inspection_and_preserves_moving_action(self) -> None:
        inspected = CavebotIntent(True, True, Mock(), CavebotStatus.NAVIGATING, "navegando")
        self.controller.evaluate.return_value = inspected
        self.module.start()
        self.assertFalse(self.module.enabled)
        self.assertTrue(self.module.toggle())

        result = self.module.inspect(self.game_state)
        proposed = self.module.propose(self.game_state, self._bot_state(BotMode.MOVING), result)

        self.assertIs(result, inspected)
        self.assertIs(proposed, inspected)
        self.controller.evaluate.assert_called_once_with(self.game_state)
        self.controller.suspend.assert_not_called()

    def test_active_module_suspends_navigation_outside_moving_mode(self) -> None:
        inspected = CavebotIntent(True, True, Mock(), CavebotStatus.NAVIGATING, "navegando")
        suspended = CavebotIntent(True, False, None, CavebotStatus.SUSPENDED, "combate")
        self.module.start()
        self.assertTrue(self.module.toggle())
        self.controller.suspend.return_value = suspended

        result = self.module.propose(self.game_state, self._bot_state(BotMode.COMBAT), inspected)

        self.assertIs(result, suspended)
        self.controller.suspend.assert_called_once_with(BotMode.COMBAT)

    def test_terminal_intent_is_not_replaced_by_suspension(self) -> None:
        self.module.start()
        self.assertTrue(self.module.toggle())
        arrived = CavebotIntent(True, False, None, CavebotStatus.ARRIVED, "chegou")

        result = self.module.propose(self.game_state, self._bot_state(BotMode.IN_PROTECTION_ZONE), arrived)

        self.assertIs(result, arrived)
        self.controller.suspend.assert_not_called()

    def test_stop_disables_module_and_forwards_simulation_recording(self) -> None:
        self.module.start()
        self.assertTrue(self.module.toggle())
        self.module.record_simulated_request()
        self.module.stop()
        intent = self.module.inspect(self.game_state)

        self.controller.record_simulated_request.assert_called_once_with()
        self.assertEqual(intent.status, CavebotStatus.INACTIVE)
        self.controller.evaluate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
