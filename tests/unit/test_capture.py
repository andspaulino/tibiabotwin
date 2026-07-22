import unittest
from datetime import datetime, timezone, timedelta
import numpy as np

from src.infrastructure.capture.frame import CapturedFrame, FrameStatus
from src.infrastructure.capture.projector import ProjectorFrameCapturer


class TestFrameCapture(unittest.TestCase):

    def test_captured_frame_validity(self):
        """Verifica se um CapturedFrame válido retorna is_valid == True."""
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        now = datetime.now(timezone.utc)
        frame = CapturedFrame(
            image=dummy_img,
            captured_at=now,
            width=100,
            height=100,
            source="test",
            status=FrameStatus.VALID
        )

        self.assertTrue(frame.is_valid)
        self.assertEqual(frame.status, FrameStatus.VALID)

    def test_captured_frame_invalid_status(self):
        """Verifica se frames com status FAILED, STALE ou FROZEN retornam is_valid == False."""
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        now = datetime.now(timezone.utc)

        for status in [FrameStatus.FAILED, FrameStatus.STALE, FrameStatus.FROZEN]:
            frame = CapturedFrame(
                image=dummy_img,
                captured_at=now,
                width=100,
                height=100,
                source="test",
                status=status
            )
            self.assertFalse(frame.is_valid, f"Frame com status {status} deveria ser is_valid=False")

    def test_captured_frame_empty_image(self):
        """Verifica se imagem vazia ou dimensões zeradas tornam o frame inválido."""
        now = datetime.now(timezone.utc)
        empty_img = np.empty((0, 0, 3), dtype=np.uint8)

        frame1 = CapturedFrame(
            image=empty_img,
            captured_at=now,
            width=0,
            height=0,
            status=FrameStatus.VALID
        )
        self.assertFalse(frame1.is_valid)

        frame2 = CapturedFrame(
            image=None,
            captured_at=now,
            width=100,
            height=100,
            status=FrameStatus.VALID
        )
        self.assertFalse(frame2.is_valid)

    def test_captured_frame_age(self):
        """Verifica o cálculo de idade do frame."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(seconds=2.5)
        dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)

        frame = CapturedFrame(
            image=dummy_img,
            captured_at=past,
            width=10,
            height=10
        )
        self.assertAlmostEqual(frame.age_seconds(now), 2.5, delta=0.1)

    def test_projector_capturer_failure_handling(self):
        """Verifica tratamento de falha quando HWND é inválido (0 ou -1)."""
        capturer = ProjectorFrameCapturer()
        try:
            frame = capturer.capture(0)
            self.assertFalse(frame.is_valid)
            self.assertEqual(frame.status, FrameStatus.FAILED)
            self.assertGreater(capturer.consecutive_failures, 0)
        finally:
            capturer.close()


if __name__ == "__main__":
    unittest.main()
