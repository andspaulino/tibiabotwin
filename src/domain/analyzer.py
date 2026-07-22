from datetime import datetime, timezone
from typing import Optional

from src.config.models import AppConfig
from src.infrastructure.capture.frame import CapturedFrame, FrameStatus
from src.domain.game_state import (
    GameState,
    CaptureState,
    WindowState,
    PlayerState,
    TargetState,
)
from src.utils.window import is_window_active, is_window_minimized
from src.utils.screen import (
    get_hp_percentage,
    get_mp_percentage,
    is_in_pz,
    has_monsters_in_battle,
    has_active_target,
)


class GameAnalyzer:
    """
    Analisador de percepção pura. Converte um CapturedFrame e o estado das janelas
    em um snapshot imutável de GameState.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config

    def analyze(
        self,
        frame: CapturedFrame,
        hwnd_tibia: int,
        hwnd_obs: int,
        config: Optional[AppConfig] = None
    ) -> GameState:
        now = datetime.now(timezone.utc)
        cfg = config or self.config

        # 1. Analisa estado do sistema/janelas
        tibia_focused = is_window_active(hwnd_tibia) if hwnd_tibia > 0 else False
        tibia_minimized = is_window_minimized(hwnd_tibia) if hwnd_tibia > 0 else True
        projector_available = hwnd_obs > 0

        win_state = WindowState(
            tibia_focused=tibia_focused,
            tibia_minimized=tibia_minimized,
            projector_available=projector_available
        )

        cap_state = CaptureState(
            status=frame.status,
            captured_at=frame.captured_at,
            age_seconds=frame.age_seconds(now)
        )

        # 2. Se a captura for inválida ou o ambiente inseguro, retorna estado nulo (sem dados presumidos)
        if not frame.is_valid or not tibia_focused or tibia_minimized or not projector_available:
            return GameState(
                timestamp=now,
                capture=cap_state,
                window=win_state,
                player=PlayerState(hp_percent=None, mana_percent=None, in_protection_zone=None),
                target=TargetState(has_monsters_in_battle=None, has_active_target=None)
            )

        # 3. Analisa pixels e padrões visuais do frame BGR único
        img_bgr = frame.image

        hp_pct = get_hp_percentage(img_bgr, roi=cfg.regions.hp) if cfg else get_hp_percentage(img_bgr)
        mp_pct = get_mp_percentage(img_bgr, roi=cfg.regions.mana) if cfg else get_mp_percentage(img_bgr)

        in_pz = is_in_pz(
            img_bgr,
            roi=cfg.regions.status_bar if cfg else None,
            pz_template_path=cfg.pz.template_path if cfg else "templates/pz.png",
            threshold=cfg.pz.match_threshold if cfg else 0.82
        )

        has_monsters = has_monsters_in_battle(
            img_bgr,
            roi=cfg.regions.battle_list if cfg else None,
            min_pixels=cfg.combat.min_battle_pixels if cfg else 10
        )

        has_target = has_active_target(
            img_bgr,
            roi=cfg.regions.battle_list if cfg else None,
            target_template_path=cfg.combat.target_template_path if cfg else "templates/target_red.png",
            threshold=cfg.combat.target_match_threshold if cfg else 0.75
        )

        player_state = PlayerState(
            hp_percent=hp_pct,
            mana_percent=mp_pct,
            in_protection_zone=in_pz
        )

        target_state = TargetState(
            has_monsters_in_battle=has_monsters,
            has_active_target=has_target
        )

        return GameState(
            timestamp=now,
            capture=cap_state,
            window=win_state,
            player=player_state,
            target=target_state
        )
