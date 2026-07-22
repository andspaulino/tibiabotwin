from datetime import datetime, timezone
from typing import List, Union
import numpy as np

from src.infrastructure.capture.frame import CapturedFrame, FrameStatus
from src.infrastructure.capture.base import FrameCapturer


class RecordedFrameCapturer(FrameCapturer):
    """
    Capturador de frames gravados / sintéticos para testes offline.
    Permite reproduzir sequências de imagens em testes unitários e de integração.
    """

    def __init__(self, images: List[np.ndarray]):
        self.images = images
        self.index = 0
        self.closed = False

    def capture(self, hwnd: int = 0) -> CapturedFrame:
        now = datetime.now(timezone.utc)

        if not self.images or self.closed:
            return CapturedFrame(
                image=np.empty((0, 0, 3), dtype=np.uint8),
                captured_at=now,
                width=0,
                height=0,
                source="recorded_fixture",
                status=FrameStatus.FAILED
            )

        current_img = self.images[self.index % len(self.images)]
        self.index += 1

        h, w = current_img.shape[:2]
        return CapturedFrame(
            image=current_img.copy(),
            captured_at=now,
            width=w,
            height=h,
            source="recorded_fixture",
            status=FrameStatus.VALID
        )

    def close(self) -> None:
        self.closed = True
