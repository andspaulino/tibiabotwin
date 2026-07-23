import unittest

from src.bot.cavebot.models import HuntRoute, RelativeRegion, RouteSettings, Waypoint, WaypointType
from src.bot.cavebot.route_runner import RouteRunner


class TestRouteRunner(unittest.TestCase):
    def setUp(self) -> None:
        settings = RouteSettings(0.75, 4.0, 1.5, 15_000, 1_500, 2)
        waypoints = (
            Waypoint("one", WaypointType.MARKER_CLICK, "flag0", RelativeRegion(0, 0, 1, 1)),
            Waypoint("two", WaypointType.MARKER_CLICK, "flag1", RelativeRegion(0, 0, 1, 1)),
        )
        self.settings = settings
        self.waypoints = waypoints

    def test_advances_only_after_arrival_and_completes_without_loop(self) -> None:
        runner = RouteRunner(HuntRoute("Test", 1, False, self.settings, self.waypoints))
        self.assertEqual(runner.current_waypoint.id, "one")
        runner.reset_movement()
        self.assertEqual(runner.current_waypoint.id, "one")
        self.assertEqual(runner.mark_arrived().id, "two")
        self.assertIsNone(runner.mark_arrived())
        self.assertTrue(runner.completed)

    def test_loops_to_first_waypoint(self) -> None:
        runner = RouteRunner(HuntRoute("Test", 1, True, self.settings, self.waypoints))
        runner.mark_arrived()
        self.assertEqual(runner.mark_arrived().id, "one")
        self.assertFalse(runner.completed)


if __name__ == "__main__":
    unittest.main()
