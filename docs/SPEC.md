# Worm Gear Calculator - Project Specification

## Overview

A two-tool system for worm gear design:

1. **Tool 1: Design Calculator** (this repo) - Takes real-world constraints, outputs valid parameters
2. **Tool 2: Geometry Generator** (future) - Takes parameters, outputs CNC-ready STEP files

This repo is Tool 1 - a standalone calculator useful for design exploration, feasibility checks, and generating parameter sets for manufacturing.

## Goals

- **Design exploration** - "What ratio can I get in this space?"
- **Feasibility checking** - "Is this combination sensible?"
- **Trade-off analysis** - "How does changing worm diameter affect efficiency?"
- **Supplier specs** - Generate parameter sheets without needing CAD
- **Education** - See how parameters interact

## Target Users

- Hobbyist engineers and makers
- Luthiers (violin makers) using geared tuning machines
- Anyone needing custom worm gears for CNC manufacture

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interfaces                       │
├─────────────────┬─────────────────┬─────────────────────┤
│   CLI (Click)   │   Web (Pyodide) │   Library (import)  │
└────────┬────────┴────────┬────────┴──────────┬──────────┘
         │                 │                   │
         ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                    Core Library                          │
│  (Zero external dependencies - stdlib only)              │
├─────────────────┬─────────────────┬─────────────────────┤
│    core.py      │  validation.py  │     output.py       │
│  Calculations   │ Engineering     │  JSON/Markdown      │
│  Dataclasses    │ Rules           │  Formatters         │
└─────────────────┴─────────────────┴─────────────────────┘
```

### Key Design Decision: Zero Dependencies in Core

The core library (`core.py`, `validation.py`, `output.py`) uses only Python stdlib. This is critical for:

- **Pyodide compatibility** - Smaller WASM bundle, faster load
- **Portability** - Works anywhere Python runs
- **Testing** - Can test without network/venv

Only the CLI (`cli.py`) has external dependency (Click).

## Current Status

### Completed (Phase 1)

- [x] Core calculation module
  - [x] `design_from_envelope()` - Both ODs specified
  - [x] `design_from_wheel()` - Wheel OD + target lead angle
  - [x] `design_from_module()` - Standard module specified
  - [x] `design_from_centre_distance()` - Fixed shaft positions
  - [x] Efficiency estimation
  - [x] Self-locking determination

- [x] Validation module
  - [x] Lead angle checks (error < 1°, warning < 3°, warning > 25°)
  - [x] Module standard check (ISO 54 / DIN 780)
  - [x] Teeth count checks (error < 17, warning < 24)
  - [x] Worm proportion checks
  - [x] Pressure angle checks
  - [x] Suggestions for fixes

- [x] Output formatters
  - [x] JSON export
  - [x] Markdown export
  - [x] Plain text summary

- [x] CLI interface
  - [x] All design modes as subcommands
  - [x] Common options (pressure angle, backlash, starts, hand)
  - [x] Output format selection
  - [x] Utility commands (check-module, list-modules)

- [x] Test suite
  - [x] Core calculation tests
  - [x] Validation rule tests

### Not Yet Started

- [ ] Web application (Pyodide + HTML/JS)
- [ ] Reverse engineering mode (measure existing gear → parameters)
- [ ] Multi-start worm support validation
- [ ] Integration with Tool 2 (geometry generator)

## File Structure

```
wormgearcalc/
├── src/wormcalc/
│   ├── __init__.py      # Public API, version
│   ├── core.py          # Calculations, dataclasses
│   ├── validation.py    # Engineering rules
│   ├── output.py        # JSON/Markdown formatters
│   └── cli.py           # Click CLI
├── tests/
│   ├── test_core.py
│   └── test_validation.py
├── web/                 # Empty - for Pyodide app
├── docs/
│   ├── SPEC.md          # This file
│   ├── GEOMETRY.md      # Geometry generator spec
│   └── WEB_APP.md       # Web app spec
├── pyproject.toml
├── README.md
└── .gitignore
```

## API Reference

### Design Functions

```python
from wormcalc import (
    design_from_envelope,
    design_from_wheel,
    design_from_module,
    design_from_centre_distance,
)

# All return WormGearDesign dataclass
design = design_from_envelope(
    worm_od=20.0,           # Worm outside diameter (mm)
    wheel_od=65.0,          # Wheel outside diameter (mm)
    ratio=30,               # Gear ratio (int)
    pressure_angle=20.0,    # Pressure angle (degrees)
    backlash=0.0,           # Backlash allowance (mm)
    num_starts=1,           # Worm thread starts
    clearance_factor=0.25,  # Bottom clearance factor
    hand=Hand.RIGHT         # Thread hand
)
```

### Validation

```python
from wormcalc import validate_design, Severity

result = validate_design(design)
# result.valid: bool
# result.messages: List[ValidationMessage]
# result.errors: List[ValidationMessage]
# result.warnings: List[ValidationMessage]
```

### Output

```python
from wormcalc import to_json, to_markdown, to_summary

json_str = to_json(design, validation)
md_str = to_markdown(design, validation)
text_str = to_summary(design)
```

## CLI Reference

```bash
# Design modes
wormcalc envelope --worm-od 20 --wheel-od 65 --ratio 30
wormcalc from-wheel --wheel-od 65 --ratio 30 --target-lead-angle 8
wormcalc from-module --module 2 --ratio 30
wormcalc from-centre-distance --centre-distance 40 --ratio 30

# Common options
--pressure-angle, -pa    # Default: 20
--backlash, -b           # Default: 0
--num-starts, -s         # Default: 1
--hand                   # right|left, default: right
--output, -o             # text|json|markdown
--no-validate            # Skip validation

# Utilities
wormcalc check-module --module 2.3
wormcalc list-modules
```

## Engineering References

### Standards

- **DIN 3975** - Worm geometry definitions
- **DIN 3996** - Worm gear load capacity
- **ISO 54 / DIN 780** - Standard modules

### Validation Thresholds

| Rule | Threshold | Severity | Rationale |
|------|-----------|----------|-----------|
| Lead angle < 1° | Too low | Error | Impractical to manufacture |
| Lead angle 1-3° | Very low | Warning | Efficiency < 50% |
| Lead angle 3-5° | Low | Info | Self-locking, ~50-65% efficiency |
| Lead angle > 25° | High | Warning | Not self-locking |
| Lead angle > 45° | Too high | Error | Impractical geometry |
| Module < 0.3mm | Too small | Error | Precision limits |
| Module non-standard | - | Info | Tooling availability |
| Wheel teeth < 17 | Too few | Error | Severe undercut |
| Wheel teeth 17-24 | Low | Warning | Some undercut |
| Worm pitch_dia < 3×module | Too thin | Error | Weak shaft |
| Worm pitch_dia < 5×module | Thin | Warning | Verify strength |

### Efficiency Estimation

Based on simplified friction model:
```
η = tan(γ) / tan(γ + ρ)
```
Where:
- γ = lead angle
- ρ = friction angle = atan(μ / cos(α))
- μ = friction coefficient (default 0.05 for lubricated steel/bronze)
- α = pressure angle

### Self-Locking

Conservative threshold: lead angle < 6° considered self-locking.
Actual self-locking depends on materials, lubrication, and load direction.
