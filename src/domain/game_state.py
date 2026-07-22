from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.infrastructure.capture.frame import FrameStatus


@dataclass(frozen=True)
class PlayerState:
    """Snapshot do estado do jogador no ciclo atual."""
    hp_percent: Optional[float]
    mana_percent: Optional[float]
    in_protection_zone: Optional[bool]


@dataclass(frozen=True)
class TargetState:
    """Snapshot do estado do alvo no ciclo atual."""
    has_monsters_in_battle: Optional[bool]
    has_active_target: Optional[bool]


@dataclass(frozen=True)
class WindowState:
    """Snapshot do estado das janelas do sistema."""
    tibia_focused: bool
    tibia_minimized: bool
    projector_available: bool

    @property
    def is_safe(self) -> bool:
        return self.tibia_focused and not self.tibia_minimized and self.projector_available


@dataclass(frozen=True)
class CaptureState:
    """Snapshot da integridade da captura no ciclo atual."""
    status: FrameStatus
    captured_at: datetime
    age_seconds: float


@dataclass(frozen=True)
class GameState:
    """Snapshot imutável e consolidado do estado do jogo para o ciclo de iteração atual."""
    timestamp: datetime
    capture: CaptureState
    window: WindowState
    player: PlayerState
    target: TargetState

    @property
    def is_safe_to_act(self) -> bool:
        """Retorna True apenas se todas as verificações de segurança forem atendidas simultaneamente."""
        if not self.window.is_safe:
            return False
        if not self.capture.status == FrameStatus.VALID:
            return False
        if self.capture.age_seconds > 1.0:
            return False
        return True
