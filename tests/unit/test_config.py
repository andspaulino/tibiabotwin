import unittest


from src.config.loader import load_config, ConfigValidationError, validate_and_parse
from src.config.models import AppConfig


class TestConfigLoader(unittest.TestCase):

    def test_load_default_config(self):
        """Verifica se a configuração padrão default.yaml é carregada corretamente."""
        cfg = load_config()
        self.assertIsInstance(cfg, AppConfig)
        self.assertEqual(cfg.window.tibia_title, "Tibia")
        self.assertEqual(cfg.window.obs_title, "obs")
        self.assertTrue(cfg.healer.enabled)
        self.assertEqual(cfg.healer.spell.key, "1")
        self.assertEqual(cfg.healer.spell.hp_below, 80.0)

    def test_profile_override(self):
        """Verifica a sobreposição correta de valores ao carregar um perfil."""
        cfg = load_config(profile_path="character-example")
        self.assertEqual(cfg.healer.spell.key, "F1")
        self.assertEqual(cfg.healer.spell.hp_below, 85.0)
        self.assertEqual(cfg.healer.mana_potion.key, "F2")
        self.assertEqual(cfg.healer.emergency_potion.key, "F3")



    def test_selected_hunt_is_loaded_from_cavebot_config(self):
        cfg = validate_and_parse({"cavebot": {"selected_hunt": "depot_loop.json"}})

        self.assertEqual(cfg.cavebot.selected_hunt, "depot_loop.json")

    def test_default_config_selects_newhaven_route(self):
        cfg = load_config()

        self.assertEqual(cfg.cavebot.selected_hunt, "newhaven_left.json")

    def test_selected_hunt_rejects_paths_outside_hunts_directory(self):
        with self.assertRaises(ConfigValidationError):
            validate_and_parse({"cavebot": {"selected_hunt": "../depot_loop.json"}})

    def test_invalid_percentage(self):
        """Verifica erro quando um percentual está fora do intervalo 0–100%."""
        data = {
            "healer": {
                "spell": {
                    "hp_below": 150.0
                }
            }
        }
        with self.assertRaises(ConfigValidationError):
            validate_and_parse(data)

    def test_negative_cooldown(self):
        """Verifica erro quando um cooldown é negativo."""
        data = {
            "healer": {
                "spell": {
                    "cooldown_ms": -500
                }
            }
        }
        with self.assertRaises(ConfigValidationError):
            validate_and_parse(data)

    def test_empty_hotkey(self):
        """Verifica erro quando a hotkey é vazia com recurso ativado."""
        data = {
            "healer": {
                "spell": {
                    "enabled": True,
                    "key": ""
                }
            }
        }
        with self.assertRaises(ConfigValidationError):
            validate_and_parse(data)

    def test_missing_file(self):
        """Verifica erro ao tentar carregar um arquivo inexistente."""
        with self.assertRaises(ConfigValidationError):
            load_config(config_path="caminho_inexistente_123.yaml")


if __name__ == "__main__":
    unittest.main()
