# FastCommandCenter integration

How FastTextSuggester plugs into FastCommandCenter (FCC) via the
[FastTool bridge](../../FastCommandCenter-tool-bridge/CONTRACT.md). This
document covers this tool's side only; the bridge repo's `CONTRACT.md` is the
protocol source of truth.

## Modes

Selected by the `--palette` CLI flag (`main.py`):

- **Standalone** (no flag): registers its own global hotkeys via
  `HotkeyHandler`, creates the Tk `SuggestionWindow`. Behaves exactly as a
  plain desktop app.
- **Palette-managed** (`--palette`): skips local hotkey registration and Tk
  window creation, and instead constructs a `FastToolPalette("fasttextsuggester")`
  client (`main.py:229-237`) and wraps it in `PaletteIntegration`
  (`src/core/screenshot_ocr_tool.py:56-88`). FCC then drives the tool over
  IPC.

The mode split happens once, in `ScreenshotOCRTool.__init__`: when a
`palette` object is passed, `suggestion_window` stays `None` and
`PaletteIntegration` is built instead of the two local `HotkeyHandler`s.

## Manifest — `fasttool.json`

```json
{
  "id": "fasttextsuggester",
  "name": "FastTextSuggester",
  "ipc_title": "FastToolIPC::fasttextsuggester",
  "launch": { "exe": "dist/FastTextSuggester.exe", "args": ["--palette"] },
  "actions": [
    { "id": "capture_full_screen", "label": "Capture full screen" },
    { "id": "capture_active_window", "label": "Capture active window" }
  ],
  "text_providers": [
    { "id": "suggestions", "label": "FastTextSuggester", "min_chars": 0 }
  ]
}
```

FCC discovers this file by scanning its configured tool folders (added via
`Tools: manage folders`), launches `dist/FastTextSuggester.exe --palette`,
and talks to the hidden `FastToolIPC::fasttextsuggester` window.

## Client library

The Python side of the bridge is a separate installable package,
`fasttool_palette` (`-e ../FastCommandCenter-tool-bridge/client/python/fasttool_palette`
in `requirements.txt`). It owns the Win32 `WM_COPYDATA` plumbing; this repo
only calls its public API:

- `FastToolPalette(tool_id)` — opens the `FastToolIPC::<id>` window on a
  background thread.
- `palette.poll()` — call every main-loop tick; drains queued actions and
  dispatches any pending settings/text-provider messages.
- `palette.add_text_provider(id, query_callback, on_selected=None)`
- `palette.add_setting(id, label, type_, getter, setter, ...)`
- `palette.activate_text_provider(id)` — ask FCC to open one of this tool's
  providers.

All of this is wired up in `src/core/palette_integration.py`.

## Action dispatch (v1)

`PaletteIntegration.poll()` (`palette_integration.py:21-26`) is called from
the tool's main loop and maps the two declared action ids straight to
existing capture methods:

```python
def poll(self) -> None:
    for action in self._palette.poll():
        if action == "capture_full_screen":
            self._tool.capture_and_process("whole_screen")
        elif action == "capture_active_window":
            self._tool.capture_and_process("active_window")
```

After a capture finishes, the tool asks FCC to reopen the suggestions level
via `activate_suggestions()` → `palette.activate_text_provider("suggestions")`
(`palette_integration.py:28-29`, called from
`screenshot_ocr_tool.py:273-274`) — this is how OCR results become browsable
without the user pressing anything else.

## Settings protocol (v2)

`PaletteIntegration._register_settings()` (`palette_integration.py:52-81`)
exposes a fixed list of tool settings (hotkeys, OCR language, output/data
directories, suggestion limits, logging) to FCC's external settings UI. Each
entry has a `getter` reading from `Config` and a `setter` routing through
`ScreenshotOCRTool.apply_config_setting()`, which writes `settings.ini` and
reloads whatever depends on it. The tool remains the sole owner of
`settings.ini`; FCC only ever sees typed values over IPC.

## Text provider protocol (v3)

This is the "suggestions" level shown in FCC's palette UI.

**Query** — `PaletteIntegration._query(query, session_id)`
(`palette_integration.py:31-45`):

- On the first query of a new `session_id`, lazily reloads suggestion data
  (`manager.load_data_files()` + `manager.load_latest_ocr_file()`) so a
  freshly captured OCR result is picked up without restarting the tool.
- Empty query → `manager.initial_suggestions(max_results)` (recents-first
  list, see below).
- Non-empty query → `manager.get_suggestions(query, max_results)` (existing
  block/line/prefix/substring ranking, unchanged from standalone mode).
- Each label is wrapped as `TextSuggestion(title=label, text=manager.resolve_text(label))`
  — `text` is what gets inserted; it differs from `title` for replacement
  keys (e.g. title `at_sign` → text `@`) and multiline blocks.

**Selection echo → recent suggestions**: FCC sends a `selected` message back
after the user picks a result. `add_text_provider` is registered with an
`on_selected` callback (`palette_integration.py:18`):

```python
palette.add_text_provider("suggestions", self._query, self._on_selected)
```

```python
def _on_selected(self, suggestion: TextSuggestion) -> None:
    manager = self._tool.suggestion_manager
    if manager is not None:
        manager.record_selection(suggestion.title, suggestion.text)
```

`SuggestionManager.record_selection` (`src/core/suggestion_manager.py`)
moves the picked title to the front of an in-memory recents list (deduped,
capped at `RECENT_MAX = 50`) and persists it to `recent.json` in the
configured output directory. `initial_suggestions()` then leads with
whichever recents are still valid — present in `lines`, `words`, `blocks`,
**or** `replacements` — and fills any remaining slots with the original
default list (first N lines, or words if no `_line.txt` data exists),
deduplicated. This applies to every suggestion type, not just plain words:
a picked replacement key or block label shows up on top next time too.

Recents survive a restart because they're loaded from `recent.json` in
`SuggestionManager.__init__`; a missing or corrupt file is treated as empty
recents, not an error.

## Building and running in palette mode

FCC launches the compiled executable, not `main.py` directly, so a source
change needs a rebuild before it's visible in FCC:

```
compile_exe.bat
```

which runs (via this project's own venv):

```
pyinstaller --name FastTextSuggester --onefile --windowed main.py --add-data "data;data" --add-data "settings_example.ini;."
```

Gotchas:

- The build fails with `PermissionError: Access is denied` if a
  `FastTextSuggester.exe` instance still has `dist/FastTextSuggester.exe`
  open — close/kill it first (FCC may auto-relaunch the tool, so kill it
  again right before rebuilding, or rebuild before reopening it in FCC).
- Run the build through **this project's** `venv/Scripts/pyinstaller.exe`
  explicitly if your shell's `PATH` could resolve a different environment's
  `pyinstaller` first.

To test without a running FCC host, exercise `SuggestionManager` directly —
`initial_suggestions()`, `record_selection()`, and `recent.json` round-trip
don't require the IPC layer at all.
