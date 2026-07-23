import unittest

from src.bot.cavebot.models import RelativeRegion, RouteSettings, Waypoint, WaypointType
from src.bot.cavebot.movement_controller import MovementController
from src.domain.actions import MouseClickPayload
from src.domain.minimap import MarkerDetection, MinimapBounds, MinimapState


class TestMovementController(unittest.TestCase):
    def setUp(self) -> None:
        self.minimap = MinimapState(True, MinimapBounds(1750, 3, 112, 112), (56, 56))
        self.waypoint = Waypoint("wp_01", WaypointType.MARKER_CLICK, "flag0", RelativeRegion(0, 0, 1, 1))
        self.settings = RouteSettings(0.75, 4.0, 1.5, 15_000, 1_500, 2)

    def test_proposes_absolute_click_for_marker_outside_arrival_radius(self) -> None:
        marker = MarkerDetection("flag0", (16, 55), 0.76)
        intent = MovementController().evaluate(self.minimap, self.waypoint, marker, self.settings)

        self.assertTrue(intent.movement_requested)
        self.assertEqual(intent.status.value, "navigating")
        self.assertIsNotNone(intent.action)
        assert intent.action is not None
        self.assertEqual(intent.action.payload, MouseClickPayload(1766, 58))

    def test_confirms_arrival_without_action(self) -> None:
        marker = MarkerDetection("flag0", (56, 59), 0.76)
        intent = MovementController().evaluate(self.minimap, self.waypoint, marker, self.settings)

        self.assertEqual(intent.status.value, "arrived")
        self.assertFalse(intent.movement_requested)
        self.assertIsNone(intent.action)

    def test_missing_marker_never_generates_action(self) -> None:
        intent = MovementController().evaluate(self.minimap, self.waypoint, None, self.settings)
        self.assertEqual(intent.status.value, "searching_marker")
        self.assertIsNone(intent.action)


if __name__ == "__main__":
    unittest.main()
