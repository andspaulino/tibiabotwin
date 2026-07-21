import os
import sys

try:
    import cv2
except ImportError:
    print("OpenCV e necessario para este utilitario. Instale com: pip install opencv-python")
    sys.exit(1)

def main():
    image_path = "screenshot_obs_clean.png"
    
    if not os.path.exists(image_path):
        print(f"[X] Imagem '{image_path}' nao encontrada na pasta raiz do projeto.")
        print("Execute primeiro: python tests/test_obs_capture.py")
        return

    print("==================================================")
    print("      Seletor de Regiao de Interesse (ROI)        ")
    print("==================================================")
    print(f"Carregando '{image_path}'...")
    print("\nINSTRUCOES:")
    print("1. Clique e arraste o mouse com o botao esquerdo para selecionar uma regiao (ex: Barra de HP/MP).")
    print("2. Pressione ENTER ou ESPACO para confirmar a selecao.")
    print("3. Pressione 'c' ou ESC para cancelar.")
    print("==================================================\n")

    img = cv2.imread(image_path)
    if img is None:
        print("[X] Erro ao carregar a imagem.")
        return

    # Janela interativa para desenhar retangulo de selecao
    roi = cv2.selectROI("Selecione a Regiao (ENTER para confirmar)", img, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()

    x, y, w, h = roi

    if w > 0 and h > 0:
        print("==================================================")
        print("🎉 Coordenadas capturadas com sucesso!")
        print("==================================================")
        print(f"X (Esquerda)  : {x}")
        print(f"Y (Topo)      : {y}")
        print(f"Largura (W)   : {w}")
        print(f"Altura (H)    : {h}")
        print("--------------------------------------------------")
        print(f"Dicionario para Python: {{'top': {y}, 'left': {x}, 'width': {w}, 'height': {h}}}")
        print("==================================================")
    else:
        print("Nenhuma regiao foi selecionada.")

if __name__ == "__main__":
    main()
