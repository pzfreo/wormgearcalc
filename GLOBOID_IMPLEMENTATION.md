# Globoid Worm Implementation - Completed

## Summary

Successfully implemented full globoid (hourglass) worm support according to specification. The calculator now generates proper parameters for globoid worms with configurable throat reduction.

## Changes Made

### 1. Core Library (`src/wormcalc/core.py`)

#### WormParameters Dataclass
- Added `throat_reduction: Optional[float]` field to store the design parameter
- Existing throat radii fields retained for geometry output

#### Design Functions
All design functions now accept `throat_reduction` parameter (default 0.0):
- `design_from_envelope()`
- `design_from_wheel()`
- `design_from_module()`
- `design_from_centre_distance()`

#### Calculation Logic

**For Globoid Worms:**
1. **Worm Pitch Diameter**: Increased by `2 × throat_reduction` compared to cylindrical
   ```python
   worm_pitch_diameter = worm_pitch_diameter_cylindrical + 2 * throat_reduction
   ```

2. **Centre Distance**: Reduced by `throat_reduction` to create hourglass effect
   ```python
   centre_distance = standard_centre_distance - throat_reduction
   ```

3. **Throat Radii**: Calculated from actual centre distance
   ```python
   throat_pitch_radius = centre_distance - wheel_pitch_radius
   ```

**Result**: `throat_pitch_radius < worm_pitch_radius` creates the hourglass geometry

### 2. Validation (`src/wormcalc/validation.py`)

Added comprehensive globoid validations:

- **Throat reduction range checks**:
  - ERROR if > 50% of module
  - WARNING if < 0.02mm (too small for effect)
  - WARNING if > 30% of module (manufacturability concerns)

- **Clearance validation**:
  - ERROR if worm throat tip interferes with wheel root
  - WARNING if clearance < 0.05mm (tight tolerances)

- **Geometry verification**:
  - ERROR if throat_pitch_radius >= nominal_pitch_radius (invalid hourglass)

### 3. JSON Output (`src/wormcalc/output.py`)

- Added `throat_reduction_mm` to worm section in JSON export
- Includes all throat radii when present
- Compatible with worm-gear-3d geometry generator

### 4. Web Application

#### UI Updates (`web/index.html`)
- Added throat reduction input field (conditionally shown for globoid)
- Includes helpful hint text with typical values by gear size
- Clean integration with existing manufacturing options

#### JavaScript (`web/app.js`)
- Added `onWormTypeChange()` handler to show/hide throat reduction input
- Updated all design mode input gathering to include `throat_reduction`
- Updated Python function call formatting
- Added change listener for worm type selector

#### Styling (`web/style.css`)
- Added `.hint` class for input helper text
- Styled with muted color and appropriate sizing

## Verification

### Test Results

**Test 1: Module Design Mode**
```
Cylindrical: pitch_dia=3.258mm, centre=4.629mm
Globoid:     pitch_dia=3.358mm, centre=4.629mm, throat_reduction=0.05mm
Result: ✓ Pitch diameter increased by 2×0.05mm, hourglass effect achieved
```

**Test 2: Envelope Design Mode**
```
Given: worm_od=7.6mm, wheel_od=6.8mm
Cylindrical: centre=6.400mm
Globoid:     centre=6.350mm (reduced by 0.05mm)
Result: ✓ Centre distance correctly reduced
```

**Test 3: JSON Output**
```json
{
  "worm": {
    "pitch_diameter_mm": 3.358,
    "throat_reduction_mm": 0.05,    ← NEW
    "throat_pitch_radius_mm": 1.629,
    "throat_tip_radius_mm": 2.029,
    "throat_root_radius_mm": 1.129
  }
}
```
Result: ✓ All required fields present

### Validation Examples

- ✓ Warns if throat reduction too small (< 0.02mm)
- ✓ Errors if throat reduction too large (> 50% of module)
- ✓ Checks clearance at throat
- ✓ Verifies throat < nominal (proper hourglass)
- ✓ Warns if globoid worm used without throated wheel

## Usage Examples

### Python Library
```python
from wormcalc import design_from_module, WormType

# Design a globoid worm gear
design = design_from_module(
    module=2.0,
    ratio=30,
    worm_type=WormType.GLOBOID,
    throat_reduction=0.1,  # 0.1mm hourglass effect
    wheel_throated=True
)

# Results include throat geometry
print(f"Throat reduction: {design.worm.throat_reduction}mm")
print(f"Throat pitch radius: {design.worm.throat_pitch_radius}mm")
print(f"Nominal pitch radius: {design.worm.pitch_radius}mm")
```

### Web Application
1. Select "Globoid (hourglass)" from Worm Type dropdown
2. Throat Reduction input appears
3. Enter value (e.g., 0.05mm for small gears)
4. Calculator automatically adjusts pitch diameter and centre distance
5. Validation feedback shows throat geometry status

## Guidelines for Throat Reduction

As specified in the prompt:

| Gear Size | Module | Recommended Throat Reduction |
|-----------|--------|------------------------------|
| Small     | < 1mm  | 0.05 - 0.1 mm               |
| Medium    | 1-3mm  | 0.1 - 0.2 mm                |
| Large     | > 3mm  | 0.2 - 0.5 mm                |

## Compatibility

- **worm-gear-3d**: JSON output includes all required parameters
- **Backwards compatible**: Default `throat_reduction=0.0` maintains cylindrical behavior
- **Web deployment**: Updated files copied to `web/wormcalc/` directory

## Next Steps

To deploy to GitHub Pages:
```bash
git add -A
git commit -m "Implement globoid worm support with throat reduction"
git push origin main
```

GitHub Actions will automatically deploy the updated web app.

## References

- Original specification: User prompt for globoid worm implementation
- Standards: DIN 3975 (worm geometry definitions)
- Related project: wormgear-geometry (3D CAD generation)
