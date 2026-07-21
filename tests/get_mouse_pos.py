import time
import ctypes
from ctypes import wintypes

GetCursorPos = ctypes.windll.user32.GetCursorPos

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def main():
    print("==================================================")
    print("   Inspetor de Posicao do Cursor em Tempo Real    ")
    print("==================================================")
    print("Mova o mouse sobre a tela para ver as coordenadas (X, Y).")
    print("Pressione Ctrl+C para encerrar.\n")

    pt = POINT()
    try:
        while True:
            GetCursorPos(ctypes.byref(pt))
            print(f"Posicao do Cursor -> X: {pt.x:4d} | Y: {pt.y:4d}", end="\r")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n\nEncerrado.")

if __name__ == "__main__":
    main()
