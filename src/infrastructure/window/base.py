from typing import Protocol, Optional, Tuple, List
from src.config.models import WindowConfig


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

    def set_opacity(self, hwnd: int, opacity: int) -> bool:
        ...

    def reset_opacity(self, hwnd: int) -> bool:
        ...
