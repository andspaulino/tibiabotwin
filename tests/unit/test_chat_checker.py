import unittest
import numpy as np
from datetime import datetime, timezone

from src.config.models import ChatConfig
from src.domain.roi import RelativeROI
from src.infrastructure.capture.base import FrameCapturer
from src.infrastructure.capture.frame import CapturedFrame, FrameStatus
from src.infrastructure.input.mock_input import MockInputController
from src.infrastructure.vision.chat_checker import is_chat_off, get_chat_button_center
from src.application.chat_initializer import ChatInitializer


class DummyCapturer(FrameCapturer):
    def __init__(self, frame: CapturedFrame):
        self.frame = frame

    def capture(self, handle: int) -> CapturedFrame:
        return self.frame

    def close(self) -> None:
        pass


class TestChatChecker(unittest.TestCase):

    def setUp(self):
        self.config = ChatConfig(
            enabled=True,
            button_roi=RelativeROI(x=0.4, y=0.9, width=0.1, height=0.05),
            off_template_path="templates/test_chat_off_dummy.png",
            match_threshold=0.8,
            max_attempts=2,
            retry_delay_ms=10
        )
        self.now = datetime.now(timezone.utc)
        self.blank_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.valid_frame = CapturedFrame(
            image=self.blank_image,
            captured_at=self.now,
            width=100,
            height=100,
            status=FrameStatus.VALID,
            source="test"
        )

    def test_get_chat_button_center(self):
        """Verifica o cálculo de ponto central em pixels a partir de ROI relativa."""
        roi = RelativeROI(x=0.2, y=0.4, width=0.1, height=0.1)
        x, y = get_chat_button_center(100, 100, roi)
        self.assertEqual(x, 25)
        self.assertEqual(y, 45)

    def test_ensure_chat_off_disabled(self):
        """Verifica que retorna True imediatamente quando a checagem de chat está desativada."""
        cfg = ChatConfig(enabled=False)
        initializer = ChatInitializer(cfg)
        capturer = DummyCapturer(self.valid_frame)
        self.assertTrue(initializer.ensure_chat_off(capturer, hwnd_obs=123))

    def test_ensure_chat_off_invalid_hwnd(self):
        """Verifica que retorna False se o HWND for inválido."""
        initializer = ChatInitializer(self.config)
        capturer = DummyCapturer(self.valid_frame)
        self.assertFalse(initializer.ensure_chat_off(capturer, hwnd_obs=0))

    def test_ensure_chat_off_success(self):
        """Verifica se o initializer confirma Chat OFF (usando o fallback gracioso quando o arquivo png não existe)."""
        initializer = ChatInitializer(self.config)
        capturer = DummyCapturer(self.valid_frame)
        mock_input = MockInputController()
        
        result = initializer.ensure_chat_off(capturer, hwnd_obs=100, input_controller=mock_input)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
