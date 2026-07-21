import os
import sys

# Garante a resolução correta dos módulos do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import run

if __name__ == "__main__":
    run()
