import argparse
import os
import sys

# Garante importações a partir do diretório raiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import load_config, ConfigValidationError, AppConfig, WindowConfig
from src.infrastructure.capture import ProjectorFrameCapturer
from src.domain.analyzer import GameAnalyzer
from src.domain.bot_state import BotMode
from src.application import StateMachine, LoopScheduler, BotEngine
from src.utils.window import find_windows_by_title
from src.utils.logger import logger
from src.utils.overlay import OnScreenOverlay
from src.bot.healer import AutoHealer
from src.bot.combat import AutoAttacker

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def check_and_prepare_windows(window_cfg: WindowConfig):
    """Verifica as janelas do Tibia e OBS utilizando as regras configuradas."""
    logger.log("SYSTEM", "Verificando janelas abertas...")
    
    tibia_windows = find_windows_by_title(window_cfg.tibia_title, allow_partial=window_cfg.allow_partial_match)
    tibia = [w for w in tibia_windows if w[1].startswith("Tibia - ")]
    if not tibia:
        tibia = tibia_windows

    obs_windows = find_windows_by_title(window_cfg.obs_title, allow_partial=window_cfg.allow_partial_match)
    if not obs_windows:
        obs_windows = find_windows_by_title("obs") or find_windows_by_title("projetor") or find_windows_by_title("projector")

    if not tibia:
        logger.log("SYSTEM", f"Janela do Tibia (busca: '{window_cfg.tibia_title}') nao encontrada!", level="ERROR")
        return None, None
    if not obs_windows:
        logger.log("SYSTEM", f"Janela do OBS Studio / Projetor (busca: '{window_cfg.obs_title}') nao encontrada!", level="ERROR")
        return None, None

    hwnd_tibia, title_tibia = tibia[0]
    hwnd_obs, title_obs = obs_windows[0]

    logger.log("SYSTEM", f"Tibia encontrado: '{title_tibia}' (HWND: {hwnd_tibia})")
    logger.log("SYSTEM", f"OBS encontrado: '{title_obs}' (HWND: {hwnd_obs})")
    return hwnd_tibia, hwnd_obs


def parse_args():
    parser = argparse.ArgumentParser(description="Tibia Bot — Engine Principal")
    parser.add_argument(
        "-c", "--config",
        type=str,
        default=None,
        help="Caminho para o arquivo YAML de configuração (padrão: config/default.yaml)"
    )
    parser.add_argument(
        "-p", "--profile",
        type=str,
        default=None,
        help="Nome ou caminho do perfil de sobreposição em config/profiles/ (ex: character-example ou 1920x1080)"
    )
    return parser.parse_args()


def run():
    """Composition Root: carrega configurações, monta dependências e inicia o BotEngine."""
    args = parse_args()

    print("==================================================")
    print("           Tibia Bot - Engine Principal           ")
    print("==================================================")

    try:
        config: AppConfig = load_config(config_path=args.config, profile_path=args.profile)
        logger.log("SYSTEM", "Configuracao carregada e validada com sucesso.")
    except ConfigValidationError as err:
        logger.log("SYSTEM", f"ERRO DE CONFIGURACAO: {err}", level="ERROR")
        print(f"\n[ERRO CRITICO DE CONFIGURACAO]: {err}\n")
        sys.exit(1)

    hwnd_tibia, hwnd_obs = check_and_prepare_windows(config.window)
    
    if not hwnd_tibia or not hwnd_obs:
        logger.log("SYSTEM", "Por favor, certifique-se de que o Tibia e o OBS estao abertos antes de iniciar.", level="WARNING")
        return

    # Composição de Dependências
    capturer = ProjectorFrameCapturer()
    analyzer = GameAnalyzer(config)
    state_machine = StateMachine(initial_mode=BotMode.IDLE)
    healer = AutoHealer(config.healer)
    combat = AutoAttacker(config.combat)
    overlay = OnScreenOverlay()
    scheduler = LoopScheduler(target_interval_ms=config.loop_interval_ms)

    # Injeção e Execução do BotEngine
    engine = BotEngine(
        config=config,
        capturer=capturer,
        analyzer=analyzer,
        state_machine=state_machine,
        healer=healer,
        combat=combat,
        overlay=overlay,
        scheduler=scheduler,
        hwnd_tibia=hwnd_tibia,
        hwnd_obs=hwnd_obs
    )
    engine.run()


if __name__ == "__main__":
    run()
