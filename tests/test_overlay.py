import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.utils.logger import logger
from src.utils.overlay import OnScreenOverlay

def main():
    print("==================================================")
    print("       Teste de Overlay Transparente (HUD)        ")
    print("==================================================")

    overlay = OnScreenOverlay()
    print("Iniciando janela de Overlay...")
    overlay.start()

    time.sleep(1)
    logger.log("SYSTEM", "Modulo de teste do HUD iniciado.")
    time.sleep(1)
    logger.log("HEALER", "[+] Magia de Cura (85%)", level="ACTION")
    time.sleep(1)
    logger.log("COMBAT", "Atacando inimigo", level="ACTION")
    time.sleep(1)
    logger.log("PZ", "Entrou em PZ", level="ACTION")
    time.sleep(1)
    logger.log("HEALER", "[*] Pocao de Mana (45%)", level="ACTION")
    time.sleep(2)

    print("\nEncerrando teste do Overlay...")
    overlay.stop()
    print("==================================================")
    print("[OK] Teste concluido com sucesso!")
    print("==================================================")

if __name__ == "__main__":
    main()
