from datetime import datetime, timezone
from typing import List, Optional

from src.domain.game_state import GameState
from src.domain.bot_state import BotMode, BotState, StateTransition
from src.infrastructure.capture.frame import FrameStatus
from src.utils.logger import logger


class StateMachine:
    """
    Controlador central da Máquina de Estados Finitos do Tibia Bot.
    Avalia o GameState por ciclo e gerencia as transições de modo com auditoria.
    """

    def __init__(self, initial_mode: BotMode = BotMode.IDLE):
        self.current_state = BotState(
            current_mode=initial_mode,
            previous_mode=BotMode.STOPPED,
            reason="Inicialização do motor",
            entered_at=datetime.now(timezone.utc)
        )
        self.history: List[StateTransition] = []

    def update(self, game_state: GameState, killswitch_paused: bool = False) -> BotState:
        """
        Avalia o GameState e flags globais, aplicando a hierarquia de prioridades:
        1. Killswitch de emergência
        2. Segurança operacional (Foco, minimização, disponibilidade do projetor)
        3. Integridade da captura de tela (frame congelado/válido)
        4. Regras de Protection Zone (PZ)
        5. Estado de Combate
        6. Ocioso (IDLE)
        """
        now = datetime.now(timezone.utc)
        target_mode = BotMode.IDLE
        reason = "Aguardando eventos"

        # 1. Prioridade máxima: Killswitch ativado pelo usuário
        if killswitch_paused:
            target_mode = BotMode.PAUSED
            reason = "Killswitch ativado pelo usuário (Pause)"

        # 2. Prioridade de segurança da janela
        elif not game_state.window.projector_available:
            target_mode = BotMode.UNSAFE
            reason = "Janela do Projetor OBS não encontrada"
        elif game_state.window.tibia_minimized:
            target_mode = BotMode.UNSAFE
            reason = "Janela do Tibia minimizada"
        elif not game_state.window.tibia_focused:
            target_mode = BotMode.UNSAFE
            reason = "Janela do Tibia sem foco ativo"

        # 3. Prioridade de integridade da captura
        elif game_state.capture.status != FrameStatus.VALID:
            target_mode = BotMode.UNSAFE
            reason = f"Frame com falha/status: {game_state.capture.status.value}"
        elif game_state.capture.age_seconds > 1.0:
            target_mode = BotMode.UNSAFE
            reason = f"Frame desatualizado (idade: {game_state.capture.age_seconds:.2f}s)"

        # 4. Protection Zone
        elif game_state.player.in_protection_zone is True:
            target_mode = BotMode.IN_PROTECTION_ZONE
            reason = "Personagem dentro de Protection Zone"

        # 5. Combate ativo (alvo selecionado ou criaturas na battle list)
        elif game_state.target.has_active_target is True or game_state.target.has_monsters_in_battle is True:
            target_mode = BotMode.COMBAT
            reason = "Criaturas detectadas na Battle List / Alvo travado"

        # 6. Modo Ocioso padrão
        else:
            target_mode = BotMode.IDLE
            reason = "Nenhum combate ativo ou evento pendente"

        # Se houve mudança de modo de operação
        if target_mode != self.current_state.current_mode:
            transition = StateTransition(
                from_mode=self.current_state.current_mode,
                to_mode=target_mode,
                reason=reason,
                timestamp=now
            )
            self.history.append(transition)

            logger.log(
                "STATE",
                f"Modo alterado: {self.current_state.current_mode.value.upper()} -> {target_mode.value.upper()} | Motivo: {reason}",
                level="INFO"
            )

            self.current_state = BotState(
                current_mode=target_mode,
                previous_mode=self.current_state.current_mode,
                reason=reason,
                entered_at=now
            )

        return self.current_state
