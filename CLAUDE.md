# CLAUDE.md - Context for Claude Code

## Project Summary

Worm gear calculator - Python library + CLI + web app for designing worm gear pairs. Takes engineering constraints, outputs validated parameters in JSON/Markdown.

**Owner**: Paul Fremantle (pzfreo) - luthier and hobby programmer
**Use case**: Designing custom worm gears for CNC manufacture

## Current State

### What's Done ✓

- **Core library** (`src/wormcalc/core.py`)
  - Dataclasses: `WormParameters`, `WheelParameters`, `WormGearDesign`
  - Design functions: `design_from_envelope()`, `design_from_wheel()`, `design_from_module()`, `design_from_centre_distance()`
  - Helper functions: `calculate_worm()`, `calculate_wheel()`, `estimate_efficiency()`
  - Constants: `STANDARD_MODULES` (ISO 54)

- **Validation** (`src/wormcalc/validation.py`)
  - Lead angle checks (error <1°, warning <3° or >25°)
  - Module standard check
  - Teeth count checks (<17 error, <24 warning)
  - Worm proportions check
  - Returns `ValidationResult` with messages and suggestions

- **Output** (`src/wormcalc/output.py`)
  - `to_json()` - JSON export
  - `to_markdown()` - MD export
  - `to_summary()` - Plain text

- **CLI** (`src/wormcalc/cli.py`)
  - Uses Click
  - Subcommands: `envelope`, `from-wheel`, `from-module`, `from-centre-distance`
  - Utilities: `check-module`, `list-modules`

- **Tests** (`tests/`)
  - `test_core.py` - calculation tests
  - `test_validation.py` - rule tests
  - All pass (tested manually, pytest needs network)

### What's Not Done ✗

- **Web app** (`web/`) - Pyodide + HTML/JS interface
- **Geometry generator** (separate Tool 2) - build123d STEP output
- Multi-start worm validation refinements
- Reverse engineering mode

## Key Design Decisions

1. **Zero dependencies in core** - `core.py`, `validation.py`, `output.py` use stdlib only. Critical for Pyodide.

2. **CLI uses Click** - Only external dependency, not loaded for web.

3. **Dataclass-based API** - All results are dataclasses, serialize cleanly to JSON.

4. **Validation separate from calculation** - Can calculate invalid designs, validation is opt-in.

## File Structure

```
src/wormcalc/
├── __init__.py      # Public API exports
├── core.py          # Calculations (~500 lines)
├── validation.py    # Engineering rules (~220 lines)
├── output.py        # Formatters (~200 lines)
└── cli.py           # Click CLI (~180 lines)

tests/
├── test_core.py
└── test_validation.py

docs/
├── SPEC.md          # Full project spec
├── GEOMETRY.md      # Tool 2 spec (future)
└── WEB_APP.md       # Web app spec (next task)

web/                 # Empty - for Pyodide app
```

## Quick Test

```bash
cd wormgearcalc
PYTHONPATH=src python3 -c "
from wormcalc import design_from_module, validate_design, to_summary
design = design_from_module(module=2.0, ratio=30)
print(to_summary(design))
"
```

## Next Tasks (Priority Order)

1. **Web app** - See `docs/WEB_APP.md`
   - `web/index.html` - Single page app
   - `web/app.js` - Pyodide loader
   - `web/style.css` - Styling
   - Copy Python files to `web/wormcalc/`

2. **GitHub Pages deployment** - Enable in repo settings

3. **Geometry generator** (Tool 2) - See `docs/GEOMETRY.md`
   - Separate repo or subpackage
   - Uses build123d
   - Accepts JSON from this calculator

## API Quick Reference

```python
from wormcalc import (
    # Design functions
    design_from_envelope,    # Both ODs specified
    design_from_wheel,       # Wheel OD + target lead angle
    design_from_module,      # Standard module
    design_from_centre_distance,  # Fixed shaft positions
    
    # Validation
    validate_design,         # Returns ValidationResult
    
    # Output
    to_json,                 # JSON string
    to_markdown,             # MD string
    to_summary,              # Plain text
    
    # Types
    WormGearDesign,          # Main result type
    Hand,                    # RIGHT or LEFT
)

# Example
design = design_from_envelope(
    worm_od=20,
    wheel_od=65,
    ratio=30,
    pressure_angle=20,
    backlash=0,
    num_starts=1,
    hand=Hand.RIGHT
)

result = validate_design(design)
if result.valid:
    print(to_json(design, result))
```

## CLI Quick Reference

```bash
wormcalc envelope --worm-od 20 --wheel-od 65 --ratio 30
wormcalc from-wheel --wheel-od 65 --ratio 30 --target-lead-angle 8
wormcalc from-module --module 2 --ratio 30 --output json
wormcalc list-modules
```

## Engineering Context

- **Lead angle** - Angle of thread helix. Low = self-locking but inefficient. High = efficient but not self-locking.
- **Module** - Tooth size. Axial module (worm) = transverse module (wheel).
- **Centre distance** - Shaft spacing. = (worm_pitch_dia + wheel_pitch_dia) / 2
- **Self-locking** - Worm can drive wheel, but wheel can't drive worm. Occurs when lead angle < ~6°.

## Commits So Far

Initial commit should include:
- All src/wormcalc/ files
- All tests/ files
- All docs/ files
- pyproject.toml
- README.md
- .gitignore
- CLAUDE.md (this file)
