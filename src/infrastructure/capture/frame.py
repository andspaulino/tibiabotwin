from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any

try:
    import numpy as np
except ImportError:
    np = None

from src.domain.capture_status import FrameStatus


@dataclass(frozen=True)
class CapturedFrame:
    """Representa um snapshot imutável de frame capturado em um ciclo do bot."""
    image: Optional[Any]  # np.ndarray OpenCV BGR
    captured_at: datetime
    width: int
    height: int
    source: str = "obs_projector"
    status: FrameStatus = FrameStatus.VALID

    def age_seconds(self, now: Optional[datetime] = None) -> float:
        """Retorna a idade do frame em segundos desde a captura."""
        ref_time = now or datetime.now(timezone.utc)
        if self.captured_at.tzinfo is None:
            # Se for naive UTC
            ref_time = ref_time.replace(tzinfo=None)
        return (ref_time - self.captured_at).total_seconds()

    @property
    def is_valid(self) -> bool:
        """Verifica se o frame é válido e seguro para consumo por detectores."""
        if self.status != FrameStatus.VALID:
            return False
        if self.width <= 0 or self.height <= 0:
            return False
        if self.image is None:
            return False
        if hasattr(self.image, "size") and self.image.size == 0:
            return False
        return True
