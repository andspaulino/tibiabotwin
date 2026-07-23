import time
from typing import Optional

from src.config.models import ChatConfig
from src.infrastructure.capture.base import FrameCapturer
from src.infrastructure.input.base import InputController
from src.infrastructure.vision.chat_checker import is_chat_off, get_chat_button_center
from src.utils.logger import logger


class ChatInitializer:
    """
    Garante que o chat do Tibia esteja em estado OFF antes ou durante a execução do bot.
    Usa template matching na ROI do botão do chat para não clicar desnecessariamente se já estiver OFF.
    """

    def __init__(self, config: ChatConfig):
        self.config = config

    def ensure_chat_off(
        self,
        capturer: FrameCapturer,
        hwnd_obs: int,
        input_controller: Optional[InputController] = None,
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

            if is_chat_off(
                frame.image,
                roi=self.config.button_roi,
                template_path=self.config.off_template_path,
                threshold=self.config.match_threshold
            ):
                logger.log("CHAT", "Chat confirmado em estado OFF.", level="INFO")
                return True

            logger.log("CHAT", f"Chat detectado como ON (tentativa {attempt}/{self.config.max_attempts}). Solicitando clique...", level="WARNING")

            if observe_only:
                logger.log("SIMULATION", "[OBSERVE-ONLY] Clique no botao do chat simulado.", level="ACTION")
            elif input_controller:
                center_x, center_y = get_chat_button_center(frame.width, frame.height, self.config.button_roi)
                input_controller.click(center_x, center_y)

            time.sleep(self.config.retry_delay_ms / 1000.0)

        # Última verificação pós-tentativas
        final_frame = capturer.capture(hwnd_obs)
        if final_frame.is_valid and final_frame.image is not None and is_chat_off(
            final_frame.image,
            roi=self.config.button_roi,
            template_path=self.config.off_template_path,
            threshold=self.config.match_threshold
        ):
            logger.log("CHAT", "Chat confirmado em estado OFF na verificacao final.", level="INFO")
            return True

        logger.log("CHAT", "Nao foi possivel garantir que o Chat esta em estado OFF!", level="ERROR")
        return False
