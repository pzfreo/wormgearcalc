# Code Review & Test Coverage Report

Generated: 2026-01-24

## Executive Summary

**Overall Quality**: Good ✓
- Core calculation logic is well-tested (96% coverage)
- Validation logic is solid (82% coverage)
- 67/69 tests passing (97% pass rate)
- Output formatting untested (7% coverage)
- CLI untested (0% coverage)

**Status**: Production-ready for calculation engine, needs test improvements for output/CLI

---

## Test Coverage Analysis

### Coverage by Module

| Module | Statements | Coverage | Status |
|--------|-----------|----------|--------|
| `core.py` | 206 | **96%** | ✓ Excellent |
| `validation.py` | 213 | **82%** | ✓ Good |
| `output.py` | 97 | **7%** | ✗ Poor |
| `cli.py` | 90 | **0%** | ✗ Not tested |
| `__init__.py` | 6 | **100%** | ✓ Perfect |
| **Overall** | 612 | **62%** | ⚠ Moderate |

### Test Files

- `test_core.py`: 527 lines, 43 tests → **All passing** ✓
- `test_validation.py`: 403 lines, 26 tests → **2 failures** ⚠

### Missing Test Coverage

#### `output.py` (93% untested)
**Missing:**
- `to_json()` - JSON serialization
- `to_markdown()` - Markdown formatting
- `to_summary()` - Text summary generation
- Edge cases: globoid fields, profile shift, throat reduction

**Impact**: High - These are user-facing outputs, should be tested

#### `cli.py` (100% untested)
**Missing:**
- All CLI commands (`envelope`, `from-wheel`, `from-module`, `from-centre-distance`)
- Argument parsing
- Error handling
- Output formatting

**Impact**: Medium - CLI is user-facing but less critical than web app

---

## Test Failures

### 1. `test_low_teeth_warning` - FAILED

**Location**: `tests/test_validation.py:142`

**Issue**: Test expects `TEETH_LOW` warning code but gets `WORM_THIN` instead

**Root Cause**: The test design (worm OD 10mm, wheel OD 42mm, ratio 20) produces a thin worm which triggers `WORM_THIN` warning before `TEETH_LOW` warning

**Fix**: Adjust test parameters to avoid worm thinness warning
```python
# Current (fails):
design = design_from_envelope(
    worm_od=10.0,   # Too small
    wheel_od=42.0,
    ratio=20
)

# Suggested fix:
design = design_from_envelope(
    worm_od=20.0,   # Larger worm
    wheel_od=50.0,
    ratio=22  # 22 teeth = in warning range
)
```

### 2. `test_globoid_design_valid` - FAILED

**Location**: `tests/test_validation.py:381`

**Issue**: Globoid design without `throat_reduction` parameter causes error

**Error Message**: "Invalid globoid: throat radius must be less than nominal radius"

**Root Cause**: Test doesn't specify `throat_reduction`, defaults to 0.0, which is invalid for globoid

**Fix**: Add proper throat_reduction parameter
```python
# Current (fails):
design = design_from_module(
    module=2.0,
    ratio=30,
    target_lead_angle=8.0,
    worm_type=WormType.GLOBOID,  # Needs throat_reduction!
    wheel_throated=True,
    profile=WormProfile.ZA
)

# Suggested fix:
design = design_from_module(
    module=2.0,
    ratio=30,
    target_lead_angle=8.0,
    worm_type=WormType.GLOBOID,
    throat_reduction=0.05,  # Add this!
    wheel_throated=True,
    profile=WormProfile.ZA
)
```

---

## Code Quality Issues

### High Priority

**None identified** - Core calculation logic is sound

### Medium Priority

#### 1. Uncovered Code Paths in `validation.py` (18% missed)

**Lines with no coverage:**
- `155`: Very high lead angle check (>45°)
- `169`: Module warning edge case
- `212`: Throat reduction edge case
- `243, 251, 265`: Profile shift warnings
- `321, 329, 336`: Manufacturing compatibility checks
- Others: Info message branches

**Recommendation**: Add tests for extreme values (lead angle >45°, large profile shifts)

#### 2. Missing Edge Case Coverage in `core.py` (4% missed)

**Lines with no coverage:**
- `76`: Error path in pitch diameter calculation
- `99`: Edge case in worm calculation
- `151`: Boundary condition
- `202`: Alternative calculation path
- `653, 800`: Exception handling

**Recommendation**: Add tests for invalid inputs and boundary conditions

### Low Priority

#### 1. No Output Format Tests

**Risk**: Format changes could break integrations without detection

**Recommendation**: Add tests for:
- JSON schema validation
- Markdown structure
- Text summary format
- Special characters/Unicode handling

#### 2. No CLI Integration Tests

**Risk**: CLI argument changes could break without detection

**Recommendation**: Add CLI tests using `pytest` with Click's `CliRunner`:
```python
from click.testing import CliRunner
from wormcalc.cli import cli

def test_envelope_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['envelope', '--worm-od', '20', '--wheel-od', '65', '--ratio', '30'])
    assert result.exit_code == 0
    assert 'Module' in result.output
```

---

