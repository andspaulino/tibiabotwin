import os
import sys
import time
import argparse
import yaml
from pathlib import Path

# Garante importações a partir da raiz do projeto
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

try:
    import cv2
except ImportError:
    cv2 = None

from src.utils.screen import ScreenCapturer, pil_to_cv2
from src.config.models import WindowConfig
from src.infrastructure.factory import create_window_manager


def enable_dpi_awareness() -> None:
    """
    Evita que o Windows virtualize dimensões e coordenadas
    quando a escala da tela está em 125%, 150%, 200%, etc.
    """
    if sys.platform != "win32":
        return

    import ctypes

    try:
        # Per-Monitor DPI Aware V2
        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(-4)
        )
        return
    except Exception:
        pass

    try:
        # Windows 8.1+
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        # Fallback para versões antigas
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def get_client_size(hwnd: int) -> tuple[int, int]:
    """
    Retorna a largura e altura da área cliente da janela.
    """
    if sys.platform != "win32":
        raise RuntimeError(
            "get_client_size atualmente suporta apenas Windows."
        )

    import ctypes
    from ctypes import wintypes

    rect = wintypes.RECT()

    success = ctypes.windll.user32.GetClientRect(
        hwnd,
        ctypes.byref(rect),
    )

    if not success:
        raise ctypes.WinError()

    width = rect.right - rect.left
    height = rect.bottom - rect.top

    return width, height


def maximize_and_wait(
    hwnd: int,
    timeout: float = 5.0,
) -> tuple[int, int]:
    """
    Maximiza a janela e aguarda a área cliente estabilizar
    antes de realizar a captura.
    """
    if sys.platform != "win32":
        return 0, 0

    import ctypes

    user32 = ctypes.windll.user32

    SW_MAXIMIZE = 3
    SW_RESTORE = 9

    # Restaura primeiro caso a janela esteja minimizada.
    user32.ShowWindow(hwnd, SW_RESTORE)

    time.sleep(0.2)

    # Maximiza a janela do Projetor.
    user32.ShowWindow(hwnd, SW_MAXIMIZE)

    # Tenta trazê-la para frente.
    user32.SetForegroundWindow(hwnd)

    deadline = time.monotonic() + timeout

    previous_size: tuple[int, int] | None = None
    stable_checks = 0

    while time.monotonic() < deadline:
        try:
            current_size = get_client_size(hwnd)
        except Exception:
            time.sleep(0.1)
            continue

        width, height = current_size

        if width <= 0 or height <= 0:
            stable_checks = 0
            previous_size = current_size
            time.sleep(0.1)
            continue

        if current_size == previous_size:
            stable_checks += 1
        else:
            stable_checks = 0

        if stable_checks >= 4:
            return current_size

        previous_size = current_size
        time.sleep(0.1)

    return get_client_size(hwnd)


def load_image_from_file(image_path: str):
    """
    Carrega uma imagem de amostra pelo OpenCV.
    """
    img_path = Path(image_path)

    if not img_path.exists():
        print(
            f"[ERRO]: Arquivo de imagem não encontrado: "
            f"{img_path}"
        )
        sys.exit(1)

    image = cv2.imread(str(img_path))

    if image is None or image.size == 0:
        print(
            f"[ERRO]: Não foi possível carregar a imagem: "
            f"{img_path}"
        )
        sys.exit(1)

    return image


def capture_obs_projector():
    """
    Localiza, maximiza e captura a área cliente
    da janela do Projetor do OBS.
    """
    print(
        "Buscando janela do Projetor OBS "
        "para captura de frame..."
    )

    window_manager = create_window_manager()

    window_config = WindowConfig(
        tibia_title="Tibia",
        obs_title="obs",
        allow_partial_match=True,
    )

    obs_window = window_manager.find_projector(
        window_config
    )

    if not obs_window:
        print(
            "[ERRO]: Janela do Projetor OBS não encontrada. "
            "Abra a janela do Projetor no OBS."
        )
        sys.exit(1)

    hwnd_obs, obs_title = obs_window

    print(
        f"[OK] Janela encontrada: "
        f"'{obs_title}' "
        f"(HWND: {hwnd_obs})"
    )

    if sys.platform == "win32":
        try:
            client_width, client_height = maximize_and_wait(
                hwnd_obs
            )

            print(
                "[OK] Projetor maximizado. "
                f"Área cliente: "
                f"{client_width}x{client_height}"
            )
        except Exception as exc:
            print(
                "[AVISO]: Não foi possível confirmar "
                f"o tamanho da janela: {exc}"
            )

            # Ainda aguarda um pouco antes da captura.
            time.sleep(1.0)

    capturer = ScreenCapturer()

    try:
        pil_image = capturer.capture_window_client_area(
            hwnd_obs
        )

        image_bgr = pil_to_cv2(pil_image)
    finally:
        capturer.close()

    if image_bgr is None or image_bgr.size == 0:
        print(
            "[ERRO]: Frame capturado vazio ou inválido."
        )
        sys.exit(1)

    frame_height, frame_width = image_bgr.shape[:2]

    print(
        "[DEBUG] Resolução real do frame capturado: "
        f"{frame_width}x{frame_height}"
    )

    return image_bgr


