import argparse
import os
import sys
import time

# Garante importações a partir do diretório raiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import keyboard
except ImportError:
    keyboard = None

from src.config import load_config, ConfigValidationError, AppConfig, WindowConfig
from src.infrastructure.capture import ProjectorFrameCapturer, CapturedFrame
from src.domain.analyzer import GameAnalyzer
from src.domain.game_state import GameState
from src.utils.window import (
    find_windows_by_title,
    set_window_opacity,
    reset_window_opacity,
    is_window_minimized,
    is_window_active
)
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

killswitch_paused = False


def toggle_killswitch(e=None):
    """Callback acionado ao pressionar a tecla de emergência (Pause)."""
    global killswitch_paused
    killswitch_paused = not killswitch_paused
    if killswitch_paused:
        logger.log("SYSTEM", "🛑 KILLSWITCH ACIONADO: Bot PAUSADO (tecla PAUSE).", level="WARNING")
    else:
        logger.log("SYSTEM", "▶️ KILLSWITCH DESATIVADO: Bot RETOMADO.", level="INFO")


def check_and_prepare_windows(window_cfg: WindowConfig):
    """Verifica e prepara as janelas do Tibia e OBS utilizando a configuração."""
    logger.log("SYSTEM", "Verificando janelas abertas...")
    
    tibia_windows = find_windows_by_title(window_cfg.tibia_title, allow_partial=window_cfg.allow_partial_match)
    tibia = [w for w in tibia_windows if w[1].startswith("Tibia - ")]
    if not tibia:
        tibia = tibia_windows

    obs_windows = find_windows_by_title(window_cfg.obs_title, allow_partial=window_cfg.allow_partial_match)
    if not obs_windows:
        # Fallback para variações comuns se busca específica falhar
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

    # Registra o Killswitch de emergência na tecla Pause
    if keyboard is not None:
        try:
            keyboard.on_press_key('pause', toggle_killswitch)
            logger.log("SYSTEM", "Killswitch registrado na tecla PAUSE.")
        except Exception as err:
            logger.log("SYSTEM", f"Aviso ao registrar hotkey global: {err}", level="WARNING")

    # Ajusta opacidade da janela do Tibia
    logger.log("SYSTEM", "Aplicando opacidade para ocultar a janela do Tibia...")
    set_window_opacity(hwnd_tibia, 1)
    logger.log("SYSTEM", "Janela do Tibia configurada como INVISIVEL.")

    capturer = ProjectorFrameCapturer()
    analyzer = GameAnalyzer(config)
    healer = AutoHealer(config.healer)
    combat = AutoAttacker(config.combat)
    overlay = OnScreenOverlay()

    try:
        logger.log("SYSTEM", "Iniciando modulos do bot e Overlay de tela...")
        overlay.start()
        healer.start()
        combat.start()

        logger.log("SYSTEM", "Aguardando foco na janela do Tibia para iniciar...")
        
        last_pz_state = None
        was_inactive = False
        sleep_sec = config.loop_interval_ms / 1000.0

        while True:
            # 0A. Verifica se o Killswitch de emergência está pausado
            if killswitch_paused:
                time.sleep(0.2)
                continue

            start_cycle = time.perf_counter()

            # 1. Captura única do frame por ciclo
            frame: CapturedFrame = capturer.capture(hwnd_obs)
            
            # 2. Converte percepção em snapshot imutável do Estado Central do Jogo (GameState)
            game_state: GameState = analyzer.analyze(frame, hwnd_tibia, hwnd_obs, config)

            # 3. Trava de Foco e Inatividade
            if not game_state.window.tibia_focused or game_state.window.tibia_minimized:
                if not was_inactive:
                    logger.log("SYSTEM", "Tibia sem foco/fora de selecao. Bot pausado...", level="WARNING")
                    was_inactive = True
                overlay.update(game_state)
                time.sleep(0.2)
                continue

            if was_inactive:
                logger.log("SYSTEM", "Tibia selecionado! Bot em execucao.", level="INFO")
                was_inactive = False

            # 4. Log de evento ao entrar ou sair de Protection Zone (PZ)
            in_pz = game_state.player.in_protection_zone
            if last_pz_state is not None and in_pz is not None and in_pz != last_pz_state:
                if in_pz:
                    logger.log("PZ", "Entrou em PZ", level="ACTION")
                else:
                    logger.log("PZ", "Saiu de PZ", level="ACTION")
            if in_pz is not None:
                last_pz_state = in_pz

            # 5. Atualiza HUD Overlay com o GameState imutável
            overlay.update(game_state)

            # 6. Executa módulos consumidores de estado somente se for seguro atuar
            if game_state.is_safe_to_act:
                healer.check_and_heal(game_state)
                combat.update(game_state)

            # 7. Mantém frequência de loop consistente
            elapsed_sec = time.perf_counter() - start_cycle
            remaining_sleep = max(0.0, sleep_sec - elapsed_sec)
            time.sleep(remaining_sleep)

    except KeyboardInterrupt:
        logger.log("SYSTEM", "Encerrando bot por solicitacao do usuario...")
    finally:
        logger.log("SYSTEM", "Restaurando visibilidade normal da janela do Tibia...")
        if keyboard is not None:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
        overlay.stop()
        reset_window_opacity(hwnd_tibia)
        capturer.close()
        logger.log("SYSTEM", "Visibilidade restaurada. Encerrado com sucesso.")


if __name__ == "__main__":
    run()
