import time
import unittest
from datetime import datetime, timezone

from src.config.models import LootConfig
from src.domain.actions import ActionPriority, ActionType, BotAction, KeyPayload
from src.domain.game_state import GameState, CaptureState, WindowState, PlayerState, TargetState
from src.domain.bot_state import BotMode, BotState
from src.bot.loot import AutoLootController
from src.application.decision_controller import DecisionController
from src.infrastructure.capture.frame import FrameStatus


class TestAutoLootController(unittest.TestCase):

    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.valid_capture = CaptureState(status=FrameStatus.VALID, captured_at=self.now, age_seconds=0.1)
        self.valid_window = WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True)
        
        self.state_active_target = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=self.valid_window,
            player=PlayerState(hp_percent=0.9, mana_percent=0.8, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=True)
        )

        self.state_no_target = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=self.valid_window,
            player=PlayerState(hp_percent=0.9, mana_percent=0.8, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=False)
        )

        self.idle_bot_state = BotState(current_mode=BotMode.IDLE, previous_mode=BotMode.STOPPED, reason="OK")
        self.config = LootConfig(enabled=True, nearby_corpses_key="x", delay_ms=50, cooldown_ms=500)
        self.loot_controller = AutoLootController(self.config)
        self.loot_controller.start()
        self.assertFalse(self.loot_controller.enabled)
        self.assertTrue(self.loot_controller.toggle())

    def test_loot_triggered_on_target_loss(self):
        """Verifica se o AutoLoot propõe a ação LOOT_NEARBY após transição de alvo ativo para inativo mantendo o estado pendente."""
        # 1ª iteração: detecta o desaparecimento (active->inactive) e entra em estado pendente (loot_pending = True)
        actions = self.loot_controller.get_proposed_actions(
            current_state=self.state_no_target,
            previous_state=self.state_active_target
        )
        self.assertEqual(len(actions), 0)
        self.assertTrue(self.loot_controller.loot_pending)
        self.assertTrue(self.loot_controller.blocks_movement)

        # Aguarda o tempo de delay (50ms)
        time.sleep(0.06)

        # 2ª iteração: mesmo no ciclo seguinte onde previous_state.has_active_target já é False, processa o estado pendente!
        actions = self.loot_controller.get_proposed_actions(
            current_state=self.state_no_target,
            previous_state=self.state_no_target
        )
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].action_type, ActionType.LOOT_NEARBY)
        self.assertEqual(actions[0].payload, KeyPayload("x"))
        self.assertFalse(self.loot_controller.loot_pending)
        self.assertFalse(self.loot_controller.blocks_movement)

    def test_prevents_duplicate_loot_for_same_target(self):
        """Verifica que o AutoLoot não gera ações duplicadas para o mesmo alvo derrotado."""
        # Primeira passagem e disparo
        self.loot_controller.get_proposed_actions(self.state_no_target, self.state_active_target)
        time.sleep(0.06)
        actions = self.loot_controller.get_proposed_actions(self.state_no_target, self.state_no_target)
        self.assertEqual(len(actions), 1)

        # Próximas iterações mantendo sem alvo
        actions_dup = self.loot_controller.get_proposed_actions(self.state_no_target, self.state_no_target)
        self.assertEqual(len(actions_dup), 0)

    def test_resets_on_new_active_target(self):
        """Verifica se o surgimento de um novo alvo reseta a flag e permite novo loot posteriormente."""
        # Primeiro alvo é derrotado
        self.loot_controller.get_proposed_actions(self.state_no_target, self.state_active_target)
        time.sleep(0.06)
        self.loot_controller.get_proposed_actions(self.state_no_target, self.state_no_target)

        # Novo alvo trava (has_active_target = True)
        self.loot_controller.get_proposed_actions(self.state_active_target, self.state_no_target)

        # Segundo alvo é derrotado
        self.loot_controller.get_proposed_actions(self.state_no_target, self.state_active_target)
        time.sleep(0.06)
        actions = self.loot_controller.get_proposed_actions(self.state_no_target, self.state_no_target)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].action_type, ActionType.LOOT_NEARBY)

    def test_cancels_loot_on_emergency_hp(self):
        """Verifica se o loot é cancelado quando o HP está em estado crítico de emergência."""
        critical_hp_state = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=self.valid_window,
            player=PlayerState(hp_percent=0.25, mana_percent=0.8, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=True, has_active_target=False)
        )
        self.loot_controller.get_proposed_actions(self.state_no_target, self.state_active_target)
        time.sleep(0.06)

        actions = self.loot_controller.get_proposed_actions(critical_hp_state, self.state_active_target)
        self.assertEqual(len(actions), 0)

    def test_cancels_loot_in_protection_zone(self):
        """Verifica se o loot é cancelado quando o personagem entra em Protection Zone."""
        pz_state = GameState(
            timestamp=self.now,
            capture=self.valid_capture,
            window=self.valid_window,
            player=PlayerState(hp_percent=0.9, mana_percent=0.8, in_protection_zone=True),
            target=TargetState(has_monsters_in_battle=False, has_active_target=False)
        )
        self.loot_controller.get_proposed_actions(self.state_no_target, self.state_active_target)
        time.sleep(0.06)

        actions = self.loot_controller.get_proposed_actions(pz_state, self.state_active_target)
        self.assertEqual(len(actions), 0)

    def test_decision_controller_resolves_loot_nearby(self):
        """Verifica se o DecisionController resolve a ação LOOT_NEARBY respeitando a regra de PZ."""
        decision_controller = DecisionController()
        loot_action = BotAction(
            action_type=ActionType.LOOT_NEARBY,
            priority=ActionPriority.LOOT,
            payload=KeyPayload("f12"),
            reason="Quick Loot",
        )

        # 1. Em área segura
        resolved = decision_controller.resolve([loot_action], self.state_no_target, self.idle_bot_state)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].action_type, ActionType.LOOT_NEARBY)

        # 2. Em Protection Zone (BotMode.IN_PROTECTION_ZONE)
        pz_bot_state = BotState(current_mode=BotMode.IN_PROTECTION_ZONE, previous_mode=BotMode.IDLE, reason="PZ")
        resolved_pz = decision_controller.resolve([loot_action], self.state_no_target, pz_bot_state)
        self.assertEqual(len(resolved_pz), 0)


if __name__ == "__main__":
    unittest.main()
