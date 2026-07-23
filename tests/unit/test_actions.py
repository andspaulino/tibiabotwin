import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from src.domain.actions import ActionType, BotAction
from src.domain.game_state import GameState, CaptureState, WindowState, PlayerState, TargetState
from src.domain.bot_state import BotMode, BotState
from src.application.decision_controller import DecisionController
from src.application.action_executor import ActionExecutor
from src.infrastructure.input.mock_input import MockInputController
from src.infrastructure.capture.frame import FrameStatus


class TestCentralActions(unittest.TestCase):

    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.valid_capture = CaptureState(status=FrameStatus.VALID, captured_at=self.now, age_seconds=0.1)
        self.valid_window = WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True)
        self.safe_game_state = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=self.valid_window,
            player=PlayerState(hp_percent=0.5, mana_percent=0.5, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=False)
        )
        self.idle_bot_state = BotState(current_mode=BotMode.IDLE, previous_mode=BotMode.STOPPED, reason="OK")

    def test_action_immutability(self):
        """Verifica a imutabilidade da classe BotAction."""
        action = BotAction(action_type=ActionType.HEAL, priority=2, key="F1", reason="Cura")
        with self.assertRaises(FrozenInstanceError):
            action.key = "F2"  # type: ignore

    def test_decision_controller_prioritization(self):
        """Verifica se o DecisionController ordena ações por prioridade."""
        controller = DecisionController()
        attack_act = BotAction(action_type=ActionType.ATTACK, priority=4, key="space", reason="Ataque")
        heal_act = BotAction(action_type=ActionType.HEAL, priority=2, key="F1", reason="Cura")

        resolved = controller.resolve([attack_act, heal_act], self.safe_game_state, self.idle_bot_state)

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].action_type, ActionType.HEAL)

    def test_decision_controller_emergency_heal_supersedes(self):
        """Verifica se a cura de emergência substitui ações de menor prioridade."""
        controller = DecisionController()
        emerg_act = BotAction(action_type=ActionType.EMERGENCY_HEAL, priority=1, key="3", reason="Emergencia")
        attack_act = BotAction(action_type=ActionType.ATTACK, priority=4, key="space", reason="Ataque")

        resolved = controller.resolve([attack_act, emerg_act], self.safe_game_state, self.idle_bot_state)

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].action_type, ActionType.EMERGENCY_HEAL)

    def test_decision_controller_pz_rejection(self):
        """Verifica se ações ofensivas são rejeitadas em Protection Zone."""
        controller = DecisionController()
        pz_bot_state = BotState(current_mode=BotMode.IN_PROTECTION_ZONE, previous_mode=BotMode.IDLE, reason="PZ")
        attack_act = BotAction(action_type=ActionType.ATTACK, priority=4, key="space", reason="Ataque")

        resolved = controller.resolve([attack_act], self.safe_game_state, pz_bot_state)
        self.assertEqual(len(resolved), 0)

    def test_action_executor_safety_check(self):
        """Verifica se o ActionExecutor recusa execução se o estado for inseguro."""
        mock_input = MockInputController()
        executor = ActionExecutor(input_controller=mock_input)

        unsafe_game_state = GameState(
            timestamp=self.now,
            capture=CaptureState(status=FrameStatus.FAILED, captured_at=self.now, age_seconds=0.1),
            window=self.valid_window,
            player=PlayerState(hp_percent=None, mana_percent=None, in_protection_zone=None),
            target=TargetState(has_monsters_in_battle=None, has_active_target=None)
        )

        act = BotAction(action_type=ActionType.HEAL, priority=2, key="F1", reason="Cura")
        executor.execute([act], unsafe_game_state)

        self.assertEqual(len(mock_input.key_history), 0)

    def test_decision_controller_and_executor_cooldown_integration(self):
        """Verifica se o CooldownManager compartilhado impede dupla execução respeitando o cooldown_ms."""
        from src.application.cooldown_manager import CooldownManager
        import time

        cd_mgr = CooldownManager()
        controller = DecisionController(cooldown_manager=cd_mgr)
        mock_input = MockInputController()
        executor = ActionExecutor(input_controller=mock_input, cooldown_manager=cd_mgr)

        act = BotAction(action_type=ActionType.HEAL, priority=2, key="F1", reason="Cura", cooldown_ms=100)

        # 1. Primeira resolução e execução -> Deve ser permitida e executada
        resolved = controller.resolve([act], self.safe_game_state, self.idle_bot_state)
        self.assertEqual(len(resolved), 1)

        executor.execute(resolved, self.safe_game_state)
        self.assertEqual(mock_input.key_history, ["F1"])

        # 2. Segunda resolução imediata -> Deve ser bloqueada pelo cooldown
        resolved_2 = controller.resolve([act], self.safe_game_state, self.idle_bot_state)
        self.assertEqual(len(resolved_2), 0)

        # 3. Espera o cooldown passar (100ms = 0.1s)
        time.sleep(0.11)

        # 4. Terceira resolução -> Deve ser permitida novamente
        resolved_3 = controller.resolve([act], self.safe_game_state, self.idle_bot_state)
        self.assertEqual(len(resolved_3), 1)


if __name__ == "__main__":
    unittest.main()
