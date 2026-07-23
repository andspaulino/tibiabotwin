import unittest

from src.bot.cavebot.marker_selector import MarkerSelector
from src.bot.cavebot.models import RelativeRegion, Waypoint, WaypointType
from src.domain.minimap import MarkerDetection, MinimapBounds, MinimapState


class TestMarkerSelector(unittest.TestCase):
    def setUp(self) -> None:
        self.minimap = MinimapState(
            available=True,
            bounds=MinimapBounds(x=1750, y=3, width=112, height=112),
            center=(56, 56),
            markers=(),
        )
        self.waypoint = Waypoint(
            id="flag-left",
            type=WaypointType.MARKER_CLICK,
            marker="flag0",
            expected_region=RelativeRegion(0.0, 0.0, 0.5, 1.0),
            description="Flag à esquerda",
        )

    def test_selects_matching_marker_in_expected_region(self) -> None:
        minimap = MinimapState(
            available=True,
            bounds=self.minimap.bounds,
            center=self.minimap.center,
            markers=(MarkerDetection("flag0", (16, 55), 0.76),),
        )

        selected = MarkerSelector().select(minimap, self.waypoint, default_threshold=0.75)
        self.assertEqual(selected, minimap.markers[0])

    def test_rejects_marker_below_threshold_or_outside_region(self) -> None:
        low_confidence = MarkerDetection("flag0", (16, 55), 0.74)
        right_side = MarkerDetection("flag0", (90, 55), 0.90)
        minimap = MinimapState(True, self.minimap.bounds, self.minimap.center, (low_confidence, right_side))

        self.assertIsNone(MarkerSelector().select(minimap, self.waypoint, default_threshold=0.75))

    def test_rejects_ambiguous_equal_confidence_candidates(self) -> None:
        first = MarkerDetection("flag0", (16, 55), 0.76)
        second = MarkerDetection("flag0", (20, 70), 0.76)
        minimap = MinimapState(True, self.minimap.bounds, self.minimap.center, (first, second))

        self.assertIsNone(MarkerSelector().select(minimap, self.waypoint, default_threshold=0.75))


if __name__ == "__main__":
    unittest.main()
