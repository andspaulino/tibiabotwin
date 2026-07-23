from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import TypeAlias


class ActionType(Enum):
    """Tipos de intenções que podem ser resolvidas pelo executor central."""

    EMERGENCY_HEAL = "emergency_heal"
    HEAL = "heal"
    USE_MANA = "use_mana"
    ATTACK = "attack"
    LOOT = "loot"
    LOOT_NEARBY = "loot_nearby"
    MOVE = "move"


class ActionPriority(IntEnum):
    """Prioridades explícitas; valores maiores vencem na resolução central."""

    MOVEMENT = 40
    LOOT = 50
    ATTACK = 60
    MANA = 70
    HEAL = 80
    EMERGENCY = 100


@dataclass(frozen=True)
class KeyPayload:
    key: str

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("a tecla da ação não pode ser vazia")


@dataclass(frozen=True)
class MouseClickPayload:
    x: int
    y: int
    button: str = "left"
    return_x: int | None = None
    return_y: int | None = None

    def __post_init__(self) -> None:
        if self.button not in {"left", "right", "middle"}:
            raise ValueError("botão de mouse não suportado")
        if (self.return_x is None) != (self.return_y is None):
            raise ValueError("as duas coordenadas de retorno devem ser informadas juntas")

    @property
    def return_position(self) -> tuple[int, int] | None:
        if self.return_x is None or self.return_y is None:
            return None
        return self.return_x, self.return_y


ActionPayload: TypeAlias = KeyPayload | MouseClickPayload


@dataclass(frozen=True)
class BotAction:
    """Intenção imutável; somente o executor central pode realizar seu payload."""

    action_type: ActionType
    priority: ActionPriority
    payload: ActionPayload
    reason: str
    cooldown_ms: int = 0
    cooldown_key: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("toda ação deve possuir um motivo")
        if self.cooldown_ms < 0:
            raise ValueError("cooldown_ms não pode ser negativo")
        if self.cooldown_key is not None and not self.cooldown_key.strip():
            raise ValueError("cooldown_key não pode ser vazia")
