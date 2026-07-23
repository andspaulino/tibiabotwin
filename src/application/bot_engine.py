
import time
from pathlib import Path
from typing import Optional, Tuple, List

import cv2

try:
    import keyboard
except ImportError:
    keyboard = None

from src.config.models import AppConfig
from src.infrastructure.capture.base import FrameCapturer
from src.infrastructure.window.base import WindowManager
from src.infrastructure.input.base import InputController
from src.infrastructure.factory import create_window_manager, create_input_controller
from src.infrastructure.vision.game_analyzer import GameAnalyzer
from src.domain.game_state import GameState, WindowState
from src.domain.bot_state import BotMode, BotState
from src.domain.actions import BotAction
from src.domain.metrics import CycleMetrics
from src.application.state_machine import StateMachine
from src.application.scheduler import LoopScheduler
from src.application.decision_controller import DecisionController
from src.application.action_executor import ActionExecutor
from src.application.cooldown_manager import CooldownManager
from src.bot.healer import AutoHealer
from src.bot.combat import AutoAttacker
from src.bot.loot import AutoLootController
from src.bot.cavebot.cavebot_controller import CavebotController
from src.bot.cavebot.module import CavebotModule
from src.utils.overlay import OnScreenOverlay
from src.utils.logger import logger


class BotEngine:
    """
    Motor principal do Tibia Bot.
    Orquestra o ciclo de execução, injeção de dependências, medições de telemetria e diagnóstico.
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
        loot: Optional[AutoLootController] = None,
        window_manager: Optional[WindowManager] = None,
        input_controller: Optional[InputController] = None,
        decision_controller: Optional[DecisionController] = None,
        action_executor: Optional[ActionExecutor] = None,
        cooldown_manager: Optional[CooldownManager] = None,
        cavebot: Optional[CavebotModule] = None,
        observe_only: bool = False
    ):
        self.config = config
        self.capturer = capturer
        self.analyzer = analyzer
        self.state_machine = state_machine
        self.healer = healer
        self.combat = combat
        self.loot = loot or AutoLootController(config.loot)
        self.overlay = overlay
        self.scheduler = scheduler
        self.hwnd_tibia = hwnd_tibia
        self.hwnd_obs = hwnd_obs
        self.window_manager = window_manager or create_window_manager()
        self.input_controller = input_controller or create_input_controller()
        self.cooldown_manager = cooldown_manager or CooldownManager()
        self.decision_controller = decision_controller or DecisionController(cooldown_manager=self.cooldown_manager)
        self.action_executor = action_executor or ActionExecutor(
            input_controller=self.input_controller,
            cooldown_manager=self.cooldown_manager
        )
        self.observe_only = observe_only
        self.cavebot = cavebot or CavebotModule(
            CavebotController(config.cavebot, config.minimap)
        )
        self.last_cavebot_signature: Optional[tuple[str, str]] = None

        self.running = False
        self.killswitch_paused = False
        self.last_pz_state: Optional[bool] = None
        self.last_minimap_signature: Optional[tuple[bool, Optional[str], tuple[str, ...]]] = None
        self.last_metrics: Optional[CycleMetrics] = None
        self.previous_state: Optional[GameState] = None

    def toggle_killswitch(self, e=None):
        """Alterna a flag de emergência do Killswitch e libera teclas imediatamente."""
        self.killswitch_paused = not self.killswitch_paused
        if self.killswitch_paused:
            if self.input_controller:
                try:
                    self.input_controller.release_all()
                except Exception:
                    pass
            logger.log("SYSTEM", "🛑 KILLSWITCH ACIONADO: Bot PAUSADO. Teclas liberadas imediatamente.", level="WARNING")
        else:
            logger.log("SYSTEM", "▶️ KILLSWITCH DESATIVADO: Bot RETOMADO.", level="INFO")

    def _save_minimap_diagnostic(self, frame_image, game_state: GameState) -> None:
        """Salva o último recorte analisado para calibrar a ROI sem nova captura."""
        minimap = game_state.minimap
        if not minimap.available or minimap.bounds is None or frame_image is None:
            return

        bounds = minimap.bounds
        cropped = frame_image[bounds.y:bounds.y + bounds.height, bounds.x:bounds.x + bounds.width]
        if getattr(cropped, "size", 0) == 0:
            return

        output_dir = Path(__file__).resolve().parent.parent.parent / "logs" / "minimap"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "latest.png"
        if cv2.imwrite(str(output_path), cropped):
            logger.log("MINIMAP", f"Recorte de diagnóstico salvo em {output_path}", level="INFO")

    def _log_minimap_state(self, game_state: GameState, frame_image) -> None:
        """Registra alterações relevantes da percepção do minimapa sem poluir o log por frame."""
        minimap = game_state.minimap
        marker_ids = tuple(sorted(marker.template_id for marker in minimap.markers))
        signature = (minimap.available, minimap.reason, marker_ids)
        if signature == self.last_minimap_signature:
            return

        self.last_minimap_signature = signature
        self._save_minimap_diagnostic(frame_image, game_state)
        if not minimap.available:
            logger.log("MINIMAP", f"Indisponível: {minimap.reason or 'motivo desconhecido'}", level="WARNING")
            return

        assert minimap.bounds is not None
        if not minimap.markers:
            logger.log(
                "MINIMAP",
                f"ROI ativa em x={minimap.bounds.x}, y={minimap.bounds.y}, "
                f"w={minimap.bounds.width}, h={minimap.bounds.height}; nenhum marcador encontrado.",
                level="INFO",
            )
            return

        details = ", ".join(
            f"{marker.template_id}@{marker.center} ({marker.confidence:.2f})"
            for marker in minimap.markers
        )
        logger.log("MINIMAP", f"Marcadores detectados: {details}", level="INFO")

    def _log_cavebot_intent(self, status: str, reason: str) -> None:
        signature = (status, reason)
        if signature == self.last_cavebot_signature:
            return
        self.last_cavebot_signature = signature
        logger.log("CAVEBOT", f"{status}: {reason}", level="INFO")

    def run_cycle(self) -> Tuple[GameState, BotState, CycleMetrics]:
        t0 = time.perf_counter()

        # 1. Captura única de frame por ciclo
        frame = self.capturer.capture(self.hwnd_obs)
        t1 = time.perf_counter()

        # 2. Constrói WindowState através da abstração WindowManager
        tibia_focused = self.window_manager.is_focused(self.hwnd_tibia) if self.hwnd_tibia > 0 else False
        tibia_minimized = self.window_manager.is_minimized(self.hwnd_tibia) if self.hwnd_tibia > 0 else True
        projector_available = self.hwnd_obs > 0

        window_state = WindowState(
            tibia_focused=tibia_focused,
            tibia_minimized=tibia_minimized,
            projector_available=projector_available
        )

        # 3. Converte percepção em snapshot imutável de GameState
        game_state: GameState = self.analyzer.analyze(frame, window_state, self.config)
        self._log_minimap_state(game_state, frame.image)
        t2 = time.perf_counter()

        # 4. Inspeciona a rota antes do modo global, sem executar nem autorizar input.
        inspected_cavebot_intent = self.cavebot.inspect(game_state)

        # 5. Atualiza a Máquina de Estados Finitos.
        bot_state: BotState = self.state_machine.update(
            game_state,
            self.killswitch_paused,
            movement_requested=inspected_cavebot_intent.movement_requested,
        )

        # 6. Só então o módulo propõe a ação compatível com o modo global final.
        final_cavebot_intent = self.cavebot.propose(
            game_state,
            bot_state,
            inspected_cavebot_intent,
        )
        self._log_cavebot_intent(final_cavebot_intent.status.value, final_cavebot_intent.reason)

        # 7. Log de transição ao entrar/sair de PZ
        in_pz = game_state.player.in_protection_zone
        if self.last_pz_state is not None and in_pz is not None and in_pz != self.last_pz_state:
            if in_pz:
                logger.log("PZ", "Entrou em PZ", level="ACTION")
            else:
                logger.log("PZ", "Saiu de PZ", level="ACTION")
        if in_pz is not None:
            self.last_pz_state = in_pz

        # 8. Renderização do HUD Overlay
        self.overlay.update(game_state, bot_state, observe_only=self.observe_only)

        # 9. Coleta intenções de ações dos módulos
        proposed_actions: List[BotAction] = []
        proposed_actions.extend(self.healer.get_proposed_actions(game_state))
        proposed_actions.extend(self.combat.get_proposed_actions(game_state))
        if self.loot:
            proposed_actions.extend(self.loot.get_proposed_actions(game_state, self.previous_state))
        # Nesta fase, o Cavebot só entra no executor em --observe-only.
        if self.observe_only and bot_state.current_mode == BotMode.MOVING and final_cavebot_intent.action is not None:
            proposed_actions.append(final_cavebot_intent.action)
            self.cavebot.record_simulated_request()

        # Atualiza o estado do ciclo anterior
        self.previous_state = game_state

        # 10. Resolução de conflitos e prioridades pelo DecisionController
        resolved_actions = self.decision_controller.resolve(
            proposed_actions, game_state, bot_state, config=self.config
        )
        t3 = time.perf_counter()

        # 11. Execução de ações pelo ActionExecutor
        self.action_executor.execute(
            resolved_actions, game_state, observe_only=self.observe_only
        )
        t4 = time.perf_counter()

        metrics = CycleMetrics(
            capture_time_ms=(t1 - t0) * 1000.0,
            analyze_time_ms=(t2 - t1) * 1000.0,
            decision_time_ms=(t3 - t2) * 1000.0,
            total_cycle_time_ms=(t4 - t0) * 1000.0
        )
        self.last_metrics = metrics

        return game_state, bot_state, metrics

    def _register_module_toggles(self) -> None:
        """Registra toggles que apenas alteram o estado dos módulos."""
        keyboard_module = keyboard
        if keyboard_module is None:
            return

        module_toggles = (
            (self.config.module_hotkeys.healer_toggle, self.healer.toggle, "HEALER"),
            (self.config.module_hotkeys.combat_toggle, self.combat.toggle, "COMBAT"),
            (self.config.module_hotkeys.loot_toggle, self.loot.toggle, "LOOT"),
            (self.config.module_hotkeys.cavebot_toggle, self.cavebot.toggle, "CAVEBOT"),
        )
        for key, toggle, module_name in module_toggles:
            keyboard_module.on_press_key(key, lambda event, callback=toggle: callback())
            logger.log("SYSTEM", f"Toggle de {module_name} registrado na tecla {key.upper()}.")

    def run(self):
        """Inicia o loop contínuo do motor principal."""
        self.running = True

        if self.observe_only:
            logger.log("SYSTEM", "🔍 MODO DE OBSERVAÇÃO ATIVO (--observe-only). Teclado e mouse FÍSICOS DESABILITADOS.")

        # Registra o Killswitch e os toggles globais dos módulos.
        if keyboard is not None:
            try:
                keyboard.on_press_key("pause", self.toggle_killswitch)
                logger.log("SYSTEM", "Killswitch registrado na tecla PAUSE.")
                self._register_module_toggles()
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
            if self.loot:
                self.loot.start()
            self.cavebot.start()

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

        if self.loot:
            self.loot.stop()

        self.cavebot.stop()

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
