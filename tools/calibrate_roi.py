import os
import sys
import argparse
import yaml
from pathlib import Path

# Garante importações a partir da raiz do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import cv2
except ImportError:
    cv2 = None

from src.utils.window import find_windows_by_title
from src.utils.screen import ScreenCapturer, pil_to_cv2


def main():
    if cv2 is None:
        print("[ERRO]: OpenCV (cv2) é necessário para a ferramenta de calibração.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Ferramenta Interativa de Calibração de ROIs")
    parser.add_argument("--image", "-i", type=str, default=None, help="Caminho para uma imagem de amostra (opcional)")
    parser.add_argument("--save-profile", "-s", type=str, default=None, help="Nome do perfil em config/profiles/ para salvar as ROIs")
    args = parser.parse_args()

    img_bgr = None

    if args.image:
        img_path = Path(args.image)
        if not img_path.exists():
            print(f"[ERRO]: Arquivo de imagem não encontrado: {img_path}")
            sys.exit(1)
        img_bgr = cv2.imread(str(img_path))
    else:
        print("Buscando janela do Projetor OBS para captura de frame...")
        obs_windows = find_windows_by_title("obs") or find_windows_by_title("projetor") or find_windows_by_title("projector")
        if not obs_windows:
            print("[ERRO]: Janela do Projetor OBS não encontrada. Abra o OBS ou forneça uma imagem com --image.")
            sys.exit(1)
        
        hwnd_obs = obs_windows[0][0]
        capturer = ScreenCapturer()
        try:
            pil_img = capturer.capture_window_client_area(hwnd_obs)
            img_bgr = pil_to_cv2(pil_img)
        finally:
            capturer.close()

    if img_bgr is None or img_bgr.size == 0:
        print("[ERRO]: Imagem inválida ou frame capturado vazio.")
        sys.exit(1)

    frame_h, frame_w = img_bgr.shape[:2]
    print(f"\n==================================================")
    print(f"        Calibração de ROIs Relativas              ")
    print(f" Dimensão do Frame: {frame_w} x {frame_h} pixels  ")
    print(f"==================================================\n")

    regions_to_calibrate = ["hp", "mana", "status_bar", "battle_list"]
    calibrated_rois = {}

    for region in regions_to_calibrate:
        print(f"-> Selecione a região da barra/área: [{region.upper()}]")
        print("   Instruções: Arraste o mouse para desenhar a caixa e pressione ENTER ou ESPAÇO para confirmar. (c para cancelar)")
        
        window_title = f"Calibrar ROI: {region} (Pressione ENTER para confirmar)"
        rect = cv2.selectROI(window_title, img_bgr, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(window_title)

        left, top, w, h = rect
        if w == 0 or h == 0:
            print(f"  [AVISO]: Região '{region}' pulada (dimensão 0).")
            continue

        rx = round(left / frame_w, 4)
        ry = round(top / frame_h, 4)
        rw = round(w / frame_w, 4)
        rh = round(h / frame_h, 4)

        calibrated_rois[region] = {
            "x": rx,
            "y": ry,
            "width": rw,
            "height": rh
        }
        print(f"  [OK] {region}: x={rx}, y={ry}, width={rw}, height={rh} (Pixels: left={left}, top={top}, w={w}, h={h})\n")

    print("==================================================")
    print("      Resultado das ROIs Calibradas em YAML       ")
    print("==================================================")
    yaml_output = yaml.dump({"regions": calibrated_rois}, default_flow_style=False, sort_keys=False)
    print(yaml_output)

    if args.save_profile:
        profile_path = Path(__file__).resolve().parent.parent / "config" / "profiles" / f"{args.save_profile}.yaml"
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing_data = {}
        if profile_path.exists():
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    existing_data = yaml.safe_load(f) or {}
            except Exception:
                existing_data = {}

        existing_data["regions"] = calibrated_rois
        with open(profile_path, "w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)
        print(f"[OK] Calibração salva com sucesso no perfil: {profile_path.resolve()}")


if __name__ == "__main__":
    main()
