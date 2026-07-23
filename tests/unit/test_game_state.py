import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import numpy as np

from src.domain.game_state import (
    GameState,
    CaptureState,
    WindowState,
    PlayerState,
    TargetState,
)
from src.infrastructure.vision.game_analyzer import GameAnalyzer
from src.infrastructure.capture.frame import CapturedFrame, FrameStatus
from src.bot.healer import AutoHealer
from src.bot.combat import AutoAttacker
from src.config.models import AppConfig


class TestGameState(unittest.TestCase):

    def test_game_state_immutability(self):
        """Verifica se os objetos de estado são imutáveis (dataclass frozen=True)."""
        now = datetime.now(timezone.utc)
        state = GameState(
            timestamp=now,
            capture=CaptureState(status=FrameStatus.VALID, captured_at=now, age_seconds=0.1),
            window=WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
            player=PlayerState(hp_percent=0.8, mana_percent=0.5, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=True)
        )

        with self.assertRaises(FrozenInstanceError):
            state.timestamp = now  # type: ignore

        with self.assertRaises(FrozenInstanceError):
            state.player.hp_percent = 0.5  # type: ignore

    def test_is_safe_to_act(self):
        """Verifica as regras de segurança do is_safe_to_act."""
        now = datetime.now(timezone.utc)

        # Estado seguro válido
        safe_state = GameState(
            timestamp=now,
            capture=CaptureState(status=FrameStatus.VALID, captured_at=now, age_seconds=0.1),
            window=WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
            player=PlayerState(hp_percent=0.8, mana_percent=0.5, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=True)
        )
        self.assertTrue(safe_state.is_safe_to_act)

        # Sem foco
        unfocused_state = GameState(
            timestamp=now,
            capture=CaptureState(status=FrameStatus.VALID, captured_at=now, age_seconds=0.1),
            window=WindowState(tibia_focused=False, tibia_minimized=False, projector_available=True),
            player=PlayerState(hp_percent=0.8, mana_percent=0.5, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=True)
        )
        self.assertFalse(unfocused_state.is_safe_to_act)

        # Frame congelado/com falha
        frozen_state = GameState(
            timestamp=now,
            capture=CaptureState(status=FrameStatus.FROZEN, captured_at=now, age_seconds=0.1),
            window=WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
            player=PlayerState(hp_percent=0.8, mana_percent=0.5, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=True)
        )
        self.assertFalse(frozen_state.is_safe_to_act)

    def test_analyzer_failed_frame_returns_nones(self):
        """Verifica se a análise de frame inválido resulta em valores None sem dados presumidos."""
        now = datetime.now(timezone.utc)
        failed_frame = CapturedFrame(
            image=np.empty((0, 0, 3), dtype=np.uint8),
            captured_at=now,
            width=0,
            height=0,
            status=FrameStatus.FAILED
        )

        win_state = WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True)
        analyzer = GameAnalyzer()
        game_state = analyzer.analyze(failed_frame, window_state=win_state)

        self.assertFalse(game_state.is_safe_to_act)
        self.assertIsNone(game_state.player.hp_percent)
        self.assertIsNone(game_state.player.mana_percent)
        self.assertIsNone(game_state.player.in_protection_zone)
        self.assertIsNone(game_state.target.has_monsters_in_battle)
        self.assertIsNone(game_state.target.has_active_target)

    def test_modules_consume_game_state(self):
        """Verifica se AutoHealer e AutoAttacker consomem GameState sem erros."""
        now = datetime.now(timezone.utc)
        safe_state = GameState(
            timestamp=now,
            capture=CaptureState(status=FrameStatus.VALID, captured_at=now, age_seconds=0.1),
            window=WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
            player=PlayerState(hp_percent=0.95, mana_percent=0.9, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=False, has_active_target=False)
        )

        healer = AutoHealer()
        healer.start()
        # Não deve disparar hotkey se a vida estiver cheia (95%)
        healer.get_proposed_actions(safe_state)

        combat = AutoAttacker()
        combat.start()
        # Não deve disparar ataque se não há monstros
        combat.get_proposed_actions(safe_state)


if __name__ == "__main__":
    unittest.main()
