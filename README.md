# Worm Gear Calculator

A comprehensive worm gear design tool available as a Python library, CLI, and web application.

**🌐 Try the web app**: [https://pzfreo.github.io/wormgearcalc/](https://pzfreo.github.io/wormgearcalc/)

## Features

- **Multiple design modes**: Design from envelope constraints, wheel size, standard module, or centre distance
- **Engineering validation**: Automatic checks against DIN/ISO standards and best practices
- **Multiple output formats**: JSON, Markdown, or plain text
- **Browser-based web app**: No installation required, runs Python via Pyodide WebAssembly
- **Standard module rounding**: Automatically adjust to ISO 54 standard modules for manufacturability
- **Zero dependencies**: Core library uses only Python stdlib, compatible with Pyodide

## Quick Start

### Web App (Easiest)

Visit **[https://pzfreo.github.io/wormgearcalc/](https://pzfreo.github.io/wormgearcalc/)** for instant access.

- No installation required
- Real-time calculations with validation
- Export to JSON, Markdown, or shareable URLs
- Optional rounding to standard modules

## Installation

```bash
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

## CLI Usage

### Design from envelope (both ODs specified)

```bash
wormcalc envelope --worm-od 20 --wheel-od 65 --ratio 30
```

### Design from wheel constraint

```bash
wormcalc from-wheel --wheel-od 65 --ratio 30 --target-lead-angle 8
```

### Design from standard module

```bash
wormcalc from-module --module 2 --ratio 30
```

### Design from centre distance

```bash
wormcalc from-centre-distance --centre-distance 40 --ratio 30
```

### Output formats

```bash
# JSON output
wormcalc from-module --module 2 --ratio 30 --output json

# Markdown output
wormcalc from-module --module 2 --ratio 30 --output md
```

### Common options

- `--pressure-angle` / `-pa`: Pressure angle in degrees (default: 20)
- `--backlash` / `-b`: Backlash allowance in mm (default: 0)
- `--num-starts` / `-s`: Number of worm starts (default: 1)
- `--hand`: Thread hand, 'right' or 'left' (default: right)
- `--output` / `-o`: Output format: text, json, or markdown

### Utility commands

```bash
# Check if a module is standard
wormcalc check-module --module 2.3

# List all standard modules
wormcalc list-modules
```

## Library Usage

```python
from wormcalc import (
    design_from_envelope,
    design_from_wheel,
    design_from_module,
    validate_design,
    to_json,
    to_markdown,
)

# Design from constraints
design = design_from_envelope(
    worm_od=20,
    wheel_od=65,
    ratio=30,
    pressure_angle=20,
    backlash=0.05
)

# Validate
validation = validate_design(design)
print(f"Valid: {validation.valid}")
for msg in validation.warnings:
    print(f"  Warning: {msg.message}")

# Export
print(to_json(design, validation))
print(to_markdown(design, validation))

# Access individual parameters
print(f"Module: {design.worm.module}")
print(f"Centre distance: {design.centre_distance}")
print(f"Lead angle: {design.worm.lead_angle}°")
print(f"Efficiency: {design.efficiency_estimate * 100:.0f}%")
```

## Design Modes

### Envelope Mode

Use when you have specific space constraints for both gears:

```python
design = design_from_envelope(
    worm_od=20,      # Max worm outside diameter
    wheel_od=65,     # Max wheel outside diameter
    ratio=30         # Required gear ratio
)
```

### Wheel-Constrained Mode

Use when wheel size is fixed but worm can be sized for optimal efficiency:

```python
design = design_from_wheel(
    wheel_od=65,
    ratio=30,
    target_lead_angle=8  # Aims for this lead angle
)
```

### Module Mode

Traditional approach using standard module values:

```python
design = design_from_module(
    module=2.0,      # Standard module
    ratio=30,
    target_lead_angle=7
)
```

### Centre Distance Mode

Use when fitting into existing housing:

```python
design = design_from_centre_distance(
    centre_distance=40,
    ratio=30
)
```

## Validation

The library validates designs against engineering rules:

| Rule | Threshold | Severity |
|------|-----------|----------|
| Lead angle < 1° | Impractical | Error |
| Lead angle 1-3° | Very inefficient | Warning |
| Lead angle > 25° | Not self-locking | Warning |
| Module < 0.3mm | Too small | Error |
| Module non-standard | Not ISO 54 | Info |
| Wheel teeth < 17 | Severe undercut | Error |
| Wheel teeth 17-24 | Some undercut | Warning |
| Worm pitch dia < 3×module | Weak shaft | Error |
| Worm pitch dia < 5×module | Verify strength | Warning |

## Output Example

### Text

```
═══ Worm Gear Design ═══
Ratio: 30:1
Module: 2.000 mm

Worm:
  Tip diameter (OD): 20.00 mm
  Pitch diameter:    16.00 mm
  Root diameter:     11.00 mm
  Lead angle:        7.1°
  Starts:            1

Wheel:
  Tip diameter (OD): 64.00 mm
  Pitch diameter:    60.00 mm
  Root diameter:     55.00 mm
  Teeth:             30
  Helix angle:       82.9°

Centre distance: 38.00 mm
Efficiency (est): 72%
Self-locking: No
```

## Testing

```bash
pytest
```

With coverage:

```bash
pytest --cov=wormcalc --cov-report=html
```

## License

MIT
