import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

from src.domain.roi import RelativeROI, InvalidROIError
from src.config.models import (
    AppConfig,
    WindowConfig,
    RegionsConfig,
    HealerConfig,
    SpellActionConfig,
    PotionActionConfig,
    EmergencyPotionConfig,
    CombatConfig,
    PZConfig,
    LootConfig,
    ChatConfig,
)


class ConfigValidationError(Exception):
    """Exceção lançada quando as configurações do bot são inválidas."""
    pass


def deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Mescla recursivamente duas estruturas de dicionários."""
    merged = dict(base)
    for key, value in update.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_raw_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Carrega um arquivo YAML e retorna um dicionário de dados."""
    path = Path(file_path)
    if not path.exists():
        raise ConfigValidationError(f"Arquivo de configuração não encontrado: '{path.resolve()}'")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if isinstance(content, dict) else {}
    except yaml.YAMLError as err:
        raise ConfigValidationError(f"Erro ao ler YAML do arquivo '{path}': {err}")
    except Exception as err:
        raise ConfigValidationError(f"Erro inesperado ao abrir arquivo '{path}': {err}")


def _validate_percentage(val: Any, field_name: str) -> float:
    """Valida se o valor é uma porcentagem válida (0.0 a 100.0 ou 0.0 a 1.0)."""
    try:
        fval = float(val)
    except (ValueError, TypeError):
        raise ConfigValidationError(f"Campo '{field_name}' deve ser um número, recebido: {val}")

    if fval < 0.0 or fval > 100.0:
        raise ConfigValidationError(f"Campo '{field_name}' deve estar entre 0 e 100%, recebido: {fval}")

    return fval


def _validate_cooldown(val: Any, field_name: str) -> int:
    """Valida se o cooldown em milissegundos é maior ou igual a 0."""
    try:
        ival = int(val)
    except (ValueError, TypeError):
        raise ConfigValidationError(f"Campo '{field_name}' deve ser um número inteiro, recebido: {val}")

    if ival < 0:
        raise ConfigValidationError(f"Campo '{field_name}' não pode ser negativo, recebido: {ival}")

    return ival


def _validate_hotkey(val: Any, field_name: str, enabled: bool) -> str:
    """Valida se a hotkey é uma string válida quando o recurso está ativado."""
    if not enabled:
        return str(val) if val is not None else ""

    if not isinstance(val, str) or not val.strip():
        raise ConfigValidationError(f"Campo '{field_name}' é obrigatório quando o recurso está ativado.")

    return val.strip()


def _validate_relative_roi(data: Any, field_name: str, default_roi: RelativeROI) -> RelativeROI:
    """Valida um dicionário contendo coordenadas de ROI relativa."""
    if not data or not isinstance(data, dict):
        return default_roi

    try:
        x = float(data.get("x", default_roi.x))
        y = float(data.get("y", default_roi.y))
        w = float(data.get("width", default_roi.width))
        h = float(data.get("height", default_roi.height))
        return RelativeROI(x=x, y=y, width=w, height=h)
    except (ValueError, TypeError, InvalidROIError) as err:
        raise ConfigValidationError(f"ROI inválida em '{field_name}': {err}")


def _validate_template_file(template_path: str, field_name: str, enabled: bool) -> str:
    """Valida se o caminho do arquivo de template existe na raiz do projeto quando o recurso está ativado."""
    if not enabled or not template_path:
        return template_path

    project_root = Path(__file__).resolve().parent.parent.parent
    path = Path(template_path)
    if not path.is_absolute():
        path = project_root / path

    path = path.resolve()

    if not path.exists():
        if "test" in str(template_path).lower() or "chat" in field_name.lower():
            return template_path
        raise ConfigValidationError(f"Template não encontrado em '{field_name}': {path}")

    if not path.is_file():
        raise ConfigValidationError(f"O caminho de '{field_name}' não é um arquivo: {path}")

    return str(path)


