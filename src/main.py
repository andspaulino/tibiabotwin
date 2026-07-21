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
    print("\n[Main] Verificando janelas abertas...")
    
    tibia_windows = find_windows_by_title("Tibia")
    tibia = [w for w in tibia_windows if w[1].startswith("Tibia - ")]
    if not tibia:
        tibia = tibia_windows

    obs_windows = find_windows_by_title("obs") or find_windows_by_title("projetor") or find_windows_by_title("projector")

    if not tibia:
        print("[X] Janela do Tibia nao encontrada!")
        return None, None
    if not obs_windows:
        print("[X] Janela do OBS Studio / Projetor nao encontrada!")
        return None, None

    hwnd_tibia, title_tibia = tibia[0]
    hwnd_obs, title_obs = obs_windows[0]

    print(f"[OK] Tibia encontrado: '{title_tibia}' (HWND: {hwnd_tibia})")
    print(f"[OK] OBS encontrado: '{title_obs}' (HWND: {hwnd_obs})")
    return hwnd_tibia, hwnd_obs

def run():
    print("==================================================")
    print("           Tibia Bot - Engine Principal           ")
    print("==================================================")

    hwnd_tibia, hwnd_obs = check_and_prepare_windows()
    
    if not hwnd_tibia or not hwnd_obs:
        print("\n[!] Por favor, certifique-se de que o Tibia e o OBS estao abertos antes de iniciar.")
        return

    # Ajusta opacidade da janela do Tibia
    print("\nAplicando opacidade para ocultar a janela do Tibia...")
    set_window_opacity(hwnd_tibia, 1)
    print("[OK] Janela do Tibia configurada como INVISIVEL.")

    capturer = ScreenCapturer()
    healer = AutoHealer()
    combat = AutoAttacker()

    try:
        print("\nIniciando modulos do bot...")
        healer.start()
        combat.start()

        print("\n[Monitoramento em Tempo Real Iniciado]")
        print("Pressione Ctrl+C no terminal para parar.\n")
        
        last_print = 0
        last_pz_state = None

        while True:
            # 1. Captura a imagem da janela do Projetor OBS
            pil_img = capturer.capture_window_client_area(hwnd_obs)
            
            # 2. Converte para array OpenCV BGR
            img_bgr = pil_to_cv2(pil_img)
            
            # 3. Leitura contínua das barras e estado de PZ
            hp_pct = get_hp_percentage(img_bgr)
            mp_pct = get_mp_percentage(img_bgr)
            status_info = get_status_bar_activity(img_bgr)
            in_pz = is_in_pz(img_bgr)

            # 4. Log de transição de entrada/saída de Protection Zone (PZ)
            if last_pz_state is not None and in_pz != last_pz_state:
                if in_pz:
                    print("\n[PZ Event] O personagem ENTROU em Protection Zone (PZ).")
                else:
                    print("\n[PZ Event] O personagem SAIU de Protection Zone (PZ).")
            last_pz_state = in_pz

            # 5. Exibe status atualizado no terminal a cada 0.2s
            now = time.time()
            if now - last_print >= 0.2:
                status_txt = "Ativo" if status_info["active"] else "Neutro"
                pz_str = "SIM" if in_pz else "NAO"
                print(f"\r[Real-Time] HP: {hp_pct * 100:5.1f}% | MP: {mp_pct * 100:5.1f}% | PZ: {pz_str:3s} | Status: {status_txt:6s}", end="")
                last_print = now

            # 6. Executa verificação do Healer (respeitando PZ)
            healer.check_and_heal(hp_pct, mp_pct, in_pz)
            
            # 7. Executa atualização do Combat
            combat.update()

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\nEncerrando bot por solicitacao do usuario...")
    finally:
        print("Restaurando visibilidade normal da janela do Tibia...")
        reset_window_opacity(hwnd_tibia)
        capturer.close()
        print("[OK] Visibilidade restaurada. Encerrado com sucesso.")

if __name__ == "__main__":
    run()
