import sys

from src.infrastructure.window.base import WindowManager
from src.infrastructure.window.windows_manager import WindowsWindowManager

from src.infrastructure.input.base import InputController
from src.infrastructure.input.windows_input import WindowsInputController
from src.infrastructure.input.mock_input import MockInputController


def create_window_manager() -> WindowManager:
    """Instancia a implementação apropriada de WindowManager segundo a plataforma."""
    if sys.platform == "win32":
        return WindowsWindowManager()
    # Em outras plataformas, retorna WindowsWindowManager com fallback gracioso
    return WindowsWindowManager()


def create_input_controller(mock: bool = False) -> InputController:
    """Instancia a implementação apropriada de InputController segundo a plataforma."""
    if mock:
        return MockInputController()
    if sys.platform == "win32":
        return WindowsInputController()
    return MockInputController()
