import unittest
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

from src.config.models import AppConfig, HealerConfig, EmergencyPotionConfig
from src.domain.metrics import CycleMetrics
from src.domain.actions import ActionType, BotAction
from src.domain.game_state import GameState, CaptureState, WindowState, PlayerState, TargetState
from src.domain.bot_state import BotMode, BotState
from src.infrastructure.vision.game_analyzer import GameAnalyzer
from src.infrastructure.capture.recorded import RecordedFrameCapturer
from src.infrastructure.capture.frame import CapturedFrame, FrameStatus
from src.infrastructure.input.mock_input import MockInputController
from src.application.action_executor import ActionExecutor
from src.application.bot_engine import BotEngine
from src.application.state_machine import StateMachine
from src.application.scheduler import LoopScheduler
from src.bot.healer import AutoHealer
from src.bot.combat import AutoAttacker
from src.utils.overlay import OnScreenOverlay
from src.utils.logger import logger
from tests.utils.generate_fixtures import generate_hp_fixture


class TestDiagnosticsAndObservability(unittest.TestCase):

    def test_cycle_metrics_collection(self):
        """Verifica se o BotEngine calcula os tempos de telemetria CycleMetrics por ciclo."""
        config = AppConfig()
        img = generate_hp_fixture(0.5)
        capturer = RecordedFrameCapturer([img])
        mock_input = MockInputController()

        analyzer = GameAnalyzer(config)
        state_machine = StateMachine(initial_mode=BotMode.IDLE)
        healer = AutoHealer(config.healer)
        combat = AutoAttacker(config.combat)
        overlay = OnScreenOverlay()
        scheduler = LoopScheduler()

        class MockWindowManager:
            def is_focused(self, hwnd: int) -> bool: return True
            def is_minimized(self, hwnd: int) -> bool: return False
            def set_opacity(self, hwnd: int, opacity: int) -> bool: return True
            def reset_opacity(self, hwnd: int) -> bool: return True

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

        game_state, bot_state, metrics = engine.run_cycle()

        self.assertIsInstance(metrics, CycleMetrics)
        self.assertGreaterEqual(metrics.total_cycle_time_ms, 0.0)
        self.assertGreaterEqual(metrics.capture_time_ms, 0.0)
        self.assertGreaterEqual(metrics.analyze_time_ms, 0.0)

    def test_observe_only_mode_blocks_physical_input(self):
        """Verifica se no modo --observe-only o ActionExecutor não dispara teclas no MockInputController."""
        mock_input = MockInputController()
        executor = ActionExecutor(input_controller=mock_input)

        now = datetime.now(timezone.utc)
        safe_game_state = GameState(
            timestamp=now,
            capture=CaptureState(status=FrameStatus.VALID, captured_at=now, age_seconds=0.1),
            window=WindowState(tibia_focused=True, tibia_minimized=False, projector_available=True),
            player=PlayerState(hp_percent=0.2, mana_percent=0.5, in_protection_zone=False),
            target=TargetState(has_monsters_in_battle=False, has_active_target=False)
        )

        emerg_action = BotAction(action_type=ActionType.EMERGENCY_HEAL, priority=1, key="3", reason="Vida Baixa")

        # Executa no modo de observação (observe_only=True)
        executor.execute([emerg_action], safe_game_state, observe_only=True)

        # Tecla "3" NÃO deve estar no histórico do MockInputController
        self.assertEqual(len(mock_input.key_history), 0)

    def test_logger_has_session_id_and_file(self):
        """Verifica se o logger possui session_id e grava no app.log."""
        self.assertTrue(hasattr(logger, "session_id"))
        self.assertIsNotNone(logger.session_id)

        log_file = Path(__file__).resolve().parent.parent.parent / "logs" / "app.log"
        self.assertTrue(log_file.exists())

    def test_failed_frame_saving(self):
        """Verifica se o GameAnalyzer salva um frame congelado/falho no diretório logs/failed_frames/."""
        analyzer = GameAnalyzer(AppConfig())
        now = datetime.now(timezone.utc)
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        failed_frame = CapturedFrame(
            image=dummy_img,
            captured_at=now,
            width=100,
            height=100,
            source="test",
            status=FrameStatus.FAILED
        )

        win_state = WindowState(tibia_focused=False, tibia_minimized=True, projector_available=False)
        analyzer.analyze(failed_frame, window_state=win_state)

        failed_dir = Path(__file__).resolve().parent.parent.parent / "logs" / "failed_frames"
        self.assertTrue(failed_dir.exists())


if __name__ == "__main__":
    unittest.main()
