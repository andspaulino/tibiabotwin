import os
import sys
import time
import argparse
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

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
from src.domain.roi import RelativeROI, AbsoluteROI, ROIResolver
from src.infrastructure.factory import create_window_manager


def enable_dpi_awareness() -> None:
    """Evita que o Windows virtualize dimensões/coordenadas em escalas >100%."""
    if sys.platform != "win32":
        return

    import ctypes

    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def get_client_size(hwnd: int) -> tuple[int, int]:
    """Retorna largura e altura da área cliente da janela no Windows."""
    if sys.platform != "win32":
        raise RuntimeError("get_client_size suporta apenas Windows.")

    import ctypes
    from ctypes import wintypes

    rect = wintypes.RECT()
    success = ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
    if not success:
        raise ctypes.WinError()

    return rect.right - rect.left, rect.bottom - rect.top


def maximize_and_wait(hwnd: int, timeout: float = 5.0) -> tuple[int, int]:
    """Restaura, maximiza e traz a janela para frente exatamente como a ferramenta de calibração."""
    if sys.platform != "win32":
        return 0, 0

    import ctypes
    user32 = ctypes.windll.user32

    # SW_RESTORE = 9, SW_MAXIMIZE = 3
    user32.ShowWindow(hwnd, 9)
    time.sleep(0.2)
    user32.ShowWindow(hwnd, 3)
    user32.SetForegroundWindow(hwnd)

    deadline = time.monotonic() + timeout
    previous_size = None
    stable_checks = 0

    while time.monotonic() < deadline:
        try:
            current_size = get_client_size(hwnd)
        except Exception:
            time.sleep(0.1)
            continue

        w, h = current_size
        if w <= 0 or h <= 0:
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


def capture_obs_projector() -> cv2.typing.MatLike | None:
    """Busca a janela do Projetor do OBS, ativa, maximiza e retorna o frame único capturado em BGR."""
    print("Buscando janela do Projetor OBS para captura de frame...")

    window_manager = create_window_manager()
    window_config = WindowConfig(tibia_title="Tibia", obs_title="obs", allow_partial_match=True)
    obs_window = window_manager.find_projector(window_config)

    if not obs_window:
        print("[ERRO]: Janela do Projetor OBS não encontrada. Abra a janela do Projetor no OBS.")
        sys.exit(1)

    hwnd_obs, obs_title = obs_window
    print(f"[OK] Janela encontrada: '{obs_title}' (HWND: {hwnd_obs})")

    if sys.platform == "win32":
        try:
            client_width, client_height = maximize_and_wait(hwnd_obs)
            print(f"[OK] Projetor maximizado. Área cliente: {client_width}x{client_height}")
        except Exception as exc:
            print(f"[AVISO]: Não foi possível confirmar o tamanho da janela: {exc}")
            time.sleep(1.0)

    capturer = ScreenCapturer()
    try:
        pil_image = capturer.capture_window_client_area(hwnd_obs)
        image_bgr = pil_to_cv2(pil_image)
    finally:
        capturer.close()

    if image_bgr is None or image_bgr.size == 0:
        print("[ERRO]: Frame capturado vazio ou inválido.")
        sys.exit(1)

    h, w = image_bgr.shape[:2]
    print(f"[DEBUG] Resolução real do frame capturado: {w}x{h}\n")
    return image_bgr


def parse_roi_arg(roi_args: list[str]) -> Optional[Dict[str, float]]:
    """Tenta converter os argumentos passados via CLI --roi para dicionário de ROI."""
    if not roi_args:
        return None

    try:
        # Ex: --roi 0.780729 0.978196 0.034375 0.020813
        if len(roi_args) == 4:
            return {
                "x": float(roi_args[0]),
                "y": float(roi_args[1]),
                "width": float(roi_args[2]),
                "height": float(roi_args[3]),
            }

        # Ex: --roi "0.780729, 0.978196, 0.034375, 0.020813"
        joined = " ".join(roi_args).replace(",", " ")
        parts = [float(p) for p in joined.split() if p]
        if len(parts) == 4:
            return {
                "x": parts[0],
                "y": parts[1],
                "width": parts[2],
                "height": parts[3],
            }
    except Exception:
        pass

    return None


