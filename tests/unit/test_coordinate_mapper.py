import unittest

from src.application.coordinate_mapper import CoordinateMappingError, FrameToWindowMapper, ScreenPoint
from src.infrastructure.window.base import WindowClientArea


class TestFrameToWindowMapper(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = FrameToWindowMapper(aspect_ratio_tolerance=0.02)

    def test_maps_frame_corners_to_client_area_corners(self) -> None:
        target = WindowClientArea(left=100, top=50, width=1920, height=1080)

        self.assertEqual(self.mapper.map_point(0, 0, 1920, 1080, target), ScreenPoint(100, 50))
        self.assertEqual(
            self.mapper.map_point(1919, 1079, 1920, 1080, target),
            ScreenPoint(2019, 1129),
        )

    def test_maps_between_compatible_scaled_dimensions(self) -> None:
        target = WindowClientArea(left=200, top=100, width=1280, height=720)

        point = self.mapper.map_point(960, 540, 1920, 1080, target)

        self.assertEqual(point, ScreenPoint(840, 460))

    def test_rejects_point_outside_frame(self) -> None:
        target = WindowClientArea(left=0, top=0, width=1920, height=1080)

        with self.assertRaisesRegex(CoordinateMappingError, "fora dos limites"):
            self.mapper.map_point(1920, 100, 1920, 1080, target)

    def test_rejects_incompatible_aspect_ratios(self) -> None:
        target = WindowClientArea(left=0, top=0, width=1280, height=1024)

        with self.assertRaisesRegex(CoordinateMappingError, "aspectos incompatíveis"):
            self.mapper.map_point(960, 540, 1920, 1080, target)

    def test_rejects_invalid_frame_dimensions(self) -> None:
        target = WindowClientArea(left=0, top=0, width=1920, height=1080)

        with self.assertRaisesRegex(CoordinateMappingError, "dimensões maiores"):
            self.mapper.map_point(0, 0, 1, 1080, target)


if __name__ == "__main__":
    unittest.main()