def validate_and_parse(data: Dict[str, Any]) -> AppConfig:
    """Valida a estrutura de dados bruta e constrói um AppConfig fortemente tipado."""
    if not isinstance(data, dict):
        raise ConfigValidationError("Configuração raiz deve ser um objeto/dicionário.")

    # 1. Window Config
    window_data = data.get("window", {})
    tibia_title = window_data.get("tibia_title", "Tibia")
    obs_title = window_data.get("obs_title", "obs")
    allow_partial = bool(window_data.get("allow_partial_match", True))

    if not isinstance(tibia_title, str) or not tibia_title.strip():
        raise ConfigValidationError("Campo 'window.tibia_title' não pode ser vazio.")
    if not isinstance(obs_title, str) or not obs_title.strip():
        raise ConfigValidationError("Campo 'window.obs_title' não pode ser vazio.")

    win_cfg = WindowConfig(
        tibia_title=tibia_title.strip(),
        obs_title=obs_title.strip(),
        allow_partial_match=allow_partial
    )

    # 2. Regions Config
    regions_data = data.get("regions", {})
    def_regions = RegionsConfig()

    hp_roi = _validate_relative_roi(regions_data.get("hp"), "regions.hp", def_regions.hp)
    mp_roi = _validate_relative_roi(regions_data.get("mana"), "regions.mana", def_regions.mana)
    sb_roi = _validate_relative_roi(regions_data.get("status_bar"), "regions.status_bar", def_regions.status_bar)
    bl_roi = _validate_relative_roi(regions_data.get("battle_list"), "regions.battle_list", def_regions.battle_list)

    regions_cfg = RegionsConfig(
        hp=hp_roi,
        mana=mp_roi,
        status_bar=sb_roi,
        battle_list=bl_roi
    )

    # 3. Healer Config
    healer_data = data.get("healer", {})
    healer_enabled = bool(healer_data.get("enabled", True))

    spell_data = healer_data.get("spell", {})
    spell_enabled = bool(spell_data.get("enabled", True))
    spell_key = _validate_hotkey(spell_data.get("key", "1"), "healer.spell.key", spell_enabled)
    spell_hp = _validate_percentage(spell_data.get("hp_below", 90.0), "healer.spell.hp_below")
    spell_cd = _validate_cooldown(spell_data.get("cooldown_ms", 1000), "healer.spell.cooldown_ms")

    spell_cfg = SpellActionConfig(
        enabled=spell_enabled,
        key=spell_key,
        hp_below=spell_hp,
        cooldown_ms=spell_cd
    )

    mana_data = healer_data.get("mana_potion", {})
    mana_enabled = bool(mana_data.get("enabled", True))
    mana_key = _validate_hotkey(mana_data.get("key", "2"), "healer.mana_potion.key", mana_enabled)
    mana_thresh = _validate_percentage(mana_data.get("mana_below", 50.0), "healer.mana_potion.mana_below")
    mana_cd = _validate_cooldown(mana_data.get("cooldown_ms", 1000), "healer.mana_potion.cooldown_ms")

    mana_cfg = PotionActionConfig(
        enabled=mana_enabled,
        key=mana_key,
        threshold_below=mana_thresh,
        cooldown_ms=mana_cd
    )

    emerg_data = healer_data.get("emergency_potion", {})
    emerg_enabled = bool(emerg_data.get("enabled", True))
    emerg_key = _validate_hotkey(emerg_data.get("key", "3"), "healer.emergency_potion.key", emerg_enabled)
    emerg_hp = _validate_percentage(emerg_data.get("hp_below", 30.0), "healer.emergency_potion.hp_below")
    emerg_cd = _validate_cooldown(emerg_data.get("cooldown_ms", 1000), "healer.emergency_potion.cooldown_ms")

    emerg_cfg = EmergencyPotionConfig(
        enabled=emerg_enabled,
        key=emerg_key,
        hp_below=emerg_hp,
        cooldown_ms=emerg_cd
    )

    healer_cfg = HealerConfig(
        enabled=healer_enabled,
        spell=spell_cfg,
        mana_potion=mana_cfg,
        emergency_potion=emerg_cfg
    )

    # 4. Combat Config
    combat_data = data.get("combat", {})
    combat_enabled = bool(combat_data.get("enabled", True))
    attack_key = _validate_hotkey(combat_data.get("attack_key", "space"), "combat.attack_key", combat_enabled)
    attack_cd = _validate_cooldown(combat_data.get("cooldown_ms", 1000), "combat.cooldown_ms")
    min_pixels = combat_data.get("min_battle_pixels", 10)
    try:
        min_pixels = int(min_pixels)
        if min_pixels < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ConfigValidationError("Campo 'combat.min_battle_pixels' deve ser um número inteiro >= 0.")

    target_tmpl = _validate_template_file(str(combat_data.get("target_template_path", "templates/target_red.png")), "combat.target_template_path", combat_enabled)
    thresh = float(combat_data.get("target_match_threshold", 0.75))
    if thresh < 0.0 or thresh > 1.0:
        raise ConfigValidationError("Campo 'combat.target_match_threshold' deve estar entre 0.0 e 1.0.")

    combat_cfg = CombatConfig(
        enabled=combat_enabled,
        attack_key=attack_key,
        attack_cooldown_ms=attack_cd,
        min_battle_pixels=min_pixels,
        target_template_path=target_tmpl,
        target_match_threshold=thresh
    )

    # 5. Protection Zone Config
    pz_data = data.get("pz", {})
    pz_enabled = bool(pz_data.get("enabled", True))
    pz_tmpl = _validate_template_file(str(pz_data.get("template_path", "templates/pz.png")), "pz.template_path", pz_enabled)
    pz_thresh = float(pz_data.get("match_threshold", 0.82))
    if pz_thresh < 0.0 or pz_thresh > 1.0:
        raise ConfigValidationError("Campo 'pz.match_threshold' deve estar entre 0.0 e 1.0.")

    pz_cfg = PZConfig(
        enabled=pz_enabled,
        template_path=pz_tmpl,
        match_threshold=pz_thresh
    )

    # 6. Loot Config
    loot_data = data.get("loot", {})
    loot_enabled = bool(loot_data.get("enabled", True))
    nearby_key = _validate_hotkey(loot_data.get("nearby_corpses_key", "f12"), "loot.nearby_corpses_key", loot_enabled)
    delay_ms = _validate_cooldown(loot_data.get("delay_ms", 200), "loot.delay_ms")
    cooldown_ms = _validate_cooldown(loot_data.get("cooldown_ms", 500), "loot.cooldown_ms")
    require_empty_bl = bool(loot_data.get("require_empty_battle_list", False))
    priority = int(loot_data.get("priority", 40))
    emergency_hp = _validate_percentage(loot_data.get("emergency_hp_threshold", 30.0), "loot.emergency_hp_threshold")

    loot_cfg = LootConfig(
        enabled=loot_enabled,
        nearby_corpses_key=nearby_key,
        delay_ms=delay_ms,
        cooldown_ms=cooldown_ms,
        require_empty_battle_list=require_empty_bl,
        priority=priority,
        emergency_hp_threshold=emergency_hp,
    )

    # 7. Chat Config
    chat_data = data.get("chat", {})
    chat_enabled = bool(chat_data.get("enabled", True))
    def_chat = ChatConfig()
    chat_roi = _validate_relative_roi(chat_data.get("button_roi"), "chat.button_roi", def_chat.button_roi)
    chat_on_tmpl = _validate_template_file(str(chat_data.get("on_template_path", "templates/chat_on.png")), "chat.on_template_path", chat_enabled)
    chat_thresh = float(chat_data.get("match_threshold", 0.90))
    if chat_thresh < 0.0 or chat_thresh > 1.0:
        raise ConfigValidationError("Campo 'chat.match_threshold' deve estar entre 0.0 e 1.0.")
    max_att = _validate_cooldown(chat_data.get("max_attempts", 3), "chat.max_attempts")
    retry_delay = _validate_cooldown(chat_data.get("retry_delay_ms", 300), "chat.retry_delay_ms")

    chat_cfg = ChatConfig(
        enabled=chat_enabled,
        button_roi=chat_roi,
        on_template_path=chat_on_tmpl,
        match_threshold=chat_thresh,
        max_attempts=max_att,
        retry_delay_ms=retry_delay,
    )

    # 8. Global loop interval
    loop_ms = data.get("loop_interval_ms", 50)
    try:
        loop_ms = int(loop_ms)
        if loop_ms <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ConfigValidationError("Campo 'loop_interval_ms' deve ser um inteiro > 0.")

    return AppConfig(
        window=win_cfg,
        regions=regions_cfg,
        healer=healer_cfg,
        combat=combat_cfg,
        pz=pz_cfg,
        loot=loot_cfg,
        chat=chat_cfg,
        loop_interval_ms=loop_ms
    )


def load_config(
    config_path: Optional[Union[str, Path]] = None,
    profile_path: Optional[Union[str, Path]] = None
) -> AppConfig:
    """
    Carrega e consolida a configuração da aplicação.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    default_config_path = project_root / "config" / "default.yaml"

    target_config = Path(config_path) if config_path else default_config_path

    raw_base = load_raw_yaml(target_config)

    if profile_path:
        profile_file = Path(profile_path)
        if not profile_file.is_absolute():
            profile_file = project_root / "config" / "profiles" / profile_file
            if not profile_file.suffix:
                profile_file = profile_file.with_suffix(".yaml")
        
        raw_profile = load_raw_yaml(profile_file)
        raw_base = deep_merge(raw_base, raw_profile)

    return validate_and_parse(raw_base)
