import unittest
from pathlib import Path
import cv2

from src.config.models import AppConfig, HealerConfig, EmergencyPotionConfig, SpellActionConfig, PotionActionConfig
from src.infrastructure.capture.recorded import RecordedFrameCapturer
from src.infrastructure.input.mock_input import MockInputController
from src.infrastructure.window.windows_manager import WindowsWindowManager
from src.domain.analyzer import GameAnalyzer
from src.domain.bot_state import BotMode
from src.domain.actions import ActionType
from src.application.state_machine import StateMachine
from src.application.scheduler import LoopScheduler
from src.application.decision_controller import DecisionController
from src.application.action_executor import ActionExecutor
from src.application.bot_engine import BotEngine
from src.bot.healer import AutoHealer
from src.bot.combat import AutoAttacker
from src.utils.overlay import OnScreenOverlay
from tests.utils.generate_fixtures import generate_hp_fixture, generate_mana_fixture


class TestFullPipelineIntegration(unittest.TestCase):

    def test_full_recorded_pipeline_emergency_heal(self):
        """
        Teste de integração de ponta a ponta sem hardware:
        Alimenta o BotEngine com um frame gravado de HP crítico e verifica a proposta,
        resolução de prioridade e disparo de tecla de emergência no MockInputController.
        """
        config = AppConfig(
            healer=HealerConfig(
                enabled=True,
                emergency_potion=EmergencyPotionConfig(enabled=True, hp_below=30.0, key="3", cooldown_ms=0),
                spell=SpellActionConfig(enabled=True, hp_below=80.0, key="F1", cooldown_ms=0),
                mana_potion=PotionActionConfig(enabled=True, threshold_below=50.0, key="F2", cooldown_ms=0)
            )
        )

        # Injeta frame gravado com HP 20%
        critical_hp_img = generate_hp_fixture(0.20)
        capturer = RecordedFrameCapturer([critical_hp_img])
        mock_input = MockInputController()

        analyzer = GameAnalyzer(config)
        state_machine = StateMachine(initial_mode=BotMode.IDLE)
        healer = AutoHealer(config.healer, input_controller=mock_input)
        combat = AutoAttacker(config.combat, input_controller=mock_input)
        overlay = OnScreenOverlay()
        scheduler = LoopScheduler()

        # Mock de WindowManager para simular janela focada sem precisar do SO
        class MockWindowManager:
            def is_focused(self, hwnd: int) -> bool:
                return True
            def is_minimized(self, hwnd: int) -> bool:
                return False
            def set_opacity(self, hwnd: int, opacity: int) -> bool:
                return True
            def reset_opacity(self, hwnd: int) -> bool:
                return True

        engine = BotEngine(
            config=config,
            capturer=capturer,
            analyzer=analyzer,
            state_machine=state_machine,
            healer=healer,
            combat=combat,
            overlay=overlay,
            scheduler=scheduler,
            hwnd_tibia=100,
            hwnd_obs=200,
            window_manager=MockWindowManager(),  # type: ignore
            input_controller=mock_input
        )

        # Ativa os módulos
        healer.start()
        combat.start()

        # Executa 1 ciclo completo da pipeline
        game_state, bot_state = engine.run_cycle()

        # Valida se a detecção percebeu HP baixo (<= 25%)
        self.assertIsNotNone(game_state.player.hp_percent)
        self.assertLessEqual(game_state.player.hp_percent, 0.30)
        self.assertTrue(game_state.is_safe_to_act)

        # Valida se a tecla "3" (Poção de Emergência) foi enviada ao MockInputController
        self.assertIn("3", mock_input.key_history)


if __name__ == "__main__":
    unittest.main()