def lookup_config_roi(element_name: str, project_root: Path) -> Optional[Dict[str, float]]:
    """Procura no config/default.yaml se existe alguma ROI mapeada para o nome informado."""
    default_yaml = project_root / "config" / "default.yaml"
    if not default_yaml.exists():
        return None

    try:
        with open(default_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        clean_name = element_name.lower().strip()

        # 1. Procura na seção `regions` (ex: hp, mana, status_bar, battle_list)
        regions = data.get("regions", {})
        if clean_name in regions and isinstance(regions[clean_name], dict):
            return regions[clean_name]

        # 2. Procura em outras seções do YAML (ex: chat -> button_roi)
        for key, val in data.items():
            if isinstance(val, dict):
                if key.lower() in clean_name or clean_name.startswith(key.lower()):
                    if "button_roi" in val and isinstance(val["button_roi"], dict):
                        return val["button_roi"]
                    if "roi" in val and isinstance(val["roi"], dict):
                        return val["roi"]

    except Exception:
        pass

    return None


def crop_by_roi(image_bgr: cv2.typing.MatLike, element_name: str, roi_dict: Dict[str, float], out_dir: Path) -> dict:
    """Recorta uma sub-imagem diretamente pelas coordenadas de ROI informadas, sem abrir a GUI interativa."""
    frame_height, frame_width = image_bgr.shape[:2]

    abs_roi = ROIResolver.resolve(roi_dict, frame_width, frame_height)
    x, y, w, h = abs_roi.left, abs_roi.top, abs_roi.width, abs_roi.height

    rel_x = round(float(x) / float(frame_width), 6)
    rel_y = round(float(y) / float(frame_height), 6)
    rel_w = round(float(w) / float(frame_width), 6)
    rel_h = round(float(h) / float(frame_height), 6)

    center_x = x + (w // 2)
    center_y = y + (h // 2)

    cropped = image_bgr[y:y + h, x:x + w]
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{element_name.lower().strip().replace(' ', '_')}.png"
    save_path = out_dir / filename
    cv2.imwrite(str(save_path), cropped)

    print(f"\n[OK] Elemento '{element_name}' recortado AUTOMATICAMENTE a partir da ROI configurada/informada:")
    print(f"     -> Path: {save_path.resolve()}")
    print(f"     -> ROI Relativa:  x={rel_x}, y={rel_y}, width={rel_w}, height={rel_h}")
    print(f"     -> Pixels Abs:    left={x}, top={y}, width={w}, height={h}")
    print(f"     -> Centro (X,Y):  ({center_x}, {center_y})\n")

    return {
        "name": element_name,
        "file": str(save_path.relative_to(Path.cwd()) if save_path.is_relative_to(Path.cwd()) else save_path),
        "relative_roi": {"x": rel_x, "y": rel_y, "width": rel_w, "height": rel_h},
        "pixels": {"left": x, "top": y, "width": w, "height": h, "center_x": center_x, "center_y": center_y}
    }


def crop_single_element(image_bgr: cv2.typing.MatLike, element_name: str, out_dir: Path) -> dict | None:
    """Abre a janela de seleção visual proporcional do OpenCV para recortar o elemento manualmente."""
    frame_height, frame_width = image_bgr.shape[:2]
    window_title = f"Capturar Elemento: [{element_name}] — Arraste a caixa e pressione ENTER"

    print(f"-> Selecionando elemento: [{element_name}]")
    print("   Arraste o mouse para desenhar a caixa.")
    print("   Pressione ENTER ou ESPAÇO para confirmar.")
    print("   Pressione C ou ESC para cancelar.")

    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_title, min(frame_width, 1600), min(frame_height, 900))

    rect = cv2.selectROI(window_title, image_bgr, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow(window_title)

    x, y, w, h = rect

    if w <= 0 or h <= 0:
        print(f"[AVISO]: Seleção do elemento '{element_name}' cancelada ou sem dimensão.\n")
        return None

    rel_x = round(float(x) / float(frame_width), 6)
    rel_y = round(float(y) / float(frame_height), 6)
    rel_w = round(float(w) / float(frame_width), 6)
    rel_h = round(float(h) / float(frame_height), 6)

    center_x = x + (w // 2)
    center_y = y + (h // 2)

    # Recorta a sub-imagem e salva em arquivo PNG
    cropped = image_bgr[y:y + h, x:x + w]
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{element_name.lower().strip().replace(' ', '_')}.png"
    save_path = out_dir / filename
    cv2.imwrite(str(save_path), cropped)

    print(f"\n[OK] Elemento '{element_name}' capturado e salvo em:")
    print(f"     -> Path: {save_path.resolve()}")
    print(f"     -> ROI Relativa:  x={rel_x}, y={rel_y}, width={rel_w}, height={rel_h}")
    print(f"     -> Pixels Abs:    left={x}, top={y}, width={w}, height={h}")
    print(f"     -> Centro (X,Y):  ({center_x}, {center_y})\n")

    return {
        "name": element_name,
        "file": str(save_path.relative_to(Path.cwd()) if save_path.is_relative_to(Path.cwd()) else save_path),
        "relative_roi": {
            "x": rel_x,
            "y": rel_y,
            "width": rel_w,
            "height": rel_h,
        },
        "pixels": {
            "left": x,
            "top": y,
            "width": w,
            "height": h,
            "center_x": center_x,
            "center_y": center_y,
        }
    }


def main() -> None:
    enable_dpi_awareness()

    if cv2 is None:
        print("[ERRO]: OpenCV (cv2) é necessário para a ferramenta de captura.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Ferramenta Interativa para Captura de Templates e ROIs Personalizadas"
    )
    parser.add_argument(
        "--image", "-i",
        type=str,
        default=None,
        help="Caminho para uma imagem de amostragem opcional (em vez de capturar o OBS)"
    )
    parser.add_argument(
        "--out-dir", "-o",
        type=str,
        default="tools/cropped_images",
        help="Diretório onde salvar a imagem recortada (padrão: tools/cropped_images/)"
    )
    parser.add_argument(
        "--name", "-n",
        type=str,
        default=None,
        help="Nome do elemento/template (ex: chat_off, hp, mana, battle_list)"
    )
    parser.add_argument(
        "--roi", "-r",
        nargs="+",
        default=None,
        help="Coordenadas da ROI relativa (ex: --roi 0.780729 0.978196 0.034375 0.020813)"
    )

    args = parser.parse_args()
    project_root = Path(__file__).resolve().parent.parent
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = project_root / out_dir

    if args.image:
        img_path = Path(args.image)
        if not img_path.is_absolute():
            img_path = project_root / img_path
        if not img_path.exists():
            print(f"[ERRO]: Arquivo de imagem não encontrado: {img_path}")
            sys.exit(1)
        image_bgr = cv2.imread(str(img_path))
    else:
        image_bgr = capture_obs_projector()

    if image_bgr is None or image_bgr.size == 0:
        print("[ERRO]: Imagem de amostra ou frame capturado é inválido.")
        sys.exit(1)

    frame_h, frame_w = image_bgr.shape[:2]

    print("==================================================")
    print("      Ferramenta de Captura de Elementos/Templates")
    print(f" Resolução do Frame: {frame_w} x {frame_h} pixels")
    print(f" Salvar em: {out_dir.resolve()}")
    print("==================================================\n")

    results = []

    if args.name:
        parsed_roi = parse_roi_arg(args.roi) if args.roi else None
        if parsed_roi:
            res = crop_by_roi(image_bgr, args.name, parsed_roi, out_dir)
        else:
            res = crop_single_element(image_bgr, args.name, out_dir)

        if res:
            results.append(res)
    else:
        while True:
            try:
                name_input = input("Digite o nome do elemento/template para recortar (ou 'q' para sair): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nEncerrando...")
                break

            if not name_input or name_input.lower() in ("q", "quit", "exit", "sair"):
                break

            res = crop_single_element(image_bgr, name_input, out_dir)
            if res:
                results.append(res)

            if res:
                results.append(res)

    if results:
        print("==================================================")
        print("          Resumo dos Elementos Capturados         ")
        print("==================================================")
        for item in results:
            print(f"# Elemento: {item['name']}")
            print(f"# Arquivo:  {item['file']}")
            print(f"roi:")
            print(f"  x: {item['relative_roi']['x']}")
            print(f"  y: {item['relative_roi']['y']}")
            print(f"  width: {item['relative_roi']['width']}")
            print(f"  height: {item['relative_roi']['height']}")
            print()


if __name__ == "__main__":
    main()
