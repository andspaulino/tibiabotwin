import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import keyboard
except ImportError:
    keyboard = None

from src.utils.logger import logger

killswitch_paused = False

def toggle_killswitch(e=None):
    global killswitch_paused
    killswitch_paused = not killswitch_paused
    if killswitch_paused:
        logger.log("SYSTEM", "🛑 KILLSWITCH ACIONADO: Bot PAUSADO (tecla PAUSE).", level="WARNING")
    else:
        logger.log("SYSTEM", "▶️ KILLSWITCH DESATIVADO: Bot RETOMADO.", level="INFO")

def main():
    print("==================================================")
    print("      Teste do Killswitch de Emergência (PAUSE)   ")
    print("==================================================")

    if keyboard is None:
        print("[X] Pacote 'keyboard' nao instalado.")
        return

    try:
        keyboard.on_press_key('pause', toggle_killswitch)
        print("[OK] Pressione a tecla 'PAUSE' no teclado para alternar o estado do Killswitch.")
        print("Pressione Ctrl+C para encerrar o teste.\n")

        counter = 0
        while counter < 10:
            if killswitch_paused:
                print("  [Pausado pelo Killswitch - Acoes bloqueadas]", end="\r")
                time.sleep(0.3)
                continue
            
            counter += 1
            print(f"  - Executando acao {counter}/10...                      ", end="\r")
            time.sleep(1)

        print("\n==================================================")
        print("[OK] Teste do Killswitch concluido com sucesso!")
        print("==================================================")

    except KeyboardInterrupt:
        print("\n\nTeste encerrado pelo usuario.")
    finally:
        keyboard.unhook_all()

if __name__ == "__main__":
    main()
