import time
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from src.application.action_executor import ActionExecutor
from src.application.cooldown_manager import CooldownManager
from src.application.decision_controller import DecisionController
from src.domain.actions import ActionPriority, ActionType, BotAction, KeyPayload, MouseClickPayload
from src.domain.bot_state import BotMode, BotState
from src.domain.capture_status import FrameStatus
from src.domain.game_state import CaptureState, GameState, PlayerState, TargetState, WindowState
from src.infrastructure.input.mock_input import MockInputController


class TestCentralActions(unittest.TestCase):
    def setUp(self) -> None:
        now = datetime.now(timezone.utc)
        self.safe_game_state = GameState(
            timestamp=now,
            capture=CaptureState(status=FrameStatus.VALID, captured_at=now, age_seconds=0.1),
            window=WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
            player=PlayerState(hp_percent=0.5, mana_percent=0.5, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=False),
        )
        self.idle_bot_state = BotState(current_mode=BotMode.IDLE, previous_mode=BotMode.STOPPED, reason="OK")

    def test_action_is_immutable_and_requires_typed_payload(self) -> None:
        action = BotAction(
            action_type=ActionType.HEAL,
            priority=ActionPriority.HEAL,
            payload=KeyPayload("F1"),
            reason="Cura",
        )
        with self.assertRaises(FrozenInstanceError):
            action.payload = KeyPayload("F2")  # type: ignore[misc]

    def test_higher_explicit_priority_wins(self) -> None:
        controller = DecisionController()
        attack = BotAction(ActionType.ATTACK, ActionPriority.ATTACK, KeyPayload("space"), "Ataque")
        heal = BotAction(ActionType.HEAL, ActionPriority.HEAL, KeyPayload("F1"), "Cura")

        resolved = controller.resolve([attack, heal], self.safe_game_state, self.idle_bot_state)
        self.assertEqual(resolved, [heal])

    def test_mouse_click_is_dispatched_by_central_executor(self) -> None:
        mock_input = MockInputController()
        executor = ActionExecutor(input_controller=mock_input)
        action = BotAction(
            action_type=ActionType.MOVE,
            priority=ActionPriority.MOVEMENT,
            payload=MouseClickPayload(x=120, y=240),
            reason="Clique de teste",
            cooldown_ms=100,
            cooldown_key="test:move",
        )

        executor.execute([action], self.safe_game_state)
        self.assertEqual(mock_input.click_history, [(120, 240, "left")])

    def test_final_validator_blocks_click_without_consuming_cooldown(self) -> None:
        mock_input = MockInputController()
        cooldowns = CooldownManager()
        executor = ActionExecutor(input_controller=mock_input, cooldown_manager=cooldowns)
        action = BotAction(
            action_type=ActionType.MOVE,
            priority=ActionPriority.MOVEMENT,
            payload=MouseClickPayload(x=120, y=240),
            reason="Clique bloqueado na revalidação",
            cooldown_ms=1_000,
            cooldown_key="test:blocked-move",
        )

        executed = executor.execute(
            [action],
            self.safe_game_state,
            final_validator=lambda candidate: False,
        )

        self.assertEqual(executed, [])
        self.assertEqual(mock_input.click_history, [])
        self.assertTrue(cooldowns.can_execute("test:blocked-move", 1_000, time.time()))

    def test_observe_only_simulates_click_without_cooldown_or_input(self) -> None:
        mock_input = MockInputController()
        cooldowns = CooldownManager()
        executor = ActionExecutor(input_controller=mock_input, cooldown_manager=cooldowns)
        action = BotAction(
            action_type=ActionType.MOVE,
            priority=ActionPriority.MOVEMENT,
            payload=MouseClickPayload(x=120, y=240),
            reason="Clique simulado",
            cooldown_ms=1_000,
            cooldown_key="test:move",
        )

        executor.execute([action], self.safe_game_state, observe_only=True)
        self.assertEqual(mock_input.click_history, [])
        self.assertTrue(cooldowns.can_execute("test:move", 1_000, time.time()))

    def test_discarded_action_does_not_consume_cooldown(self) -> None:
        cooldowns = CooldownManager()
        controller = DecisionController(cooldown_manager=cooldowns)
        action = BotAction(
            ActionType.HEAL,
            ActionPriority.HEAL,
            KeyPayload("F1"),
            "Cura",
            cooldown_ms=1_000,
            cooldown_key="healer:spell",
        )
        unsafe_state = BotState(current_mode=BotMode.UNSAFE, previous_mode=BotMode.IDLE, reason="Sem foco")

        self.assertEqual(controller.resolve([action], self.safe_game_state, unsafe_state), [])
        self.assertTrue(cooldowns.can_execute("healer:spell", 1_000, time.time()))

    def test_executed_action_consumes_its_independent_cooldown(self) -> None:
        cooldowns = CooldownManager()
        controller = DecisionController(cooldown_manager=cooldowns)
        mock_input = MockInputController()
        executor = ActionExecutor(input_controller=mock_input, cooldown_manager=cooldowns)
        action = BotAction(
            ActionType.HEAL,
            ActionPriority.HEAL,
            KeyPayload("F1"),
            "Cura",
            cooldown_ms=1_000,
            cooldown_key="healer:spell",
        )

        resolved = controller.resolve([action], self.safe_game_state, self.idle_bot_state)
        executor.execute(resolved, self.safe_game_state)
        self.assertEqual(mock_input.key_history, ["F1"])
        self.assertEqual(controller.resolve([action], self.safe_game_state, self.idle_bot_state), [])


if __name__ == "__main__":
    unittest.main()
