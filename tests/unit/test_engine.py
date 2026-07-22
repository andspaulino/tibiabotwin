import unittest
import time
from datetime import datetime, timezone
import numpy as np

from src.config.models import AppConfig
from src.domain.game_state import GameState, CaptureState, WindowState, PlayerState, TargetState
from src.domain.bot_state import BotMode, BotState
from src.domain.analyzer import GameAnalyzer
from src.application.state_machine import StateMachine
from src.application.scheduler import LoopScheduler
from src.application.bot_engine import BotEngine
from src.infrastructure.capture.base import FrameCapturer
from src.infrastructure.capture.frame import CapturedFrame, FrameStatus
from src.bot.healer import AutoHealer
from src.bot.combat import AutoAttacker
from src.utils.overlay import OnScreenOverlay


class DummyCapturer(FrameCapturer):
    def __init__(self):
        self.closed = False

    def capture(self, hwnd: int) -> CapturedFrame:
        now = datetime.now(timezone.utc)
        return CapturedFrame(
            image=np.zeros((100, 100, 3), dtype=np.uint8),
            captured_at=now,
            width=100,
            height=100,
            source="dummy",
            status=FrameStatus.VALID
        )

    def close(self) -> None:
        self.closed = True


class TestEngineAndScheduler(unittest.TestCase):

    def test_loop_scheduler(self):
        """Verifica o cálculo de métricas e controle do LoopScheduler."""
        scheduler = LoopScheduler(target_interval_ms=10.0)
        start_perf = time.perf_counter()
        
        # Simula pequeno trabalho de 1ms
        time.sleep(0.001)
        cycle_ms = scheduler.tick(start_perf)

        self.assertEqual(scheduler.total_cycles, 1)
        self.assertGreater(cycle_ms, 0.0)
        self.assertGreater(scheduler.average_fps, 0.0)

    def test_bot_engine_run_cycle(self):
        """Verifica a execução de um ciclo atômico no BotEngine."""
        config = AppConfig()
        capturer = DummyCapturer()
        analyzer = GameAnalyzer(config)
        state_machine = StateMachine(initial_mode=BotMode.IDLE)
        healer = AutoHealer()
        combat = AutoAttacker()
        overlay = OnScreenOverlay()
        scheduler = LoopScheduler()

        engine = BotEngine(
            config=config,
            capturer=capturer,
            analyzer=analyzer,
            state_machine=state_machine,
            healer=healer,
            combat=combat,
            overlay=overlay,
            scheduler=scheduler,
            hwnd_tibia=0,
            hwnd_obs=0
        )

        game_state, bot_state = engine.run_cycle()

        self.assertIsInstance(game_state, GameState)
        self.assertIsInstance(bot_state, BotState)
        # Como hwnd_tibia=0, a janela estará sem foco (UNSAFE)
        self.assertEqual(bot_state.current_mode, BotMode.UNSAFE)

        engine.stop()
        self.assertTrue(capturer.closed)


if __name__ == "__main__":
    unittest.main()
