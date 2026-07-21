import os
import sys
import time

# Adiciona o diretório raiz do projeto ao path do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.window import (
    find_windows_by_title,
    set_window_opacity,
    reset_window_opacity
)

def find_tibia_window():
    """Busca a janela do cliente do Tibia."""
    all_windows = find_windows_by_title("Tibia")
    # Prioriza janelas do cliente do Tibia (que costumam começar com 'Tibia - ')
    tibia_windows = [w for w in all_windows if w[1].startswith("Tibia - ")]
    if not tibia_windows:
        tibia_windows = all_windows
    return tibia_windows[0] if tibia_windows else None

def find_obs_window():
    """Busca a janela do OBS Studio ou Projetor do OBS."""
    obs_windows = find_windows_by_title("obs")
    if not obs_windows:
        obs_windows = find_windows_by_title("projetor")
    if not obs_windows:
        obs_windows = find_windows_by_title("projector")
    return obs_windows[0] if obs_windows else None

def main():
    print("==================================================")
    print("      Iniciador Tibia Bot - Ocultador de Janela   ")
    print("==================================================")
    
    while True:
        print("\nVerificando janelas abertas...")
        
        tibia = find_tibia_window()
        obs = find_obs_window()
        
        # Status do Tibia
        if tibia:
            hwnd_tibia, title_tibia = tibia
            print(f"  [✔] Tibia encontrado: '{title_tibia}' (HWND: {hwnd_tibia})")
        else:
            print("  [❌] Tibia NÃO foi encontrado.")
            
        # Status do OBS
        if obs:
            hwnd_obs, title_obs = obs
            print(f"  [✔] OBS encontrado: '{title_obs}' (HWND: {hwnd_obs})")
        else:
            print("  [❌] OBS Studio / Projetor NÃO foi encontrado.")
            
        if tibia and obs:
            print("\n==================================================")
            print("  🎉 Ambas as janelas foram encontradas com sucesso!")
            print("==================================================")
            break
        else:
            print("\n⚠️ Não foi possível prosseguir pois faltam janelas abertas.")
            print("[1] Tentar novamente")
            print("[2] Sair")
            op = input("\nEscolha uma opção (padrão=1): ").strip()
            if op == '2':
                print("Saindo...")
                return

    hwnd_tibia, title_tibia = tibia

    try:
        print("\nAplicando opacidade para deixar a janela do Tibia invisível...")
        set_window_opacity(hwnd_tibia, 1)
        print("✅ Opacidade alterada para 1 (Invisível para olhos humanos, capturável pelo OBS)!")
        print("\nO Tibia continuará invisível enquanto este iniciador estiver aberto.")
        print("Pressione ENTER ou envie Ctrl+C para restaurar a visibilidade e encerrar...")
        input()
    except KeyboardInterrupt:
        print("\nInterrupção detectada.")
    finally:
        print("\nRestaurando visibilidade normal da janela do Tibia...")
        reset_window_opacity(hwnd_tibia)
        print("✨ Janela do Tibia restaurada para opacidade normal (255)!")
        print("Programa encerrado.")

if __name__ == "__main__":
    main()
