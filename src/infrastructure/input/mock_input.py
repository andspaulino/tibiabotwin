from typing import List, Tuple
from src.infrastructure.input.base import InputController


class MockInputController(InputController):
    """
    Controlador de input Falso (Mock) para testes unitários e ambientes sem hardware.
    Armazena histórico de teclas e cliques sem acionar o sistema operacional.
    """

    def __init__(self):
        self.key_history: List[str] = []
        self.click_history: List[Tuple[int, int, str]] = []
        self.released_all: bool = False

    def press_key(self, key: str) -> None:
        self.key_history.append(key)

    def click(
        self,
        x: int,
        y: int,
        button: str = "left",
        return_position: tuple[int, int] | None = None,
    ) -> None:
        del return_position
        self.click_history.append((x, y, button))

    def release_all(self) -> None:
        self.released_all = True
