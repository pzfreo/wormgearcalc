"""
Tests for wormcalc.output

Test JSON, Markdown, and text output formatting.
"""

import pytest
import json

from wormcalc.core import (
    design_from_module, design_from_envelope,
    WormProfile, WormType, Hand
)
from wormcalc.validation import validate_design
from wormcalc.output import to_json, to_markdown, to_summary


class TestToJson:
    """Tests for JSON output"""

    def test_json_valid_schema(self):
        """JSON output should be valid and parseable"""
        design = design_from_module(module=2.0, ratio=30)
        result = validate_design(design)
        json_str = to_json(design, result)

        # Should parse without error
        data = json.loads(json_str)

        # Check top-level structure
        assert 'worm' in data
        assert 'wheel' in data
        assert 'assembly' in data
        assert 'validation' in data
        assert data['assembly']['ratio'] == 30

    def test_json_worm_fields(self):
        """JSON should include all worm parameters"""
        design = design_from_module(module=2.0, ratio=30)
        result = validate_design(design)
        data = json.loads(to_json(design, result))

        worm = data['worm']
        assert 'module_mm' in worm
        assert 'pitch_diameter_mm' in worm
        assert 'tip_diameter_mm' in worm
        assert 'root_diameter_mm' in worm
        assert 'lead_mm' in worm
        assert 'lead_angle_deg' in worm
        assert 'num_starts' in worm

    def test_json_wheel_fields(self):
        """JSON should include all wheel parameters"""
        design = design_from_module(module=2.0, ratio=30)
        result = validate_design(design)
        data = json.loads(to_json(design, result))

        wheel = data['wheel']
        assert 'module_mm' in wheel
        assert 'num_teeth' in wheel
        assert 'pitch_diameter_mm' in wheel
        assert 'tip_diameter_mm' in wheel
        assert 'root_diameter_mm' in wheel
        assert 'helix_angle_deg' in wheel

    def test_json_validation_fields(self):
        """JSON should include validation results"""
        design = design_from_module(module=2.0, ratio=30)
        result = validate_design(design)
        data = json.loads(to_json(design, result))

        validation = data['validation']
        assert 'valid' in validation
        assert 'messages' in validation
        assert isinstance(validation['valid'], bool)
        assert isinstance(validation['messages'], list)

    def test_json_globoid_fields(self):
        """JSON should include globoid-specific fields when applicable"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_type=WormType.GLOBOID,
            throat_reduction=0.05
        )
        result = validate_design(design)
        data = json.loads(to_json(design, result))

        worm = data['worm']
        assert 'throat_reduction_mm' in worm
        assert 'throat_pitch_radius_mm' in worm
        assert 'throat_tip_radius_mm' in worm
        assert 'throat_root_radius_mm' in worm

    def test_json_no_throat_fields_for_cylindrical(self):
        """JSON should not include throat fields for cylindrical worms"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_type=WormType.CYLINDRICAL
        )
        result = validate_design(design)
        data = json.loads(to_json(design, result))

        worm = data['worm']
        assert 'throat_pitch_radius_mm' not in worm

    def test_json_manufacturing_fields(self):
        """JSON should include manufacturing parameters"""
        design = design_from_module(module=2.0, ratio=30)
        result = validate_design(design)
        data = json.loads(to_json(design, result))

        manufacturing = data['manufacturing']
        assert 'profile' in manufacturing
        assert 'worm_type' in manufacturing
        assert 'worm_length' in manufacturing
        assert 'wheel_width' in manufacturing
        assert 'wheel_throated' in manufacturing

    def test_json_with_profile_shift(self):
        """JSON should include profile shift when non-zero"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            profile_shift=0.3
        )
        result = validate_design(design)
        data = json.loads(to_json(design, result))

        assert 'profile_shift' in data['wheel']
        assert data['wheel']['profile_shift'] == 0.3

    def test_json_with_backlash(self):
        """JSON should include backlash when non-zero"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            backlash=0.1
        )
        result = validate_design(design)
        data = json.loads(to_json(design, result))

        assert 'backlash_mm' in data['assembly']
        assert data['assembly']['backlash_mm'] == 0.1


