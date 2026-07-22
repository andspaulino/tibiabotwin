import unittest
from datetime import datetime, timezone

from src.domain.game_state import (
    GameState,
    CaptureState,
    WindowState,
    PlayerState,
    TargetState,
)
from src.domain.bot_state import BotMode, BotState
from src.application.state_machine import StateMachine
from src.infrastructure.capture.frame import FrameStatus


class TestStateMachine(unittest.TestCase):

    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.valid_capture = CaptureState(status=FrameStatus.VALID, captured_at=self.now, age_seconds=0.1)
        self.valid_window = WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True)

    def test_initial_state(self):
        """Verifica a inicialização da máquina de estados."""
        sm = StateMachine(initial_mode=BotMode.IDLE)
        self.assertEqual(sm.current_state.current_mode, BotMode.IDLE)

    def test_killswitch_priority(self):
        """Verifica se o killswitch força o estado PAUSED acima de qualquer condição de jogo."""
        sm = StateMachine()
        game_state = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=self.valid_window,
            player=PlayerState(hp_percent=0.5, mana_percent=0.5, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=True)
        )

        bot_state = sm.update(game_state, killswitch_paused=True)
        self.assertEqual(bot_state.current_mode, BotMode.PAUSED)
        self.assertEqual(len(sm.history), 1)

    def test_window_unsafe_priority(self):
        """Verifica se a falta de foco ou janela minimizada força o estado UNSAFE."""
        sm = StateMachine()

        # Janela sem foco
        unfocused_win = WindowState(tibia_focused=False, tibia_minimized=False, projector_available=True)
        gs1 = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=unfocused_win,
            player=PlayerState(hp_percent=0.8, mana_percent=0.8, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=False, has_active_target=False)
        )
        bs1 = sm.update(gs1, killswitch_paused=False)
        self.assertEqual(bs1.current_mode, BotMode.UNSAFE)

    def test_pz_priority(self):
        """Verifica transição para IN_PROTECTION_ZONE."""
        sm = StateMachine()
        gs = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=self.valid_window,
            player=PlayerState(hp_percent=0.9, mana_percent=0.9, in_protection_zone=True),
            target=TargetState(has_monsters_in_battle=False, has_active_target=False)
        )
        bs = sm.update(gs)
        self.assertEqual(bs.current_mode, BotMode.IN_PROTECTION_ZONE)

    def test_combat_priority(self):
        """Verifica transição para COMBAT quando houver inimigos ou alvo travado."""
        sm = StateMachine()
        gs = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=self.valid_window,
            player=PlayerState(hp_percent=0.9, mana_percent=0.9, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=False)
        )
        bs = sm.update(gs)
        self.assertEqual(bs.current_mode, BotMode.COMBAT)

    def test_no_duplicate_transition_spam(self):
        """Verifica se estados repetidos consecutivos não geram spam de histórico de transições."""
        sm = StateMachine()
        gs = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=self.valid_window,
            player=PlayerState(hp_percent=0.9, mana_percent=0.9, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=False)
        )

        for _ in range(10):
            sm.update(gs)

        self.assertEqual(len(sm.history), 1)
        self.assertEqual(sm.history[0].to_mode, BotMode.COMBAT)


if __name__ == "__main__":
    unittest.main()
