import sys
import time
from typing import Optional, Tuple, List

try:
    import keyboard
except ImportError:
    keyboard = None

from src.config.models import AppConfig
from src.infrastructure.capture.base import FrameCapturer
from src.infrastructure.window.base import WindowManager
from src.infrastructure.input.base import InputController
from src.infrastructure.factory import create_window_manager, create_input_controller
from src.domain.game_state import GameState
from src.domain.bot_state import BotState, BotMode
from src.domain.actions import BotAction
from src.domain.analyzer import GameAnalyzer
from src.application.state_machine import StateMachine
from src.application.scheduler import LoopScheduler
from src.application.decision_controller import DecisionController
from src.application.action_executor import ActionExecutor
from src.bot.healer import AutoHealer
from src.bot.combat import AutoAttacker
from src.utils.overlay import OnScreenOverlay
from src.utils.logger import logger


class BotEngine:
    """
    Motor principal do Tibia Bot.
    Orquestra o ciclo de execução, injeção de dependências e gerenciamento de recursos.
    """

    def __init__(
        self,
        config: AppConfig,
        capturer: FrameCapturer,
        analyzer: GameAnalyzer,
        state_machine: StateMachine,
        healer: AutoHealer,
        combat: AutoAttacker,
        overlay: OnScreenOverlay,
        scheduler: LoopScheduler,
        hwnd_tibia: int,
        hwnd_obs: int,
        window_manager: Optional[WindowManager] = None,
        input_controller: Optional[InputController] = None,
        decision_controller: Optional[DecisionController] = None,
        action_executor: Optional[ActionExecutor] = None
    ):
        self.config = config
        self.capturer = capturer
        self.analyzer = analyzer
        self.state_machine = state_machine
        self.healer = healer
        self.combat = combat
        self.overlay = overlay
        self.scheduler = scheduler
        self.hwnd_tibia = hwnd_tibia
        self.hwnd_obs = hwnd_obs
        self.window_manager = window_manager or create_window_manager()
        self.input_controller = input_controller or create_input_controller()
        self.decision_controller = decision_controller or DecisionController()
        self.action_executor = action_executor or ActionExecutor()

        self.running = False
        self.killswitch_paused = False
        self.last_pz_state: Optional[bool] = None

    def toggle_killswitch(self, e=None):
        """Alterna a flag de emergência do Killswitch."""
        self.killswitch_paused = not self.killswitch_paused
        if self.killswitch_paused:
            logger.log("SYSTEM", "🛑 KILLSWITCH ACIONADO: Bot PAUSADO (tecla PAUSE).", level="WARNING")
        else:
            logger.log("SYSTEM", "▶️ KILLSWITCH DESATIVADO: Bot RETOMADO.", level="INFO")

    def run_cycle(self) -> Tuple[GameState, BotState]:
        # 1. Captura única de frame por ciclo
        frame = self.capturer.capture(self.hwnd_obs)

        # 2. Converte percepção em snapshot imutável de GameState
        game_state: GameState = self.analyzer.analyze(
            frame, self.hwnd_tibia, self.hwnd_obs, self.config
        )

        # 3. Atualiza a Máquina de Estados Finitos
        bot_state: BotState = self.state_machine.update(game_state, self.killswitch_paused)

        # 4. Log de transição ao entrar/sair de PZ
        in_pz = game_state.player.in_protection_zone
        if self.last_pz_state is not None and in_pz is not None and in_pz != self.last_pz_state:
            if in_pz:
                logger.log("PZ", "Entrou em PZ", level="ACTION")
            else:
                logger.log("PZ", "Saiu de PZ", level="ACTION")
        if in_pz is not None:
            self.last_pz_state = in_pz

        # 5. Renderização do HUD Overlay
        self.overlay.update(game_state, bot_state)

        # 6. Coleta intenções de ações dos módulos
        proposed_actions: List[BotAction] = []
        proposed_actions.extend(self.healer.get_proposed_actions(game_state))
        proposed_actions.extend(self.combat.get_proposed_actions(game_state))

        # 7. Resolução de conflitos e prioridades pelo DecisionController
        resolved_actions = self.decision_controller.resolve(proposed_actions, game_state, bot_state)

        # 8. Execução segura das ações autorizadas pelo ActionExecutor
        self.action_executor.execute(resolved_actions, game_state, self.input_controller)

        return game_state, bot_state

    def run(self):
        """Inicia o loop contínuo do motor principal."""
        self.running = True

        # Registra o Killswitch na tecla Pause
        if keyboard is not None:
            try:
                keyboard.on_press_key('pause', self.toggle_killswitch)
                logger.log("SYSTEM", "Killswitch registrado na tecla PAUSE.")
            except Exception as err:
                logger.log("SYSTEM", f"Aviso ao registrar hotkey global: {err}", level="WARNING")

        logger.log("SYSTEM", "Aplicando opacidade para ocultar a janela do Tibia...")
        if self.hwnd_tibia > 0:
            self.window_manager.set_opacity(self.hwnd_tibia, 1)
        logger.log("SYSTEM", "Janela do Tibia configurada como INVISIVEL.")

        try:
            logger.log("SYSTEM", "Iniciando modulos do bot e Overlay de tela...")
            self.overlay.start()
            self.healer.start()
            self.combat.start()

            logger.log("SYSTEM", "Engine em execucao. Pressione Ctrl+C ou PAUSE para parar.")

            while self.running:
                start_perf = time.perf_counter()
                self.run_cycle()
                self.scheduler.tick(start_perf)

        except KeyboardInterrupt:
            logger.log("SYSTEM", "Encerrando bot por solicitacao do usuario...")
        finally:
            self.stop()

    def stop(self):
        """Encerra o motor graciosamente e restaura recursos e visibilidade."""
        self.running = False
        logger.log("SYSTEM", "Restaurando visibilidade normal da janela do Tibia...")
        
        if keyboard is not None:
            try:
                keyboard.unhook_all()
            except Exception:
                pass

        if self.input_controller:
            try:
                self.input_controller.release_all()
            except Exception:
                pass

        if self.overlay:
            self.overlay.stop()

        if self.hwnd_tibia > 0 and self.window_manager:
            self.window_manager.reset_opacity(self.hwnd_tibia)

        if self.capturer:
            try:
                self.capturer.close()
            except Exception:
                pass

        logger.log("SYSTEM", "Visibilidade restaurada. Engine encerrado com sucesso.")
