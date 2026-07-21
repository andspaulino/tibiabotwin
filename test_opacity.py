import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.window import find_windows_by_title, set_window_opacity, reset_window_opacity

def main():
    print("==================================================")
    print("      Teste de Opacidade da Janela do Tibia       ")
    print("==================================================")
    print("Procurando janelas de jogo do Tibia...")

    # Busca janelas
    all_windows = find_windows_by_title("Tibia")

    # Prioriza janelas do cliente do Tibia (que costumam começar com 'Tibia - ')
    tibia_windows = [w for w in all_windows if w[1].startswith("Tibia - ")]
    
    if not tibia_windows:
        tibia_windows = all_windows

    if not tibia_windows:
        print("\n❌ Nenhuma janela do Tibia foi encontrada.")
        print("Certifique-se de que o seu cliente do Tibia está aberto!")
        return

    print("\nJanelas encontradas:")
    for idx, (hwnd, title) in enumerate(tibia_windows):
        print(f"[{idx}] HWND: {hwnd} | Título: '{title}'")

    if len(tibia_windows) > 1:
        choice = int(input("\nDigite o número da janela desejada: "))
        hwnd, title = tibia_windows[choice]
    else:
        hwnd, title = tibia_windows[0]

    print(f"\nJanela selecionada: '{title}' (HWND: {hwnd})")

    print("\nOPÇÕES DE OPACIDADE:")
    print("1. Deixar quase invisível (Opacidade = 1)")
    print("2. Deixar translúcido (Opacidade = 100)")
    print("3. Restaurar visibilidade normal (Opacidade = 255)")
    print("4. Teste temporário (Invisível por 10s e restaura automaticamente)")

    op = input("\nEscolha uma opção: ").strip()

    if op in ['1', 'invisivel']:
        set_window_opacity(hwnd, 1)
        print("Opacidade definida para 1 (quase invisível). O OBS continua capturando!")
    elif op == '2':
        set_window_opacity(hwnd, 100)
        print("Opacidade definida para 100 (translúcido).")
    elif op in ['3', '255', 'reset', 'normal']:
        reset_window_opacity(hwnd)
        print("Opacidade restaurada para 255 (normal) e estilo de janela resetado!")
    elif op == '4':
        print("\nDeixando a janela invisível por 10 segundos...")
        set_window_opacity(hwnd, 1)
        print("Janela invisível! Observe o OBS Studio...")
        
        for i in range(10, 0, -1):
            print(f"Restaurando em {i}s...", end="\r")
            time.sleep(1)
            
        reset_window_opacity(hwnd)
        print("\nJanela restaurada com sucesso para o estado original!")
    else:
        print("Opção inválida.")

if __name__ == "__main__":
    main()
