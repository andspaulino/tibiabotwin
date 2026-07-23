import unittest
from datetime import datetime, timezone

from src.infrastructure.input.mock_input import MockInputController
from src.infrastructure.factory import create_input_controller, create_window_manager
from src.domain.game_state import GameState, CaptureState, WindowState, PlayerState, TargetState
from src.infrastructure.capture.frame import FrameStatus
from src.bot.healer import AutoHealer
from src.bot.combat import AutoAttacker
from src.config.models import HealerConfig, SpellActionConfig, CombatConfig
from src.domain.actions import KeyPayload


class TestPlatformAbstractions(unittest.TestCase):

    def test_mock_input_controller(self):
        """Verifica o comportamento do MockInputController."""
        mock_input = MockInputController()
        mock_input.press_key("F1")
        mock_input.click(100, 200, button="right")
        mock_input.release_all()

        self.assertEqual(mock_input.key_history, ["F1"])
        self.assertEqual(mock_input.click_history, [(100, 200, "right")])
        self.assertTrue(mock_input.released_all)

    def test_factory_mock_creation(self):
        """Verifica se a fábrica cria MockInputController quando solicitado."""
        mock_input = create_input_controller(mock=True)
        self.assertIsInstance(mock_input, MockInputController)

    def test_healer_proposes_action(self):
        """Verifica se o AutoHealer propõe a ação correta sem executar inputs físicos."""
        cfg = HealerConfig(spell=SpellActionConfig(enabled=True, hp_below=80.0, key="F1", cooldown_ms=0))
        healer = AutoHealer(config=cfg)
        healer.start()

        now = datetime.now(timezone.utc)
        low_hp_state = GameState(
            timestamp=now,
            capture=CaptureState(status=FrameStatus.VALID, captured_at=now, age_seconds=0.1),
            window=WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
            player=PlayerState(hp_percent=0.5, mana_percent=0.9, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=False, has_active_target=False)
        )

        actions = healer.get_proposed_actions(low_hp_state)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].payload, KeyPayload("F1"))

    def test_combat_proposes_action(self):
        """Verifica se o AutoAttacker propõe a ação de ataque sem executar inputs físicos."""
        cfg = CombatConfig(enabled=True, attack_key="space", attack_cooldown_ms=0)
        combat = AutoAttacker(config=cfg)
        combat.start()

        now = datetime.now(timezone.utc)
        combat_state = GameState(
            timestamp=now,
            capture=CaptureState(status=FrameStatus.VALID, captured_at=now, age_seconds=0.1),
            window=WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
            player=PlayerState(hp_percent=0.9, mana_percent=0.9, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=False)
        )

        actions = combat.get_proposed_actions(combat_state)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].payload, KeyPayload("space"))


if __name__ == "__main__":
    unittest.main()
