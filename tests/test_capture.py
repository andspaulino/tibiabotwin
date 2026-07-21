import sys
import time
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mss
from PIL import Image

def main():
    print("========================================")
    print("   Teste de Captura de Tela do Tibia   ")
    print("========================================")
    print("Esse script vai tirar um print da sua tela em 5 segundos.")
    print("Abra o seu cliente do Tibia e deixe ele visível na tela!")
    
    for i in range(5, 0, -1):
        print(f"Capturando em {i}...")
        time.sleep(1)
        
    print("\nCapturando tela...")
    
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            output_file = "screenshot.png"
            img.save(output_file)
            
            abs_path = os.path.abspath(output_file)
            print("========================================")
            print(f"Sucesso! Print salvo em:\n{abs_path}")
            print("========================================")
            print("\nINSTRUÇÕES:")
            print("1. Abra a imagem 'screenshot.png' gerada na pasta do projeto.")
            print("2. Verifique se a janela do Tibia está perfeitamente visível na imagem.")
            print("   - Se ela estiver visível, o Python consegue ver o jogo DIRETAMENTE!")
            print("   - Se o Tibia aparecer PRETO ou BRANCO, o jogo está bloqueando capturas comuns e necessita do OBS.")
            
    except Exception as e:
        print(f"Ocorreu um erro durante a captura de tela: {e}")

if __name__ == "__main__":
    main()
