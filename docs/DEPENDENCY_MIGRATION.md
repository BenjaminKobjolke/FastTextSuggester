# Dependency Migration

## Status

Completed on 2026-07-27.

## Platform

- Operating system: Windows
- Python: CPython 3.11.9
- Package manager: pip 24.0 with `requirements.txt`
- Dependency locking: exact direct pins in `requirements.txt`; no generated lockfile

## Inventory

Runtime dependencies:

- `keyboard==0.13.5`
- `pillow==11.1.0`
- `pynput==1.8.1`
- `pytesseract==0.3.13`
- `pywin32>=310`
- `winhotkeys` from a pinned Git commit
- Local editable `fasttool_palette` bridge client

Packaging and supporting dependencies:

- `altgraph==0.17.4`
- `packaging==24.2`
- `pefile==2023.2.7`
- `pyinstaller==6.17.0`
- `pyinstaller-hooks-contrib==2025.10`
- `pywin32-ctypes==0.2.3`
- `six==1.17.0`

## Security migration

Source: `pillow==11.1.0`

Target: `pillow==12.3.0`

The 17 unique Pillow advisories reported by `pip-audit` match the 17 open
Dependabot alerts (13 high and 4 moderate). All 17 advisories list fixed
versions no newer than Pillow 12.3.0.

Migration order:

1. Pin Pillow 12.3.0.
2. Install that single upgrade in the existing Python 3.11 environment.
3. Run import and Pillow API smoke checks.
4. Run the project's tests and executable build.
5. Re-run the dependency audit and record the result below.

Compatibility notes:

- Pillow 12.3.0 publishes a CPython 3.11 Windows x86-64 wheel.
- The application uses `ImageGrab`, `Image.open`, `ImageEnhance.Contrast`, and
  `ImageOps.autocontrast`; no removed Pillow APIs were found in the codebase.
- The editable local bridge and Git-sourced `winhotkeys` dependency cannot be
  resolved through PyPI-based vulnerability auditing and require separate
  source/repository review.

## Results

- Updated `requirements.txt` from Pillow 11.1.0 to 12.3.0.
- Installed Pillow 12.3.0 successfully in the CPython 3.11 environment.
- Pillow import and image-processing API smoke check: passed.
- Unit tests: 2 passed.
- Python bytecode compilation check: passed.
- PyInstaller one-file Windows build: passed in an isolated output directory.
- `pip check`: no broken requirements.
- Post-upgrade audit: no Pillow vulnerabilities reported; all 17 Dependabot
  findings are remediated by the new pin.

The environment-wide audit still reports findings in `pip==24.0` and
`setuptools==65.5.0`. These bootstrap tools are installed in the local virtual
environment but are not declared application dependencies and are not the
source of the 17 Dependabot alerts. The audit also skips the editable local
bridge client and cannot audit the Git-sourced `winhotkeys` package through
PyPI.

No project code analyzer is configured. Validation therefore used the existing
unit tests, Python compilation, dependency consistency checks, and the
PyInstaller build.