def calibrate_regions(
    image_bgr,
    regions: list[str],
) -> dict[str, dict[str, float]]:
    """
    Abre o seletor interativo do OpenCV para cada ROI
    e retorna as coordenadas relativas.
    """
    frame_height, frame_width = image_bgr.shape[:2]

    calibrated_rois: dict[
        str,
        dict[str, float],
    ] = {}

    for region in regions:
        print()
        print(
            "-> Selecione a região da barra/área: "
            f"[{region.upper()}]"
        )
        print(
            "   Arraste o mouse para desenhar a caixa."
        )
        print(
            "   Pressione ENTER ou ESPAÇO para confirmar."
        )
        print(
            "   Pressione C ou ESC para cancelar."
        )

        window_title = (
            f"Calibrar ROI: {region} "
            "(ENTER para confirmar)"
        )

        cv2.namedWindow(
            window_title,
            cv2.WINDOW_NORMAL,
        )

        # Ajusta somente a janela de visualização.
        # A imagem original não é redimensionada.
        cv2.resizeWindow(
            window_title,
            min(frame_width, 1600),
            min(frame_height, 900),
        )

        rect = cv2.selectROI(
            window_title,
            image_bgr,
            showCrosshair=True,
            fromCenter=False,
        )

        cv2.destroyWindow(window_title)

        left, top, width, height = rect

        if width == 0 or height == 0:
            print(
                f"[AVISO]: Região '{region}' pulada "
                "porque possui dimensão zero."
            )
            continue

        relative_x = round(
            left / frame_width,
            6,
        )

        relative_y = round(
            top / frame_height,
            6,
        )

        relative_width = round(
            width / frame_width,
            6,
        )

        relative_height = round(
            height / frame_height,
            6,
        )

        calibrated_rois[region] = {
            "x": relative_x,
            "y": relative_y,
            "width": relative_width,
            "height": relative_height,
        }

        print(
            f"[OK] {region}: "
            f"x={relative_x}, "
            f"y={relative_y}, "
            f"width={relative_width}, "
            f"height={relative_height}"
        )

        print(
            "     Pixels: "
            f"left={left}, "
            f"top={top}, "
            f"width={width}, "
            f"height={height}"
        )

    return calibrated_rois


def save_profile(
    profile_name: str,
    calibrated_rois: dict[str, dict[str, float]],
) -> Path:
    """
    Salva as ROIs dentro de config/profiles/<perfil>.yaml.
    Preserva outras configurações já existentes no perfil.
    """
    project_root = Path(__file__).resolve().parent.parent

    profile_path = (
        project_root
        / "config"
        / "profiles"
        / f"{profile_name}.yaml"
    )

    profile_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_data = {}

    if profile_path.exists():
        try:
            with profile_path.open(
                "r",
                encoding="utf-8",
            ) as profile_file:
                existing_data = (
                    yaml.safe_load(profile_file) or {}
                )
        except yaml.YAMLError as exc:
            print(
                "[ERRO]: O perfil existente possui "
                f"YAML inválido: {exc}"
            )
            sys.exit(1)
        except OSError as exc:
            print(
                "[ERRO]: Não foi possível ler "
                f"o perfil existente: {exc}"
            )
            sys.exit(1)

    existing_data["regions"] = calibrated_rois

    try:
        with profile_path.open(
            "w",
            encoding="utf-8",
        ) as profile_file:
            yaml.safe_dump(
                existing_data,
                profile_file,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
    except OSError as exc:
        print(
            "[ERRO]: Não foi possível salvar "
            f"o perfil: {exc}"
        )
        sys.exit(1)

    return profile_path


def main() -> None:
    enable_dpi_awareness()

    if cv2 is None:
        print(
            "[ERRO]: OpenCV (cv2) é necessário "
            "para a ferramenta de calibração."
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description=(
            "Ferramenta Interativa "
            "de Calibração de ROIs"
        )
    )

    parser.add_argument(
        "--image",
        "-i",
        type=str,
        default=None,
        help=(
            "Caminho para uma imagem "
            "de amostra opcional"
        ),
    )

    parser.add_argument(
        "--save-profile",
        "-s",
        type=str,
        default=None,
        help=(
            "Nome do perfil em config/profiles/ "
            "onde as ROIs serão salvas"
        ),
    )

    args = parser.parse_args()

    if args.image:
        image_bgr = load_image_from_file(
            args.image
        )
    else:
        image_bgr = capture_obs_projector()

    if image_bgr is None or image_bgr.size == 0:
        print(
            "[ERRO]: Imagem inválida "
            "ou frame capturado vazio."
        )
        sys.exit(1)

    frame_height, frame_width = image_bgr.shape[:2]

    print()
    print(
        "=================================================="
    )
    print(
        "        Calibração de ROIs Relativas"
    )
    print(
        f" Dimensão do Frame: "
        f"{frame_width} x {frame_height} pixels"
    )
    print(
        "=================================================="
    )
    print()

    regions_to_calibrate = [
        "hp",
        "mana",
        "status_bar",
        "battle_list",
    ]

    calibrated_rois = calibrate_regions(
        image_bgr,
        regions_to_calibrate,
    )

    print()
    print(
        "=================================================="
    )
    print(
        "      Resultado das ROIs Calibradas em YAML"
    )
    print(
        "=================================================="
    )

    yaml_output = yaml.safe_dump(
        {
            "regions": calibrated_rois,
        },
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    print(yaml_output)

    if args.save_profile:
        profile_path = save_profile(
            args.save_profile,
            calibrated_rois,
        )

        print(
            "[OK] Calibração salva com sucesso "
            f"no perfil: {profile_path.resolve()}"
        )


if __name__ == "__main__":
    main()
