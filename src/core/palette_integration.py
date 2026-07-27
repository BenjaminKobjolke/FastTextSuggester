"""FastCommandCenter integration for FastTextSuggester."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fasttool_palette import FastToolPalette, TextSuggestion

if TYPE_CHECKING:
    from src.core.screenshot_ocr_tool import ScreenshotOCRTool


class PaletteIntegration:
    def __init__(self, tool: ScreenshotOCRTool, palette: FastToolPalette) -> None:
        self._tool = tool
        self._palette = palette
        self._loaded_session = ""
        palette.add_text_provider("suggestions", self._query)
        self._register_settings()

    def poll(self) -> None:
        for action in self._palette.poll():
            if action == "capture_full_screen":
                self._tool.capture_and_process("whole_screen")
            elif action == "capture_active_window":
                self._tool.capture_and_process("active_window")

    def activate_suggestions(self) -> None:
        self._palette.activate_text_provider("suggestions")

    def _query(self, query: str, session_id: str) -> list[TextSuggestion]:
        manager = self._tool.suggestion_manager
        if manager is None or not self._tool.suggestion_settings["enabled"]:
            return []
        if session_id != self._loaded_session:
            manager.load_data_files()
            manager.load_latest_ocr_file()
            self._loaded_session = session_id
        maximum = self._tool.suggestion_settings["max_results"]
        labels = (
            manager.get_suggestions(query, maximum)
            if query
            else manager.initial_suggestions(maximum)
        )
        return [TextSuggestion(title=label, text=manager.resolve_text(label)) for label in labels]

    def _register_settings(self) -> None:
        config = self._tool.config
        hotkeys = config.get_hotkey_combinations()
        ocr = config.get_ocr_settings()
        suggestions = config.get_suggestion_settings()
        logging_settings = config.config
        definitions: list[tuple[str, str, str, Any, str, str, dict[str, Any]]] = [
            ("capture_hotkey", "Capture hotkey (standalone)", "shortcut", hotkeys["capture"], "Hotkey", "combination", {}),
            ("suggestion_hotkey", "Suggestion hotkey (standalone)", "shortcut", hotkeys["suggestion_only"], "Hotkey", "suggestion_only", {}),
            ("ocr_language", "OCR language", "string", ocr["language"], "OCR", "language", {}),
            ("optimize", "Optimize images", "bool", ocr["optimize"], "OCR", "optimize", {}),
            ("output_directory", "Output directory", "directory", config.get_output_directory(), "Output", "directory", {}),
            ("data_directory", "Data directory", "directory", config.get_data_directory(), "Output", "data_directory", {}),
            ("suggestions_enabled", "Suggestions enabled", "bool", suggestions["enabled"], "Suggestions", "enabled", {}),
            ("max_results", "Maximum results", "int", suggestions["max_results"], "Suggestions", "max_results", {"min": 1, "max": 100, "step": 1}),
            ("show_at_startup", "Show at startup (standalone)", "bool", suggestions["show_at_startup"], "Suggestions", "show_at_startup", {}),
            ("debug", "Debug logging", "bool", logging_settings.getboolean("Logging", "debug", fallback=False), "Logging", "debug", {}),
            ("log_level", "Log level", "enum", logging_settings.get("Logging", "log_level", fallback="INFO").upper(), "Logging", "log_level", {"choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]}),
        ]
        for setting_id, label, type_, value, section, key, options in definitions:
            self._palette.add_setting(
                setting_id,
                label,
                type_,
                getter=lambda type_=type_, section=section, key=key, value=value: self._read(
                    type_, section, key, value
                ),
                setter=lambda new_value, section=section, key=key: self._set(section, key, new_value),
                **options,
            )

    def _set(self, section: str, key: str, value: object) -> None:
        self._tool.apply_config_setting(section, key, value)

    def _read(self, type_: str, section: str, key: str, fallback: object) -> object:
        config = self._tool.config.config
        if type_ == "bool":
            return config.getboolean(section, key, fallback=bool(fallback))
        if type_ == "int":
            return config.getint(section, key, fallback=int(fallback))
        return config.get(section, key, fallback=str(fallback))
