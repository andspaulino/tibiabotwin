from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import cv2

from src.config.models import AppConfig
from src.infrastructure.capture.frame import CapturedFrame
from src.domain.capture_status import FrameStatus
from src.domain.game_state import (
    GameState,
    CaptureState,
    WindowState,
    PlayerState,
    TargetState,
)
from src.utils.screen import (
    get_hp_percentage,
    get_mp_percentage,
    is_in_pz,
    has_monsters_in_battle,
    has_active_target,
)


class GameAnalyzer:
    """
    Analisador de percepção pura (Visão Computacional).
    Converte um CapturedFrame e um WindowState em um snapshot imutável de GameState.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config

    def _save_failed_frame(self, frame: CapturedFrame):
        """Salva um frame com falha/congelado na pasta logs/failed_frames para diagnóstico."""
        try:
            save_dir = Path(__file__).resolve().parent.parent.parent.parent / "logs" / "failed_frames"
            save_dir.mkdir(parents=True, exist_ok=True)
            filename = f"frame_{frame.captured_at.strftime('%Y%m%d_%H%M%S_%f')}_{frame.status.value}.png"
            cv2.imwrite(str(save_dir / filename), frame.image)
        except Exception:
            pass

    def analyze(
        self,
        frame: CapturedFrame,
        window_state: WindowState,
        config: Optional[AppConfig] = None
    ) -> GameState:
        now = datetime.now(timezone.utc)
        cfg = config or self.config

        cap_state = CaptureState(
            status=frame.status,
            captured_at=frame.captured_at,
            age_seconds=frame.age_seconds(now)
        )

        # 1. Se a captura for inválida ou o ambiente inseguro, retorna estado nulo (sem dados presumidos)
        if not frame.is_valid or not window_state.is_safe:
            if frame.status in (FrameStatus.FAILED, FrameStatus.FROZEN) and frame.image is not None and frame.image.size > 0:
                self._save_failed_frame(frame)

            return GameState(
                timestamp=now,
                capture=cap_state,
                window=window_state,
                player=PlayerState(hp_percent=None, mana_percent=None, in_protection_zone=None),
                target=TargetState(has_monsters_in_battle=None, has_active_target=None)
            )

        # 2. Analisa pixels e padrões visuais do frame BGR único
        img_bgr = frame.image

        hp_pct = get_hp_percentage(img_bgr, roi=cfg.regions.hp) if cfg else get_hp_percentage(img_bgr)
        mp_pct = get_mp_percentage(img_bgr, roi=cfg.regions.mana) if cfg else get_mp_percentage(img_bgr)

        # Respeita a flag pz.enabled
        if cfg and not cfg.pz.enabled:
            in_pz = None
        else:
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
            window=window_state,
            player=player_state,
            target=target_state
        )
