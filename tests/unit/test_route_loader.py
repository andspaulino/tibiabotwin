import json
import tempfile
import unittest
from pathlib import Path

from src.config.route_loader import RouteValidationError, load_route


class TestRouteLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.template = Path("templates/markers/flag0.png").resolve()
        self.markers = {"flag0": str(self.template)}
        self.data = {
            "hunt_name": "Test route",
            "version": 1,
            "loop": False,
            "settings": {
                "match_threshold": 0.75,
                "arrival_radius_pixels": 4.0,
                "progress_epsilon_pixels": 1.5,
                "stuck_timeout_ms": 15000,
                "click_cooldown_ms": 1500,
                "max_retries": 2,
            },
            "waypoints": [{
                "id": "wp-01",
                "type": "marker_click",
                "marker": "flag0",
                "expected_region": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
            }],
        }

    def test_loads_valid_route(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route.json"
            path.write_text(json.dumps(self.data), encoding="utf-8")
            route = load_route(path, self.markers)
        self.assertEqual(route.hunt_name, "Test route")
        self.assertEqual(route.waypoints[0].id, "wp-01")

    def test_rejects_unknown_marker_and_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route.json"
            invalid = dict(self.data)
            invalid["waypoints"] = [dict(self.data["waypoints"][0], marker="missing")]
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaises(RouteValidationError):
                load_route(path, self.markers)

            invalid["waypoints"] = [self.data["waypoints"][0], self.data["waypoints"][0]]
            path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaises(RouteValidationError):
                load_route(path, self.markers)


if __name__ == "__main__":
    unittest.main()
