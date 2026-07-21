import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    logger.log("SYSTEM", "Módulo de teste do HUD iniciado.")
    time.sleep(1)
    logger.log("HEALER", "[+] Vida em 88.5% (<= 90%). Usando Magia de Cura (HK 1).", level="ACTION")
    time.sleep(1)
    logger.log("COMBAT", "⚔️ Inimigo detectado na Battle List. Atacando (HK 'SPACE')...", level="ACTION")
    time.sleep(1)
    logger.log("PZ", "O personagem ENTROU em Protection Zone (PZ).", level="ACTION")
    time.sleep(1)
    logger.log("HEALER", "[*] Mana em 45.0% (<= 50%). Usando Pocao de Mana (HK 2).", level="ACTION")
    time.sleep(2)

    print("\nEncerrando teste do Overlay...")
    overlay.stop()
    print("==================================================")
    print("[OK] Teste concluído com sucesso!")
    print("==================================================")

if __name__ == "__main__":
    main()
