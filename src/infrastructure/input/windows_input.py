from src.infrastructure.input.base import InputController
from src.utils.input import press_key, click_at


class WindowsInputController(InputController):
    """Implementação DirectX / pydirectinput para Windows."""

    def press_key(self, key: str) -> None:
        press_key(key)

    def click(self, x: int, y: int, button: str = "left") -> None:
        click_at(x, y, button=button)

    def release_all(self) -> None:
        try:
            import pydirectinput
            pydirectinput.keyUp("shift")
            pydirectinput.keyUp("ctrl")
            pydirectinput.keyUp("alt")
        except Exception:
            pass
