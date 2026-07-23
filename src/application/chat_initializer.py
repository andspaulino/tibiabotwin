import time
from typing import Optional

from src.config.models import ChatConfig
from src.infrastructure.capture.base import FrameCapturer
from src.infrastructure.input.base import InputController
from src.infrastructure.window.base import WindowManager
from src.infrastructure.vision.chat_checker import is_chat_on, get_chat_button_center
from src.utils.logger import logger


class ChatInitializer:
    """
    Garante que o chat do Tibia esteja em estado OFF no arranque ou na despausa.
    Utiliza template matching procurando por chat_on.png:
    - Se encontrar Chat ON: clica nas coordenadas absolutas de tela e confirma.
    - Se NÃO encontrar Chat ON: presume Chat OFF e NÃO envia cliques.
    """

    def __init__(self, config: ChatConfig):
        self.config = config

    def ensure_chat_off(
        self,
        capturer: FrameCapturer,
        hwnd_obs: int,
        input_controller: Optional[InputController] = None,
        window_manager: Optional[WindowManager] = None,
        observe_only: bool = False
    ) -> bool:
        if not self.config.enabled:
            return True

        if hwnd_obs <= 0:
            return False

        logger.log("CHAT", "Verificando se o chat esta em estado OFF...")

        for attempt in range(1, self.config.max_attempts + 1):
            frame = capturer.capture(hwnd_obs)
            if not frame.is_valid or frame.image is None or frame.image.size == 0:
                logger.log("CHAT", f"Frame invalido na tentativa {attempt}/{self.config.max_attempts}.", level="WARNING")
                time.sleep(self.config.retry_delay_ms / 1000.0)
                continue

            # Busca o template Chat ON
            if not is_chat_on(
                frame.image,
                roi=self.config.button_roi,
                template_path=self.config.on_template_path,
                threshold=self.config.match_threshold
            ):
                logger.log("CHAT", "Chat confirmado em estado OFF (Chat ON nao detectado).", level="INFO")
                return True

            logger.log("CHAT", f"Chat detectado como ON (tentativa {attempt}/{self.config.max_attempts}). Solicitando clique...", level="WARNING")

            if observe_only:
                logger.log("SIMULATION", "[OBSERVE-ONLY] Clique no botao do chat simulado.", level="ACTION")
            elif input_controller:
                center_x, center_y = get_chat_button_center(frame.width, frame.height, self.config.button_roi)
                
                # Converte coordenadas relativas do frame para coordenadas absolutas da tela
                obs_left, obs_top = (0, 0)
                if window_manager and hwnd_obs > 0:
                    try:
                        obs_left, obs_top = window_manager.get_client_position(hwnd_obs)
                    except Exception:
                        pass

                screen_x = obs_left + center_x
                screen_y = obs_top + center_y

                logger.log("CHAT", f"Clicando no botao do chat na tela: ({screen_x}, {screen_y}) [Frame: ({center_x}, {center_y}) + OBS Client: ({obs_left}, {obs_top})]")
                input_controller.click(screen_x, screen_y)

            time.sleep(self.config.retry_delay_ms / 1000.0)

        # Última verificação pós-tentativas
        final_frame = capturer.capture(hwnd_obs)
        if final_frame.is_valid and final_frame.image is not None and not is_chat_on(
            final_frame.image,
            roi=self.config.button_roi,
            template_path=self.config.on_template_path,
            threshold=self.config.match_threshold
        ):
            logger.log("CHAT", "Chat confirmado em estado OFF na verificacao final.", level="INFO")
            return True

        logger.log("CHAT", "Nao foi possivel garantir que o Chat esta em estado OFF!", level="ERROR")
        return False
