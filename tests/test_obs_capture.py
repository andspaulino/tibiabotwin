import sys
import time
import os
import ctypes
from ctypes import wintypes

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mss
from PIL import Image

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
GetWindowTextW = ctypes.windll.user32.GetWindowTextW
GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible
GetClientRect = ctypes.windll.user32.GetClientRect
ClientToScreen = ctypes.windll.user32.ClientToScreen

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_window_title(hwnd):
    length = GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    GetWindowTextW(hwnd, buff, length + 1)
    return buff.value

def find_projector_windows():
    windows = []
    def enum_handler(hwnd, lparam):
        if IsWindowVisible(hwnd):
            title = get_window_title(hwnd)
            if "projector" in title.lower() or "projetor" in title.lower() or "obs" in title.lower():
                windows.append((hwnd, title))
        return True
    
    EnumWindows(EnumWindowsProc(enum_handler), 0)
    return windows

def main():
    print("==================================================")
    print("   Teste de Captura Otimizada (Client Area) OBS   ")
    print("==================================================")

    projectors = find_projector_windows()

    if not projectors:
        print("\n❌ Nenhuma janela de 'OBS' ou 'Projetor' foi encontrada!")
        print("Certifique-se de que a janela do OBS/Projetor está aberta.")
        return

    if len(projectors) > 1:
        for idx, (hwnd, title) in enumerate(projectors):
            print(f"[{idx}] HWND: {hwnd} | Título: '{title}'")
        choice = int(input("\nDigite o número da janela desejada: "))
        hwnd, title = projectors[choice]
    else:
        hwnd, title = projectors[0]
        print(f"\nProjetor encontrado: '{title}'")

    print("\nTirando print ajustado em 2 segundos...")
    time.sleep(2)

    try:
        client_rect = wintypes.RECT()
        GetClientRect(hwnd, ctypes.byref(client_rect))
        
        width = client_rect.right - client_rect.left
        height = client_rect.bottom - client_rect.top

        pt = POINT(0, 0)
        ClientToScreen(hwnd, ctypes.byref(pt))
        left, top = pt.x, pt.y

        print(f"Área útil da janela: Left={left}, Top={top}, Width={width}, Height={height}")

        with mss.mss() as sct:
            monitor = {"top": top, "left": left, "width": width, "height": height}
            screenshot = sct.grab(monitor)
            
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            output_file = "screenshot_obs_clean.png"
            img.save(output_file)
            
            abs_path = os.path.abspath(output_file)
            print("==================================================")
            print(f"🎉 Captura limpa salva em: {abs_path}")
            print("==================================================")

    except Exception as e:
        print(f"❌ Ocorreu um erro ao capturar a janela: {e}")

if __name__ == "__main__":
    main()
