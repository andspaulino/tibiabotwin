from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class BotMode(Enum):
    """Modos principais de operação da máquina de estados do bot."""
    STOPPED = "stopped"
    PAUSED = "paused"
    UNSAFE = "unsafe"
    IDLE = "idle"
    IN_PROTECTION_ZONE = "in_protection_zone"
    COMBAT = "combat"
    LOOTING = "looting"
    MOVING = "moving"


@dataclass(frozen=True)
class StateTransition:
    """Representa um evento de transição de estado auditável."""
    from_mode: BotMode
    to_mode: BotMode
    reason: str
    timestamp: datetime


@dataclass(frozen=True)
class BotState:
    """Snapshot imutável do estado ativo da máquina de estados."""
    current_mode: BotMode = BotMode.STOPPED
    previous_mode: BotMode = BotMode.STOPPED
    reason: str = "Inicialização"
    entered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
