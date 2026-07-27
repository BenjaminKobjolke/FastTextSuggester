from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from src.core.suggestion_manager import SuggestionManager
from src.utils.config import Config


class PaletteIntegrationTests(TestCase):
    def test_resolve_text_expands_replacements_and_blocks(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            manager = SuggestionManager(str(root / "output"), str(root / "data"))
            manager.replacements = {"email": "a@example.com"}
            manager.blocks = {"Greeting": "Greeting\nSecond line"}

            self.assertEqual(manager.resolve_text("email"), "a@example.com")
            self.assertEqual(manager.resolve_text("Greeting"), "Greeting\nSecond line")
            self.assertEqual(manager.resolve_text("ordinary"), "ordinary")

    def test_config_set_value_persists_and_reloads(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.ini"
            config = Config(str(path))

            config.set_value("Suggestions", "max_results", 25)

            reloaded = Config(str(path))
            self.assertEqual(reloaded.get_suggestion_settings()["max_results"], 25)