class TestToMarkdown:
    """Tests for Markdown output"""

    def test_markdown_structure(self):
        """Markdown should have expected structure"""
        design = design_from_module(module=2.0, ratio=30)
        result = validate_design(design)
        md = to_markdown(design, result)

        assert '# Worm Gear Design' in md
        assert '## Worm' in md
        assert '## Wheel' in md
        assert '## Manufacturing' in md

    def test_markdown_includes_key_values(self):
        """Markdown should include key design values"""
        design = design_from_module(module=2.0, ratio=30)
        result = validate_design(design)
        md = to_markdown(design, result)

        assert '2.0' in md  # Module value
        assert '30:1' in md or 'Ratio: 30' in md  # Ratio
        assert '20.0' in md or '20°' in md  # Pressure angle

    def test_markdown_validation_section(self):
        """Markdown should include validation results"""
        design = design_from_module(module=0.2, ratio=30)  # Too small - will error
        result = validate_design(design)
        md = to_markdown(design, result)

        assert '## Validation' in md
        assert '### Errors' in md or 'ERROR' in md

    def test_markdown_globoid_section(self):
        """Markdown should include globoid info when applicable"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_type=WormType.GLOBOID,
            throat_reduction=0.05
        )
        result = validate_design(design)
        md = to_markdown(design, result)

        assert 'globoid' in md.lower() or 'throat' in md.lower()

    def test_markdown_zk_profile(self):
        """Markdown should mention ZK profile"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            profile=WormProfile.ZK
        )
        result = validate_design(design)
        md = to_markdown(design, result)

        assert 'ZK' in md

    def test_markdown_left_hand(self):
        """Markdown should indicate left-hand thread"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            hand=Hand.LEFT
        )
        result = validate_design(design)
        md = to_markdown(design, result)

        assert 'left' in md.lower() or 'LEFT' in md


class TestToSummary:
    """Tests for text summary output"""

    def test_summary_contains_design_info(self):
        """Summary should include key design information"""
        design = design_from_module(module=2.0, ratio=30)
        summary = to_summary(design)

        assert 'Worm Gear Design' in summary
        assert 'Ratio' in summary
        assert 'Module' in summary

    def test_summary_contains_worm_info(self):
        """Summary should include worm parameters"""
        design = design_from_module(module=2.0, ratio=30)
        summary = to_summary(design)

        assert 'Worm:' in summary
        assert 'Tip diameter' in summary or 'OD' in summary
        assert 'Lead angle' in summary

    def test_summary_contains_wheel_info(self):
        """Summary should include wheel parameters"""
        design = design_from_module(module=2.0, ratio=30)
        summary = to_summary(design)

        assert 'Wheel:' in summary
        assert 'Teeth' in summary

    def test_summary_self_locking_yes(self):
        """Summary should indicate self-locking when applicable"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            target_lead_angle=4.0  # Low angle = self-locking
        )
        summary = to_summary(design)

        assert 'Self-locking: Yes' in summary

    def test_summary_self_locking_no(self):
        """Summary should indicate not self-locking when applicable"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            target_lead_angle=15.0  # High angle = not self-locking
        )
        summary = to_summary(design)

        assert 'Self-locking: No' in summary

    def test_summary_globoid(self):
        """Summary should indicate globoid worm type"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            worm_type=WormType.GLOBOID,
            throat_reduction=0.05
        )
        summary = to_summary(design)

        assert 'globoid' in summary.lower()

    def test_summary_multi_start(self):
        """Summary should indicate multi-start worm"""
        design = design_from_module(
            module=2.0,
            ratio=30,
            num_starts=2
        )
        summary = to_summary(design)

        # Check for starts indication (format may vary)
        assert '2' in summary and ('start' in summary.lower() or 'Starts' in summary)


class TestOutputEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_json_very_small_module(self):
        """JSON should handle very small modules"""
        design = design_from_module(module=0.3, ratio=30)
        result = validate_design(design)
        json_str = to_json(design, result)

        data = json.loads(json_str)
        assert data['worm']['module_mm'] == 0.3

    def test_json_large_ratio(self):
        """JSON should handle large ratios"""
        design = design_from_module(module=2.0, ratio=100)
        result = validate_design(design)
        json_str = to_json(design, result)

        data = json.loads(json_str)
        assert data['assembly']['ratio'] == 100
        assert data['wheel']['num_teeth'] == 100

    def test_markdown_no_validation(self):
        """Markdown should work without validation result"""
        design = design_from_module(module=2.0, ratio=30)
        # Don't validate - pass None
        md = to_markdown(design, None)

        assert '# Worm Gear Design' in md
        assert 'Validation' not in md or 'Not validated' in md

    def test_summary_envelope_design(self):
        """Summary should work for envelope-based design"""
        design = design_from_envelope(
            worm_od=20.0,
            wheel_od=65.0,
            ratio=30
        )
        summary = to_summary(design)

        assert 'Worm Gear Design' in summary
        assert 'Ratio: 30:1' in summary


class TestOutputConsistency:
    """Tests that outputs remain consistent for same input"""

    def test_json_deterministic(self):
        """JSON output should be deterministic"""
        design = design_from_module(module=2.0, ratio=30)
        result = validate_design(design)

        json1 = to_json(design, result)
        json2 = to_json(design, result)

        assert json1 == json2

    def test_markdown_deterministic(self):
        """Markdown output should be deterministic"""
        design = design_from_module(module=2.0, ratio=30)
        result = validate_design(design)

        md1 = to_markdown(design, result)
        md2 = to_markdown(design, result)

        assert md1 == md2

    def test_summary_deterministic(self):
        """Summary output should be deterministic"""
        design = design_from_module(module=2.0, ratio=30)

        summary1 = to_summary(design)
        summary2 = to_summary(design)

        assert summary1 == summary2
