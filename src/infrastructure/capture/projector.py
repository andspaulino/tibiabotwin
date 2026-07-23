from datetime import datetime, timezone
from typing import Optional, Any
import numpy as np
import time

from src.infrastructure.capture.frame import CapturedFrame, FrameStatus
from src.infrastructure.capture.base import FrameCapturer
from src.utils.logger import logger


class ProjectorFrameCapturer(FrameCapturer):
    """
    Capturador de alta velocidade para a janela do Projetor OBS Studio.
    Realiza exatamente uma captura única por ciclo e detecta frames congelados ou com falha.
    """

    def __init__(
        self,
        frozen_threshold_diff: float = 0.05,
        frozen_timeout_seconds: float = 5.0
    ):
        from src.utils.screen import ScreenCapturer
        self.screen_capturer = ScreenCapturer()
        self.frozen_threshold_diff = frozen_threshold_diff
        self.frozen_timeout_seconds = frozen_timeout_seconds

        self.previous_image: Optional[np.ndarray] = None
        self.last_visual_change_at: Optional[float] = None
        self.consecutive_failures: int = 0

    def capture(self, hwnd: int) -> CapturedFrame:
        now = datetime.now(timezone.utc)

        if not hwnd or hwnd <= 0:
            self.consecutive_failures += 1
            return CapturedFrame(
                image=np.empty((0, 0, 3), dtype=np.uint8),
                captured_at=now,
                width=0,
                height=0,
                source="obs_projector",
                status=FrameStatus.FAILED
            )

        try:
            from src.utils.screen import pil_to_cv2
            pil_img = self.screen_capturer.capture_window_client_area(hwnd)
            img_bgr = pil_to_cv2(pil_img)
        except Exception as err:
            self.consecutive_failures += 1
            if self.consecutive_failures == 1 or self.consecutive_failures % 50 == 0:
                logger.log("SYSTEM", f"Falha na captura da janela do Projetor OBS ({self.consecutive_failures}x): {err}", level="WARNING")
            
            return CapturedFrame(
                image=np.empty((0, 0, 3), dtype=np.uint8),
                captured_at=now,
                width=0,
                height=0,
                source="obs_projector",
                status=FrameStatus.FAILED
            )

        if img_bgr is None or img_bgr.size == 0:
            self.consecutive_failures += 1
            return CapturedFrame(
                image=np.empty((0, 0, 3), dtype=np.uint8),
                captured_at=now,
                width=0,
                height=0,
                source="obs_projector",
                status=FrameStatus.FAILED
            )

        h, w = img_bgr.shape[:2]
        self.consecutive_failures = 0

        # Detecção de Frame Congelado (Frozen)
        status = FrameStatus.VALID
        current_time = time.time()
        if self.previous_image is not None and self.previous_image.shape == img_bgr.shape:
            # Calcula diferença média absoluta de pixels
            diff = float(np.mean(np.abs(img_bgr.astype(float) - self.previous_image.astype(float))))
            if diff > self.frozen_threshold_diff:
                self.last_visual_change_at = current_time
            
            if self.last_visual_change_at is None:
                self.last_visual_change_at = current_time

            elapsed = current_time - self.last_visual_change_at
            if elapsed >= self.frozen_timeout_seconds:
                status = FrameStatus.FROZEN
                logger.log("SYSTEM", f"Captura estática/congelada detectada há {elapsed:.1f} segundos.", level="WARNING")
        else:
            self.last_visual_change_at = current_time

        self.previous_image = img_bgr.copy()

        return CapturedFrame(
            image=img_bgr,
            captured_at=now,
            width=w,
            height=h,
            source="obs_projector",
            status=status
        )

    def close(self) -> None:
        """Libera os recursos de captura de tela."""
        if self.screen_capturer:
            try:
                self.screen_capturer.close()
            except Exception:
                pass
