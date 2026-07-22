from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class WindowConfig:
    tibia_title: str = "Tibia"
    obs_title: str = "obs"
    allow_partial_match: bool = True


@dataclass(frozen=True)
class SpellActionConfig:
    enabled: bool = True
    key: str = "1"
    hp_below: float = 90.0
    cooldown_ms: int = 1000


@dataclass(frozen=True)
class PotionActionConfig:
    enabled: bool = True
    key: str = "2"
    threshold_below: float = 50.0
    cooldown_ms: int = 1000


@dataclass(frozen=True)
class EmergencyPotionConfig:
    enabled: bool = True
    key: str = "3"
    hp_below: float = 30.0
    cooldown_ms: int = 1000


@dataclass(frozen=True)
class HealerConfig:
    enabled: bool = True
    spell: SpellActionConfig = field(default_factory=SpellActionConfig)
    mana_potion: PotionActionConfig = field(default_factory=PotionActionConfig)
    emergency_potion: EmergencyPotionConfig = field(default_factory=EmergencyPotionConfig)


@dataclass(frozen=True)
class CombatConfig:
    enabled: bool = True
    attack_key: str = "space"
    attack_cooldown_ms: int = 1000
    min_battle_pixels: int = 10
    target_template_path: str = "templates/target_red.png"
    target_match_threshold: float = 0.75


@dataclass(frozen=True)
class PZConfig:
    enabled: bool = True
    template_path: str = "templates/pz.png"
    match_threshold: float = 0.82


@dataclass(frozen=True)
class AppConfig:
    window: WindowConfig = field(default_factory=WindowConfig)
    healer: HealerConfig = field(default_factory=HealerConfig)
    combat: CombatConfig = field(default_factory=CombatConfig)
    pz: PZConfig = field(default_factory=PZConfig)
    loop_interval_ms: int = 50
