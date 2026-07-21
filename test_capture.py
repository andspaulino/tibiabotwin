import sys
import subprocess
import time
import os

def install_and_import(import_name, install_name=None):
    if install_name is None:
        install_name = import_name
    try:
        __import__(import_name)
    except ImportError:
        print(f"Instalando a biblioteca '{install_name}' necessária para o teste...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", install_name])

# Instala mss e pillow (PIL) se não estiverem presentes
try:
    install_and_import('mss')
    install_and_import('PIL', 'pillow')
except Exception as e:
    print(f"Erro ao tentar instalar dependências automaticamente: {e}")
    print("Por favor, tente instalar manualmente no terminal:")
    print("pip install mss pillow")
    sys.exit(1)

import mss
from PIL import Image

def main():
    print("========================================")
    print("   Teste de Captura de Tela do Tibia   ")
    print("========================================")
    print("Esse script vai tirar um print da sua tela em 5 segundos.")
    print("Abra o seu cliente do Tibia e deixe ele visível na tela!")
    
    # Contagem regressiva
    for i in range(5, 0, -1):
        print(f"Capturando em {i}...")
        time.sleep(1)
        
    print("\nCapturando tela...")
    
    try:
        with mss.mss() as sct:
            # Captura a tela inteira (monitor principal)
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # Converte para imagem PIL
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Salva no diretório atual
            output_file = "screenshot.png"
            img.save(output_file)
            
            print("========================================")
            # Imprime o caminho absoluto do arquivo
            abs_path = os.path.abspath(output_file)
            print(f"Sucesso! Print salvo em:\n{abs_path}")
            print("========================================")
            print("\nINSTRUÇÕES:")
            print("1. Abra a imagem 'screenshot.png' gerada na pasta do projeto.")
            print("2. Verifique se a janela do Tibia está perfeitamente visível na imagem.")
            print("   - Se ela estiver visível, o Python consegue ver o jogo DIRETAMENTE! Não precisamos do OBS.")
            print("   - Se o Tibia aparecer todo PRETO ou em BRANCO, o jogo está bloqueando capturas comuns, e precisaremos do OBS.")
            
    except Exception as e:
        print(f"Ocorreu um erro durante a captura de tela: {e}")

if __name__ == "__main__":
    main()
