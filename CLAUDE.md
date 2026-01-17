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
  - Helper functions: `calculate_worm()`, `calculate_wheel()`, `estimate_efficiency()`, `nearest_standard_module()`
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

- **Web app** (`web/`) - **COMPLETE** ✓
  - `index.html` - Responsive UI with 4 design modes
  - `app.js` - Pyodide integration, real-time calculations
  - `style.css` - Modern styling with mobile support
  - `test.html` - Diagnostic page for troubleshooting
  - `wormcalc/` - Core Python library (copied from src/)
  - **Features:**
    - Real-time calculation with debounced input (300ms)
    - Live validation feedback (errors, warnings, info)
    - Optional rounding to nearest ISO 54 standard module
    - Export to JSON, Markdown, and shareable URLs
    - Progressive enhancement with loading states
    - Works entirely in browser via Pyodide WebAssembly

- **GitHub Pages deployment** - **COMPLETE** ✓
  - `.github/workflows/deploy.yml` - Automated deployment on push to main
  - `.nojekyll` - Disables Jekyll processing for proper routing
  - Live at: `https://pzfreo.github.io/wormgearcalc/`

### What's Not Done ✗

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
├── test_core.py     # Core calculation tests
└── test_validation.py  # Validation rule tests

docs/
├── SPEC.md          # Full project spec
├── GEOMETRY.md      # Tool 2 spec (future)
└── WEB_APP.md       # Web app spec

web/                 # Browser app (deployed to GitHub Pages)
├── index.html       # Main UI (~130 lines)
├── app.js           # Pyodide integration (~400 lines)
├── style.css        # Styling (~350 lines)
├── test.html        # Diagnostic page
├── README.md        # Web app documentation
├── .nojekyll        # Disable Jekyll processing
└── wormcalc/        # Python library (copied from src/)
    ├── __init__.py
    ├── core.py
    ├── validation.py
    └── output.py

.github/
├── workflows/
│   └── deploy.yml   # Automated GitHub Pages deployment
└── README.md        # Workflow documentation
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

## Using the Web App

**Live URL**: `https://pzfreo.github.io/wormgearcalc/`

The web app provides an intuitive interface for designing worm gears:

1. **Select design mode**: Envelope, From Wheel, From Module, or From Centre Distance
2. **Enter parameters**: ODs, ratio, pressure angle, etc.
3. **Optional**: Toggle "Round to nearest standard module" (default: on)
4. **View results**: Real-time calculation with validation feedback
5. **Export**: Copy JSON, download Markdown, or share via URL

**Key feature**: When "Round to nearest standard module" is enabled, the calculator automatically adjusts non-standard modules to the nearest ISO 54 value and recalculates, ensuring manufacturability with standard tooling while showing both original and adjusted values.

## Next Tasks (Priority Order)

1. **Geometry generator** (Tool 2) - See `docs/GEOMETRY.md`
   - Separate repo or subpackage
   - Uses build123d for 3D CAD
   - Accepts JSON from this calculator
   - Outputs STEP files for CNC manufacturing

2. **Multi-start worm validation refinements**
   - Enhance validation rules for multi-start worms
   - Better efficiency estimation for higher starts

3. **Reverse engineering mode**
   - Calculate unknown parameters from measured dimensions
   - Useful for repairing or replicating existing gears

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

## Web App Workflow (for updates)

When updating the web app after changes to core Python files:

```bash
# Copy updated Python files to web directory
cp src/wormcalc/{__init__.py,core.py,validation.py,output.py} web/wormcalc/

# Commit and push
git add web/wormcalc/
git commit -m "Update web app with latest calculator changes"
git push origin main

# GitHub Actions automatically deploys to Pages (~1-2 minutes)
```

**Note**: `cli.py` is intentionally excluded from web app (uses Click, not needed in browser).

## Development History

**Initial development**:
- Core library with all 4 design modes
- Validation system
- CLI interface
- Tests

**Web app development**:
- Pyodide integration for browser-based Python
- Responsive UI with 4 design modes
- Real-time validation feedback
- Standard module rounding feature
- Export functionality (JSON, Markdown, URL sharing)
- GitHub Actions deployment workflow
- `.nojekyll` fix for proper GitHub Pages routing

**Current state**: Fully functional calculator available at `https://pzfreo.github.io/wormgearcalc/`
