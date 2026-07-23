from typing import Protocol


class InputController(Protocol):
    """Interface abstrata para envio de comandos de entrada (teclado e mouse)."""

    def press_key(self, key: str) -> None:
        """Pressiona e solta uma tecla com humanização."""
        ...

    def click(
        self,
        x: int,
        y: int,
        button: str = "left",
        return_position: tuple[int, int] | None = None,
    ) -> None:
        """Executa um clique e pode estacionar o cursor em uma posição segura."""
        ...

    def release_all(self) -> None:
        """Garante a liberação de todas as teclas e botões em situação de pânico."""
        ...
