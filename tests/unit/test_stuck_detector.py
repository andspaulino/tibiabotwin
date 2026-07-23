import unittest

from src.bot.cavebot.models import MovementState, RouteSettings
from src.bot.cavebot.stuck_detector import StuckDetector


class TestStuckDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = RouteSettings(0.75, 4.0, 1.5, 1_000, 1_500, 2)
        self.detector = StuckDetector()
        self.initial = MovementState("wp_01", None, None, 0.0)

    def test_progress_requires_epsilon_and_resets_timeout(self) -> None:
        first = self.detector.update(self.initial, 40.0, self.settings, now=10.0)
        noise = self.detector.update(first.state, 39.2, self.settings, now=10.5)
        progress = self.detector.update(noise.state, 38.4, self.settings, now=10.7)

        self.assertEqual(noise.status.value, "navigating")
        self.assertEqual(progress.status.value, "navigating")
        self.assertEqual(progress.state.best_distance, 38.4)
        self.assertEqual(progress.state.last_progress_at, 10.7)

    def test_timeout_requests_limited_retries_then_stuck(self) -> None:
        state = self.detector.update(self.initial, 40.0, self.settings, now=0.0).state
        first_retry = self.detector.update(state, 40.0, self.settings, now=1.1)
        second_retry = self.detector.update(first_retry.state, 40.0, self.settings, now=2.2)
        stuck = self.detector.update(second_retry.state, 40.0, self.settings, now=3.3)

        self.assertEqual(first_retry.status.value, "waiting_retry")
        self.assertEqual(second_retry.status.value, "waiting_retry")
        self.assertEqual(stuck.status.value, "stuck")
        self.assertEqual(stuck.state.waypoint_id, "wp_01")
        self.assertEqual(stuck.state.retry_count, 2)


if __name__ == "__main__":
    unittest.main()
