import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from src.bot.cavebot.cavebot_controller import CavebotController
from src.config.models import CavebotConfig, MinimapConfig
from src.domain.bot_state import BotMode
from src.domain.capture_status import FrameStatus
from src.domain.game_state import CaptureState, GameState, PlayerState, TargetState, WindowState
from src.domain.minimap import MarkerDetection, MinimapBounds, MinimapState


class TestCavebotController(unittest.TestCase):
    def setUp(self) -> None:
        now = datetime.now(timezone.utc)
        self.state = GameState(
            timestamp=now,
            capture=CaptureState(FrameStatus.VALID, now, 0.1),
            window=WindowState(True, False, True),
            player=PlayerState(0.9, 0.9, False),
            target=TargetState(False, False),
            minimap=MinimapState(
                True,
                MinimapBounds(1750, 3, 112, 112),
                (56, 56),
                (MarkerDetection("flag0", (16, 55), 0.76),),
            ),
        )
        self.controller = CavebotController(
            CavebotConfig(enabled=True, marker="flag0"),
            MinimapConfig(enabled=True, marker_templates=(("flag0", "ignored-in-unit-test"),), match_threshold=0.75),
        )

    def test_requests_movement_for_distant_marker(self) -> None:
        intent = self.controller.evaluate(self.state)
        self.assertTrue(intent.movement_requested)
        self.assertEqual(intent.status.value, "navigating")
        self.assertIsNotNone(intent.action)
        # Apenas o engine, após autorizar a simulação, inicia o intervalo.
        self.assertIsNotNone(self.controller.evaluate(self.state).action)
        self.controller.record_simulated_request()
        self.assertIsNone(self.controller.evaluate(self.state).action)

    def test_lack_of_progress_enters_stuck_without_action(self) -> None:
        controller = CavebotController(
            CavebotConfig(enabled=True, marker="flag0", stuck_timeout_ms=1, max_retries=0),
            MinimapConfig(enabled=True, marker_templates=(("flag0", "ignored-in-unit-test"),), match_threshold=0.75),
        )
        with patch("src.bot.cavebot.cavebot_controller.time.monotonic", side_effect=(0.0, 0.002)):
            self.assertIsNotNone(controller.evaluate(self.state).action)
            stuck = controller.evaluate(self.state)

        self.assertEqual(stuck.status.value, "stuck")
        self.assertFalse(stuck.movement_requested)
        self.assertIsNone(stuck.action)

    def test_suspension_preserves_waypoint_and_reacquires_marker(self) -> None:
        initial = self.controller.evaluate(self.state)
        suspended = self.controller.suspend(BotMode.COMBAT)
        resumed = self.controller.evaluate(self.state)

        self.assertIsNotNone(initial.action)
        self.assertEqual(suspended.status.value, "suspended")
        self.assertFalse(suspended.movement_requested)
        self.assertIsNone(suspended.action)
        self.assertIsNotNone(resumed.action)

    def test_arrival_does_not_request_action(self) -> None:
        arrived_state = GameState(
            timestamp=self.state.timestamp,
            capture=self.state.capture,
            window=self.state.window,
            player=self.state.player,
            target=self.state.target,
            minimap=MinimapState(
                True,
                self.state.minimap.bounds,
                self.state.minimap.center,
                (MarkerDetection("flag0", (56, 59), 0.76),),
            ),
        )
        intent = self.controller.evaluate(arrived_state)
        self.assertEqual(intent.status.value, "arrived")
        self.assertFalse(intent.movement_requested)
        self.assertIsNone(intent.action)


if __name__ == "__main__":
    unittest.main()
