import unittest
from unittest.mock import MagicMock, patch

from src.infrastructure.input.windows_input import WindowsInputController
from src.utils import input as input_utils


class TestMouseInput(unittest.TestCase):
    def test_click_restores_previous_cursor_position(self) -> None:
        fake_direct_input = MagicMock()
        fake_direct_input.position.return_value = (100, 200)

        with (
            patch.object(input_utils, "pydirectinput", fake_direct_input),
            patch.object(input_utils, "move_mouse_human") as move_mouse,
            patch.object(input_utils, "gaussian_delay", return_value=0.0),
            patch.object(input_utils.time, "sleep"),
        ):
            input_utils.click_at(500, 600)

        self.assertEqual(move_mouse.call_args_list[0].args, (500, 600))
        self.assertEqual(move_mouse.call_args_list[1].args, (100, 200))
        fake_direct_input.click.assert_called_once_with(button="left", _pause=False)

    def test_windows_controller_forwards_neutral_return_position(self) -> None:
        controller = WindowsInputController()

        with patch("src.infrastructure.input.windows_input.click_at") as click_at:
            controller.click(500, 600, return_position=(1738, 59))

        self.assertEqual(click_at.call_args.kwargs["return_position"], (1738, 59))

    def test_click_uses_explicit_return_position(self) -> None:
        fake_direct_input = MagicMock()
        fake_direct_input.position.return_value = (100, 200)

        with (
            patch.object(input_utils, "pydirectinput", fake_direct_input),
            patch.object(input_utils, "move_mouse_human") as move_mouse,
            patch.object(input_utils, "gaussian_delay", return_value=0.0),
            patch.object(input_utils.time, "sleep"),
        ):
            input_utils.click_at(500, 600, return_position=(1738, 59))

        self.assertEqual(move_mouse.call_args_list[1].args, (1738, 59))


if __name__ == "__main__":
    unittest.main()
