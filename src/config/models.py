from dataclasses import dataclass, field
from typing import Optional

from src.domain.roi import RelativeROI


@dataclass(frozen=True)
class WindowConfig:
    tibia_title: str = "Tibia"
    obs_title: str = "obs"
    allow_partial_match: bool = True


@dataclass(frozen=True)
class RegionsConfig:
    hp: RelativeROI = field(default_factory=lambda: RelativeROI(x=0.187, y=0.000, width=0.281, height=0.018))
    mana: RelativeROI = field(default_factory=lambda: RelativeROI(x=0.533, y=0.001, width=0.280, height=0.018))
    status_bar: RelativeROI = field(default_factory=lambda: RelativeROI(x=0.477, y=0.001, width=0.057, height=0.017))
    battle_list: RelativeROI = field(default_factory=lambda: RelativeROI(x=0.908, y=0.361, width=0.058, height=0.091))


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
class LootConfig:
    enabled: bool = True
    nearby_corpses_key: str = "x"
    delay_ms: int = 200
    cooldown_ms: int = 500
    require_empty_battle_list: bool = False
    priority: int = 3
    emergency_hp_threshold: float = 30.0


@dataclass(frozen=True)
class ChatConfig:
    enabled: bool = True
    button_roi: RelativeROI = field(default_factory=lambda: RelativeROI(x=0.775521, y=0.971259, width=0.043229, height=0.026759))
    on_template_path: str = "templates/chat_on.png"
    match_threshold: float = 0.90
    max_attempts: int = 3
    retry_delay_ms: int = 300


@dataclass(frozen=True)
class AppConfig:
    window: WindowConfig = field(default_factory=WindowConfig)
    regions: RegionsConfig = field(default_factory=RegionsConfig)
    healer: HealerConfig = field(default_factory=HealerConfig)
    combat: CombatConfig = field(default_factory=CombatConfig)
    pz: PZConfig = field(default_factory=PZConfig)
    loot: LootConfig = field(default_factory=LootConfig)
    chat: ChatConfig = field(default_factory=ChatConfig)
    loop_interval_ms: int = 50
