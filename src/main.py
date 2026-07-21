import os
import sys
import time

# Garante importações a partir do diretório raiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.window import (
    find_windows_by_title,
    set_window_opacity,
    reset_window_opacity
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

def check_and_prepare_windows():
    """Verifica e prepara as janelas do Tibia e OBS."""
    logger.log("SYSTEM", "Verificando janelas abertas...")
    
    tibia_windows = find_windows_by_title("Tibia")
    tibia = [w for w in tibia_windows if w[1].startswith("Tibia - ")]
    if not tibia:
        tibia = tibia_windows

    obs_windows = find_windows_by_title("obs") or find_windows_by_title("projetor") or find_windows_by_title("projector")

    if not tibia:
        logger.log("SYSTEM", "Janela do Tibia nao encontrada!", level="ERROR")
        return None, None
    if not obs_windows:
        logger.log("SYSTEM", "Janela do OBS Studio / Projetor nao encontrada!", level="ERROR")
        return None, None

    hwnd_tibia, title_tibia = tibia[0]
    hwnd_obs, title_obs = obs_windows[0]

    logger.log("SYSTEM", f"Tibia encontrado: '{title_tibia}' (HWND: {hwnd_tibia})")
    logger.log("SYSTEM", f"OBS encontrado: '{title_obs}' (HWND: {hwnd_obs})")
    return hwnd_tibia, hwnd_obs

def run():
    print("==================================================")
    print("           Tibia Bot - Engine Principal           ")
    print("==================================================")

    hwnd_tibia, hwnd_obs = check_and_prepare_windows()
    
    if not hwnd_tibia or not hwnd_obs:
        logger.log("SYSTEM", "Por favor, certifique-se de que o Tibia e o OBS estao abertos antes de iniciar.", level="WARNING")
        return

    # Ajusta opacidade da janela do Tibia
    logger.log("SYSTEM", "Aplicando opacidade para ocultar a janela do Tibia...")
    set_window_opacity(hwnd_tibia, 1)
    logger.log("SYSTEM", "Janela do Tibia configurada como INVISIVEL.")

    capturer = ScreenCapturer()
    healer = AutoHealer()
    combat = AutoAttacker()
    overlay = OnScreenOverlay()

    try:
        logger.log("SYSTEM", "Iniciando modulos do bot e Overlay de tela...")
        overlay.start()
        healer.start()
        combat.start()

        logger.log("SYSTEM", "Bot Ativo - Registrando Acoes em Tempo Real.")
        
        last_pz_state = None

        while True:
            # 1. Captura a imagem da janela do Projetor OBS
            pil_img = capturer.capture_window_client_area(hwnd_obs)
            
            # 2. Converte para array OpenCV BGR
            img_bgr = pil_to_cv2(pil_img)
            
            # 3. Leitura contínua das barras e estado de PZ
            hp_pct = get_hp_percentage(img_bgr)
            mp_pct = get_mp_percentage(img_bgr)
            in_pz = is_in_pz(img_bgr)

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

            time.sleep(0.05)

    except KeyboardInterrupt:
        logger.log("SYSTEM", "Encerrando bot por solicitacao do usuario...")
    finally:
        logger.log("SYSTEM", "Restaurando visibilidade normal da janela do Tibia...")
        overlay.stop()
        reset_window_opacity(hwnd_tibia)
        capturer.close()
        logger.log("SYSTEM", "Visibilidade restaurada. Encerrado com sucesso.")

if __name__ == "__main__":
    run()
