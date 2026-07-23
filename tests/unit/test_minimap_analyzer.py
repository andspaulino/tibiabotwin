import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from src.config.models import AppConfig, MinimapConfig, RegionsConfig
from src.domain.game_state import WindowState
from src.domain.roi import RelativeROI
from src.infrastructure.capture.frame import CapturedFrame, FrameStatus
from src.infrastructure.vision.game_analyzer import GameAnalyzer
from src.infrastructure.vision.minimap_analyzer import MinimapAnalyzer


class TestMinimapAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.template_path = Path(self.temp_dir.name) / "flag.png"
        self.template = np.array(
            [
                [[0, 0, 255], [20, 40, 220], [0, 255, 0]],
                [[255, 0, 0], [255, 255, 255], [0, 0, 0]],
                [[80, 30, 10], [10, 180, 80], [90, 90, 180]],
            ],
            dtype=np.uint8,
        )
        self.assertTrue(cv2.imwrite(str(self.template_path), self.template))
        self.analyzer = MinimapAnalyzer(nms_distance_pixels=3.0)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_returns_local_marker_coordinates_and_absolute_bounds(self) -> None:
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        # Relative ROI: x=20, y=20, width=100, height=60.
        frame[30:33, 60:63] = self.template
        frame[55:58, 90:93] = self.template

        state = self.analyzer.analyze(
            frame,
            RelativeROI(x=0.1, y=0.2, width=0.5, height=0.6),
            {"flag0": str(self.template_path)},
            match_threshold=0.99,
        )

        self.assertTrue(state.available)
        self.assertIsNotNone(state.bounds)
        bounds = state.bounds
        assert bounds is not None
        self.assertEqual((bounds.x, bounds.y, bounds.width, bounds.height), (20, 20, 100, 60))
        self.assertEqual(state.center, (50, 30))
        self.assertEqual({marker.center for marker in state.markers}, {(41, 11), (71, 36)})
        self.assertTrue(all(marker.template_id == "flag0" for marker in state.markers))
        self.assertTrue(all(marker.confidence >= 0.99 for marker in state.markers))

    def test_returns_available_state_when_no_marker_is_visible(self) -> None:
        state = self.analyzer.analyze(
            np.zeros((20, 20, 3), dtype=np.uint8),
            RelativeROI(x=0.0, y=0.0, width=1.0, height=1.0),
            {"flag0": str(self.template_path)},
            match_threshold=0.99,
        )

        self.assertTrue(state.available)
        self.assertEqual(state.markers, ())

    def test_invalid_frame_and_cross_validation_fail_safe(self) -> None:
        invalid_frame = self.analyzer.analyze(
            np.empty((0, 0, 3), dtype=np.uint8),
            RelativeROI(x=0.0, y=0.0, width=1.0, height=1.0),
            {},
            match_threshold=0.8,
        )
        self.assertFalse(invalid_frame.available)
        self.assertIsNotNone(invalid_frame.reason)
        self.assertIn("frame", invalid_frame.reason or "")

        invalid_cross = self.analyzer.analyze(
            np.zeros((20, 20, 3), dtype=np.uint8),
            RelativeROI(x=0.0, y=0.0, width=1.0, height=1.0),
            {},
            match_threshold=0.8,
            validate_cross=True,
            cross_template_path=str(Path(self.temp_dir.name) / "missing-cross.png"),
        )
        self.assertFalse(invalid_cross.available)
        self.assertIsNotNone(invalid_cross.reason)
        self.assertIn("cross", invalid_cross.reason or "")

    def test_game_analyzer_filters_templates_to_active_route(self) -> None:
        frame_image = np.zeros((40, 40, 3), dtype=np.uint8)
        frame_image[10:13, 15:18] = self.template
        config = AppConfig(
            regions=RegionsConfig(minimap=RelativeROI(x=0.0, y=0.0, width=1.0, height=1.0)),
            minimap=MinimapConfig(
                enabled=True,
                marker_templates=(("flag0", str(self.template_path)), ("flag1", str(self.template_path))),
                match_threshold=0.99,
            ),
        )
        frame = CapturedFrame(frame_image, datetime.now(timezone.utc), 40, 40, status=FrameStatus.VALID)

        state = GameAnalyzer(config, marker_template_ids={"flag1"}).analyze(
            frame,
            WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
        )

        self.assertEqual([marker.template_id for marker in state.minimap.markers], ["flag1"])

    def test_game_analyzer_includes_minimap_from_shared_frame(self) -> None:
        frame_image = np.zeros((40, 40, 3), dtype=np.uint8)
        frame_image[10:13, 15:18] = self.template
        config = AppConfig(
            regions=RegionsConfig(minimap=RelativeROI(x=0.0, y=0.0, width=1.0, height=1.0)),
            minimap=MinimapConfig(
                enabled=True,
                marker_templates=(("flag0", str(self.template_path)),),
                match_threshold=0.99,
            ),
        )
        frame = CapturedFrame(
            image=frame_image,
            captured_at=datetime.now(timezone.utc),
            width=40,
            height=40,
            source="test",
            status=FrameStatus.VALID,
        )

        state = GameAnalyzer(config).analyze(
            frame,
            WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
        )

        self.assertTrue(state.minimap.available)
        self.assertEqual(len(state.minimap.markers), 1)
        self.assertEqual(state.minimap.markers[0].center, (16, 11))


if __name__ == "__main__":
    unittest.main()
