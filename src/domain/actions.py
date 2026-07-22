from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ActionType(Enum):
    """Tipos de ações possíveis que o bot pode propor e executar."""
    EMERGENCY_HEAL = "emergency_heal"
    HEAL = "heal"
    USE_MANA = "use_mana"
    ATTACK = "attack"
    LOOT = "loot"
    MOVE = "move"


@dataclass(frozen=True)
class BotAction:
    """Representa a intenção imutável de uma ação proposta por um módulo."""
    action_type: ActionType
    priority: int
    key: Optional[str] = None
    reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
