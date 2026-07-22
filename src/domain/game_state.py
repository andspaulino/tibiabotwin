from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.infrastructure.capture.frame import FrameStatus


@dataclass(frozen=True)
class PlayerState:
    """Representa o estado do jogador inferido puramente da visão computacional."""
    hp_percent: Optional[float] = None
    mana_percent: Optional[float] = None
    in_protection_zone: Optional[bool] = None


@dataclass(frozen=True)
class TargetState:
    """Representa o estado de combate e alvos do jogo."""
    has_monsters_in_battle: Optional[bool] = None
    has_active_target: Optional[bool] = None


@dataclass(frozen=True)
class WindowState:
    """Representa o estado do sistema operacional quanto às janelas envolvidas."""
    tibia_focused: bool = False
    tibia_minimized: bool = False
    projector_available: bool = False


@dataclass(frozen=True)
class CaptureState:
    """Representa a saúde e integridade da captura de imagem do ciclo."""
    status: FrameStatus = FrameStatus.FAILED
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    age_seconds: float = 0.0


@dataclass(frozen=True)
class GameState:
    """
    Snapshot imutável do estado central do jogo percebido em um ciclo.
    Consolida captura, janelas, jogador e alvos.
    """
    timestamp: datetime
    capture: CaptureState
    window: WindowState
    player: PlayerState
    target: TargetState

    @property
    def is_safe_to_act(self) -> bool:
        """
        Retorna True somente quando todas as condições operacionais são seguras para envio de inputs:
        - Janela do Tibia focada e não minimizada.
        - Janela do Projetor disponível.
        - Frame de captura VÁLIDO e recente (idade <= 1.0s).
        """
        if not self.window.tibia_focused or self.window.tibia_minimized or not self.window.projector_available:
            return False
        if self.capture.status != FrameStatus.VALID or self.capture.age_seconds > 1.0:
            return False
        return True
