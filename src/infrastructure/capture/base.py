from typing import Protocol, runtime_checkable

from src.infrastructure.capture.frame import CapturedFrame


@runtime_checkable
class FrameCapturer(Protocol):
    """Interface de capturador de frames para abstração de fontes visuais."""

    def capture(self, hwnd: int) -> CapturedFrame:
        """Captura e retorna um CapturedFrame a partir do handle da janela."""
        ...

    def close(self) -> None:
        """Libera recursos do capturador."""
        ...
