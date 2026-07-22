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
from src.utils.window import (
    find_windows_by_title,
    set_window_opacity,
    reset_window_opacity,
    is_window_minimized,
    is_window_active
)
from src.utils.screen import (
    ScreenCapturer,
    pil_to_cv2,
    get_hp_percentage,
    get_mp_percentage,
    get_status_bar_activity,
    is_in_pz
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

    capturer = ScreenCapturer()
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

            # 0B. Garante que o bot só executa se a janela do Tibia for a JANELA ATIVA (Foco do Windows)
            if not is_window_active(hwnd_tibia):
                if not was_inactive:
                    logger.log("SYSTEM", "Tibia sem foco/fora de selecao. Bot pausado...", level="WARNING")
                    was_inactive = True
                time.sleep(0.2)
                continue

            if was_inactive:
                logger.log("SYSTEM", "Tibia selecionado! Bot em execucao.", level="INFO")
                was_inactive = False

            # 1. Captura a imagem da janela do Projetor OBS
            pil_img = capturer.capture_window_client_area(hwnd_obs)
            
            # 2. Converte para array OpenCV BGR
            img_bgr = pil_to_cv2(pil_img)
            
            # 3. Leitura contínua das barras e estado de PZ
            hp_pct = get_hp_percentage(img_bgr)
            mp_pct = get_mp_percentage(img_bgr)
            in_pz = is_in_pz(
                img_bgr,
                pz_template_path=config.pz.template_path,
                threshold=config.pz.match_threshold
            )

            # 4. Log de evento ao entrar ou sair de Protection Zone (PZ)
            if last_pz_state is not None and in_pz != last_pz_state:
                if in_pz:
                    logger.log("PZ", "Entrou em PZ", level="ACTION")
                else:
                    logger.log("PZ", "Saiu de PZ", level="ACTION")
            last_pz_state = in_pz

            # 5. Executa verificação do Healer (dispara apenas ao realizar ação de cura)
            healer.check_and_heal(hp_pct, mp_pct, in_pz)
            
            # 6. Executa atualização do Combat (dispara apenas ao realizar ação de combate)
            combat.update(img_bgr, in_pz)

            time.sleep(sleep_sec)

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