## Code Smells / Anti-patterns

### None Critical

✓ No global mutable state
✓ No circular imports
✓ Clean dataclass usage
✓ Type hints present
✓ No magic numbers (constants defined)
✓ No TODO/FIXME/HACK comments

### Minor Observations

1. **Web app duplicates core files**: `web/wormcalc/` copies from `src/wormcalc/`
   - **Current process**: Manual copy after changes
   - **Risk**: Files can get out of sync
   - **Recommendation**: Add pre-commit hook or CI check to verify sync

2. **Web app has no automated tests**: JavaScript code in `web/app.js` (560 lines) is untested
   - **Risk**: Breaking changes to calculator UI/UX
   - **Recommendation**: Add browser tests (Playwright/Selenium) or at minimum JS unit tests

---

## Recommendations

### Immediate (Before Next Release)

1. **Fix failing tests** (2 failures)
   - Update `test_low_teeth_warning` with better parameters
   - Add `throat_reduction` to `test_globoid_design_valid`

2. **Add output format tests** (boost coverage 7% → 80%+)
   ```python
   # tests/test_output.py
   def test_to_json_valid_schema():
       design = design_from_module(module=2.0, ratio=30)
       result = validate_design(design)
       json_str = to_json(design, result)

       data = json.loads(json_str)
       assert 'worm' in data
       assert 'wheel' in data
       assert 'module' in data['worm']

   def test_to_markdown_structure():
       design = design_from_module(module=2.0, ratio=30)
       result = validate_design(design)
       md = to_markdown(design, result)

       assert '# Worm Gear Design' in md
       assert '## Worm' in md
       assert '## Wheel' in md
   ```

3. **Verify web/src sync** - Ensure `web/wormcalc/*.py` matches `src/wormcalc/*.py`
   ```bash
   diff -r src/wormcalc/ web/wormcalc/ --exclude='cli.py' --exclude='__pycache__'
   ```

### Short Term (Next Sprint)

4. **Add CLI tests** (boost coverage 0% → 70%+)
   - Test all command variants
   - Test error handling
   - Test output formats (JSON, MD, text)

5. **Add edge case tests**
   - Very large/small modules
   - Extreme lead angles (>45°, <0.5°)
   - Large profile shifts
   - Multi-start worms (2, 3, 4 starts)

6. **Web app JS tests**
   - Unit tests for calculation logic
   - Integration tests for UI flows
   - Browser tests for cross-browser compatibility

### Long Term (Future)

7. **Property-based testing** with Hypothesis
   ```python
   from hypothesis import given, strategies as st

   @given(
       module=st.floats(min_value=0.3, max_value=50),
       ratio=st.integers(min_value=5, max_value=100)
   )
   def test_design_properties(module, ratio):
       design = design_from_module(module=module, ratio=ratio)
       # Invariants that should always hold
       assert design.wheel.num_teeth == ratio
       assert design.centre_distance > 0
   ```

8. **Performance benchmarks**
   - Track calculation time for typical designs
   - Prevent performance regressions

9. **Integration tests** for full workflows
   - Design → Validate → Export pipeline
   - URL parameter loading in web app

---

## Security Considerations

✓ **No SQL injection risk** - No database
✓ **No XSS risk** - Pyodide runs in sandbox
✓ **No command injection** - No shell execution in core
✓ **Input validation** - Validation module checks bounds

**Web App**: Uses Pyodide (WebAssembly sandbox) - inherently safe

---

## Performance Notes

**Calculation Speed**: Fast (< 1ms for typical designs)
**Web App Load Time**: ~2-3s for Pyodide initialization (acceptable)
**Memory Usage**: Low (dataclasses, no caching)

No performance issues identified.

---

## Documentation Quality

✓ **CLAUDE.md**: Excellent project context
✓ **GLOBOID_CORRECTION.md**: Good error documentation
✓ **Docstrings**: Present in test files
⚠ **Missing**: API documentation in source code

**Recommendation**: Add docstrings to public functions in `core.py`
```python
def design_from_module(
    module: float,
    ratio: int,
    ...
) -> WormGearDesign:
    """
    Design a worm gear pair from a specified module.

    Args:
        module: Tooth module in mm (ISO 54 standard recommended)
        ratio: Gear ratio (wheel teeth / worm starts)
        ...

    Returns:
        Complete worm gear design with calculated parameters

    Example:
        >>> design = design_from_module(module=2.0, ratio=30)
        >>> design.worm.lead_angle
        7.125
    """
```

---

## Conclusion

**Strengths:**
- Solid calculation engine (96% coverage)
- Good validation logic (82% coverage)
- Clean architecture
- Well-tested core functionality

**Weaknesses:**
- Output formatting untested
- CLI untested
- Web app JS untested
- 2 test failures need fixing

**Overall Grade**: B+ (Good, with room for improvement in test coverage)

**Production Readiness**:
- ✓ Core library: Production-ready
- ✓ Web app: Production-ready (deployed and working)
- ⚠ CLI: Functional but untested
- ⚠ Output formats: Functional but untested

**Next Steps**: Fix 2 test failures, add output/CLI tests to reach 90%+ coverage
