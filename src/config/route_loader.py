import json
from pathlib import Path
from typing import Mapping

from src.bot.cavebot.models import HuntRoute, RelativeRegion, RouteSettings, Waypoint, WaypointType


class RouteValidationError(ValueError):
    """Indica que um arquivo de rota não pode ser usado com segurança."""


def load_route(path: str | Path, known_markers: Mapping[str, str]) -> HuntRoute:
    route_path = Path(path)
    if not route_path.is_file():
        raise RouteValidationError(f"Arquivo de rota não encontrado: {route_path}")
    try:
        data = json.loads(route_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RouteValidationError(f"JSON de rota inválido: {error}") from error

    if not isinstance(data, dict):
        raise RouteValidationError("A raiz da rota deve ser um objeto JSON")
    try:
        hunt_name = _required_string(data, "hunt_name")
        version = _required_int(data, "version")
        loop = data.get("loop", False)
        if not isinstance(loop, bool):
            raise RouteValidationError("Campo 'loop' deve ser booleano")
        settings = _parse_settings(data.get("settings"))
        raw_waypoints = data.get("waypoints")
        if not isinstance(raw_waypoints, list) or not raw_waypoints:
            raise RouteValidationError("A rota deve conter ao menos um waypoint")
        waypoints = tuple(_parse_waypoint(item, known_markers) for item in raw_waypoints)
    except (TypeError, ValueError) as error:
        if isinstance(error, RouteValidationError):
            raise
        raise RouteValidationError(str(error)) from error

    waypoint_ids = [waypoint.id for waypoint in waypoints]
    if len(set(waypoint_ids)) != len(waypoint_ids):
        raise RouteValidationError("Os IDs dos waypoints devem ser únicos")
    try:
        return HuntRoute(hunt_name, version, loop, settings, waypoints)
    except ValueError as error:
        raise RouteValidationError(str(error)) from error


def _parse_settings(raw: object) -> RouteSettings:
    if not isinstance(raw, dict):
        raise RouteValidationError("Campo 'settings' deve ser um objeto")
    try:
        return RouteSettings(
            match_threshold=float(raw["match_threshold"]),
            arrival_radius_pixels=float(raw["arrival_radius_pixels"]),
            progress_epsilon_pixels=float(raw["progress_epsilon_pixels"]),
            stuck_timeout_ms=int(raw["stuck_timeout_ms"]),
            click_cooldown_ms=int(raw["click_cooldown_ms"]),
            max_retries=int(raw["max_retries"]),
        )
    except KeyError as error:
        raise RouteValidationError(f"Campo obrigatório ausente em settings: {error.args[0]}") from error


def _parse_waypoint(raw: object, known_markers: Mapping[str, str]) -> Waypoint:
    if not isinstance(raw, dict):
        raise RouteValidationError("Cada waypoint deve ser um objeto")
    waypoint_id = _required_string(raw, "id")
    type_name = _required_string(raw, "type")
    try:
        waypoint_type = WaypointType(type_name)
    except ValueError as error:
        raise RouteValidationError(f"Tipo de waypoint desconhecido: {type_name}") from error
    if waypoint_type != WaypointType.MARKER_CLICK:
        raise RouteValidationError("Nesta fase, somente waypoints MARKER_CLICK são suportados")

    marker = _required_string(raw, "marker")
    if marker not in known_markers:
        raise RouteValidationError(f"Marcador '{marker}' não está configurado no perfil")
    marker_path = Path(known_markers[marker])
    if not marker_path.is_file():
        raise RouteValidationError(f"Template do marcador '{marker}' não existe: {marker_path}")

    region_raw = raw.get("expected_region")
    if not isinstance(region_raw, dict):
        raise RouteValidationError(f"Waypoint '{waypoint_id}' exige expected_region")
    try:
        region = RelativeRegion(
            float(region_raw["x"]),
            float(region_raw["y"]),
            float(region_raw["width"]),
            float(region_raw["height"]),
        )
        threshold = raw.get("match_threshold")
        return Waypoint(
            id=waypoint_id,
            type=waypoint_type,
            marker=marker,
            expected_region=region,
            match_threshold=float(threshold) if threshold is not None else None,
            description=str(raw.get("description", "")),
        )
    except KeyError as error:
        raise RouteValidationError(f"Campo obrigatório ausente em expected_region: {error.args[0]}") from error


def _required_string(data: dict, field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RouteValidationError(f"Campo '{field}' deve ser uma string não vazia")
    return value.strip()


def _required_int(data: dict, field: str) -> int:
    value = data.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise RouteValidationError(f"Campo '{field}' deve ser inteiro")
    return value
