from dataclasses import dataclass
from typing import Protocol, Optional, Tuple

from src.config.models import WindowConfig


@dataclass(frozen=True)
class WindowClientArea:
    """Área cliente de uma janela em coordenadas absolutas da tela."""

    left: int
    top: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("a área cliente deve possuir dimensões positivas")


class WindowManager(Protocol):
    """Interface abstrata para descoberta e manipulação de janelas no SO."""

    def find_tibia(self, window_cfg: WindowConfig) -> Optional[Tuple[int, str]]:
        ...

    def find_projector(self, window_cfg: WindowConfig) -> Optional[Tuple[int, str]]:
        ...

    def is_focused(self, hwnd: int) -> bool:
        ...

    def is_minimized(self, hwnd: int) -> bool:
        ...

    def get_client_area(self, hwnd: int) -> Optional[WindowClientArea]:
        """Retorna a área cliente em coordenadas absolutas da tela."""
        ...

    def set_opacity(self, hwnd: int, opacity: int) -> bool:
        ...

    def reset_opacity(self, hwnd: int) -> bool:
        ...
