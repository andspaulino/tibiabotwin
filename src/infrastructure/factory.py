import sys

from src.infrastructure.window.base import WindowManager
from src.infrastructure.window.windows_manager import WindowsWindowManager

from src.infrastructure.input.base import InputController
from src.infrastructure.input.windows_input import WindowsInputController
from src.infrastructure.input.mock_input import MockInputController
from src.utils.logger import logger


class UnsupportedPlatformError(NotImplementedError):
    """Exceção lançada quando o sistema operacional atual não possui implementação suportada."""
    pass


def create_window_manager() -> WindowManager:
    """Instancia a implementação apropriada de WindowManager segundo a plataforma."""
    if sys.platform == "win32":
        return WindowsWindowManager()
    raise UnsupportedPlatformError(f"Gerenciamento de janelas nativo não suportado no sistema operacional: '{sys.platform}'.")


def create_input_controller(mock: bool = False) -> InputController:
    """Instancia a implementação apropriada de InputController segundo a plataforma."""
    if mock:
        return MockInputController()
    if sys.platform == "win32":
        return WindowsInputController()
    
    logger.log("SYSTEM", f"[AVISO] Input de hardware não suportado na plataforma '{sys.platform}'. Utilizando MockInputController.", level="WARNING")
    return MockInputController()
